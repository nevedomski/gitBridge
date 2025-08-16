"""Certificate support for Windows - automatic detection and export"""

import atexit
import contextlib
import logging
import os
import platform
import ssl
import tempfile
import threading
from typing import Any

from .interfaces import CertificateProvider

logger = logging.getLogger(__name__)

# Thread-safe certificate management
# DOCDEV-NOTE: Thread lock prevents race conditions in certificate operations
_cert_lock = threading.Lock()
_temp_cert_files: list[str] = []


def cleanup_temp_certs() -> None:
    """Clean up temporary certificate files on exit (thread-safe)."""
    with _cert_lock:
        # Create a copy to avoid modification during iteration
        files_to_clean = _temp_cert_files.copy()

    for cert_file in files_to_clean:
        try:
            if os.path.exists(cert_file):
                os.unlink(cert_file)
                logger.debug(f"Cleaned up temporary cert file: {cert_file}")
                with _cert_lock:
                    if cert_file in _temp_cert_files:
                        _temp_cert_files.remove(cert_file)
        except Exception as e:
            logger.warning(f"Failed to clean up {cert_file}: {e}")


# Register cleanup function
atexit.register(cleanup_temp_certs)


class CertificateManager:
    """Thread-safe certificate manager with automatic cleanup.

    Provides context manager support for guaranteed cleanup of temporary
    certificate files, even in the presence of exceptions or thread interruptions.

    DOCDEV-NOTE: Use this for all certificate operations to ensure thread safety
    """

    def __init__(self) -> None:
        """Initialize certificate manager with thread-local storage."""
        self._local = threading.local()
        self._exit_stack = contextlib.ExitStack()
        self._managed_certs: list[str] = []

    def add_temp_cert(self, cert_path: str) -> None:
        """Add a temporary certificate file for tracking and cleanup.

        Args:
            cert_path: Path to temporary certificate file
        """
        with _cert_lock:
            _temp_cert_files.append(cert_path)
            self._managed_certs.append(cert_path)

        # Register cleanup callback
        self._exit_stack.callback(self._cleanup_cert, cert_path)

    def _cleanup_cert(self, cert_path: str) -> None:
        """Clean up a single certificate file (thread-safe).

        Args:
            cert_path: Path to certificate file to clean up
        """
        with _cert_lock:
            try:
                if cert_path in _temp_cert_files:
                    _temp_cert_files.remove(cert_path)
                if cert_path in self._managed_certs:
                    self._managed_certs.remove(cert_path)

                if os.path.exists(cert_path):
                    os.unlink(cert_path)
                    logger.debug(f"Cleaned up managed cert file: {cert_path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup {cert_path}: {e}")

    def __enter__(self) -> "CertificateManager":
        """Enter context manager."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Exit context manager and clean up all managed certificates."""
        self._exit_stack.__exit__(*args)


class WindowsCertificateDetector(CertificateProvider):
    """Detect and export certificates from Windows certificate store."""

    def __init__(self) -> None:
        self.is_windows = platform.system() == "Windows"
        self._temp_bundle: str | None = None

    def is_available(self) -> bool:
        """Check if Windows certificate detection is available."""
        if not self.is_windows:
            return False

        try:
            # Test if ssl.enum_certificates is available
            ssl.enum_certificates("ROOT")  # type: ignore[attr-defined]
            return True
        except Exception:
            return False

    def get_windows_certificates(self, store_names: list[str] | None = None) -> list[tuple[bytes, str, Any]]:
        """Get certificates from Windows certificate stores.

        Args:
            store_names: List of store names to check. Defaults to ['ROOT', 'CA']

        Returns:
            List of (cert_bytes, encoding_type, trust) tuples
        """
        if not self.is_available():
            return []

        if store_names is None:
            store_names = ["ROOT", "CA"]  # Default to trusted root and intermediate CAs

        all_certs = []

        for store_name in store_names:
            try:
                certs = ssl.enum_certificates(store_name)  # type: ignore[attr-defined]
                logger.info(f"Found {len(certs)} certificates in {store_name} store")
                all_certs.extend(certs)
            except Exception as e:
                logger.warning(f"Failed to access {store_name} certificate store: {e}")

        return all_certs

    def export_certificates_to_pem(self, include_certifi: bool = True) -> str | None:
        """Export Windows certificates to a temporary PEM file.

        Args:
            include_certifi: Whether to include certifi's default bundle

        Returns:
            Path to temporary certificate bundle file, or None if failed
        """
        if not self.is_available():
            return None

        try:
            # Create temporary file
            temp_bundle = tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=False, encoding="utf-8")

            # Track for cleanup (thread-safe)
            with _cert_lock:
                _temp_cert_files.append(temp_bundle.name)

            cert_count = 0

            # Start with certifi's bundle if requested
            if include_certifi:
                try:
                    import certifi

                    with open(certifi.where(), encoding="utf-8") as f:
                        temp_bundle.write(f.read())
                        temp_bundle.write("\n")
                    logger.info("Added certifi's default certificate bundle")
                except ImportError:
                    logger.warning("certifi not available, using only Windows certificates")
                except Exception as e:
                    logger.warning(f"Failed to include certifi bundle: {e}")

            # Get Windows certificates
            windows_certs = self.get_windows_certificates()

            # Export each certificate
            for cert_bytes, encoding_type, _trust in windows_certs:
                # Only process X.509 ASN.1 encoded certificates
                if encoding_type == "x509_asn":
                    try:
                        # Convert DER to PEM format
                        pem_cert = ssl.DER_cert_to_PEM_cert(cert_bytes)
                        temp_bundle.write(pem_cert)
                        temp_bundle.write("\n")
                        cert_count += 1
                    except Exception as e:
                        logger.debug(f"Failed to convert certificate: {e}")

            temp_bundle.close()

            logger.info(f"Exported {cert_count} Windows certificates to {temp_bundle.name}")
            self._temp_bundle = temp_bundle.name

            return temp_bundle.name

        except Exception as e:
            logger.error(f"Failed to export certificates: {e}")
            return None

    def get_cert_bundle_path(self) -> str | None:
        """Get path to certificate bundle, creating it if necessary.

        Returns:
            Path to certificate bundle file, or None if not available
        """
        if self._temp_bundle and os.path.exists(self._temp_bundle):
            return self._temp_bundle

        # Create new bundle
        return self.export_certificates_to_pem()

    def get_certificates(self, store_names: list[str] | None = None) -> list[tuple[bytes, str, Any]]:
        """Retrieve SSL certificates from configured sources.

        This method implements the CertificateProvider interface by delegating
        to the existing get_windows_certificates method.

        Args:
            store_names: Optional list of certificate store names to query

        Returns:
            List[Tuple[bytes, str, Any]]: List of certificate tuples
        """
        return self.get_windows_certificates(store_names)

    def export_certificates(self, output_path: str | None = None, include_system: bool = True) -> str | None:
        """Export certificates to a PEM bundle file for HTTP clients.

        This method implements the CertificateProvider interface by delegating
        to the existing export_certificates_to_pem method.

        Args:
            output_path: Optional path for certificate bundle file (ignored - uses temp file)
            include_system: Whether to include system/default certificates

        Returns:
            Optional[str]: Path to created certificate bundle file
        """
        return self.export_certificates_to_pem(include_certifi=include_system)

    def validate_certificates(self, test_url: str = "https://api.github.com") -> bool:
        """Test certificate bundle functionality with a target URL.

        Verifies that the current certificate configuration can successfully
        validate SSL connections to the target URL.

        Args:
            test_url: URL to use for certificate testing

        Returns:
            bool: True if certificate configuration successfully validates SSL connections
        """
        try:
            cert_bundle = self.get_cert_bundle_path()
            if not cert_bundle:
                # If no custom bundle, assume system certs will work
                return True

            import requests

            # Test SSL validation with our certificate bundle
            response = requests.head(test_url, verify=cert_bundle, timeout=10, allow_redirects=True)

            # Consider 2xx, 3xx, and 405 (Method Not Allowed) as success
            return response.status_code < 500

        except requests.exceptions.SSLError as e:
            logger.error(f"SSL certificate validation failed: {e}")
            return False
        except Exception as e:
            logger.warning(f"Certificate validation test failed: {e}")
            # Don't fail completely for non-SSL errors
            return True


def get_system_cert_bundle() -> str | None:
    """Get system certificate bundle path.

    On Windows, this exports certificates from the Windows certificate store.
    On other systems, returns None (use default certifi bundle).

    Returns:
        Path to certificate bundle file, or None
    """
    detector = WindowsCertificateDetector()

    if detector.is_available():
        logger.info("Windows certificate store detected, exporting certificates...")
        return detector.export_certificates_to_pem()
    else:
        logger.debug("Windows certificate store not available")
        return None


def get_combined_cert_bundle() -> str | None:
    """Get a certificate bundle combining certifi and system certificates.

    Returns:
        Path to combined certificate bundle, or None to use defaults
    """
    if platform.system() != "Windows":
        # On non-Windows systems, use default behavior
        return None

    try:
        # Try to get Windows certificates
        detector = WindowsCertificateDetector()
        if detector.is_available():
            bundle_path = detector.export_certificates_to_pem(include_certifi=True)
            if bundle_path:
                logger.info(f"Using combined certificate bundle: {bundle_path}")
                return bundle_path
    except Exception as e:
        logger.warning(f"Failed to create combined certificate bundle: {e}")

    # Fall back to None (use default certifi)
    return None


# Fallback support for wincertstore if ssl.enum_certificates fails
def export_with_wincertstore() -> str | None:
    """Export certificates using wincertstore package (fallback method).

    Returns:
        Path to certificate bundle file, or None if failed
    """
    try:
        import certifi
        import wincertstore

        temp_bundle = tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=False, encoding="utf-8")

        # Track for cleanup
        _temp_cert_files.append(temp_bundle.name)

        # Start with certifi's bundle
        with open(certifi.where(), encoding="utf-8") as f:
            temp_bundle.write(f.read())
            temp_bundle.write("\n")

        # Add Windows certificates
        cert_count = 0
        for store_name in ["ROOT", "CA"]:
            with wincertstore.CertSystemStore(store_name) as store:
                for cert in store.itercerts(usage=wincertstore.SERVER_AUTH):
                    pem = cert.get_pem()
                    temp_bundle.write(pem.decode("ascii"))
                    temp_bundle.write("\n")
                    cert_count += 1

        temp_bundle.close()

        logger.info(f"Exported {cert_count} certificates using wincertstore to {temp_bundle.name}")
        return temp_bundle.name

    except ImportError:
        logger.debug("wincertstore not available")
        return None
    except Exception as e:
        logger.error(f"Failed to export with wincertstore: {e}")
        return None
