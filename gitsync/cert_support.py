"""Certificate support for Windows - automatic detection and export"""

import os
import platform
import tempfile
import ssl
import logging
from typing import Optional, List, Tuple
import atexit

logger = logging.getLogger(__name__)

# Track temporary files for cleanup
_temp_cert_files = []

def cleanup_temp_certs():
    """Clean up temporary certificate files on exit."""
    for cert_file in _temp_cert_files:
        try:
            if os.path.exists(cert_file):
                os.unlink(cert_file)
                logger.debug(f"Cleaned up temporary cert file: {cert_file}")
        except Exception as e:
            logger.warning(f"Failed to clean up {cert_file}: {e}")

# Register cleanup function
atexit.register(cleanup_temp_certs)


class WindowsCertificateDetector:
    """Detect and export certificates from Windows certificate store."""
    
    def __init__(self):
        self.is_windows = platform.system() == "Windows"
        self._temp_bundle = None
        
    def is_available(self) -> bool:
        """Check if Windows certificate detection is available."""
        if not self.is_windows:
            return False
            
        try:
            # Test if ssl.enum_certificates is available
            ssl.enum_certificates("ROOT")
            return True
        except Exception:
            return False
    
    def get_windows_certificates(self, store_names: List[str] = None) -> List[Tuple[bytes, str, any]]:
        """Get certificates from Windows certificate stores.
        
        Args:
            store_names: List of store names to check. Defaults to ['ROOT', 'CA']
            
        Returns:
            List of (cert_bytes, encoding_type, trust) tuples
        """
        if not self.is_available():
            return []
            
        if store_names is None:
            store_names = ['ROOT', 'CA']  # Default to trusted root and intermediate CAs
            
        all_certs = []
        
        for store_name in store_names:
            try:
                certs = ssl.enum_certificates(store_name)
                logger.info(f"Found {len(certs)} certificates in {store_name} store")
                all_certs.extend(certs)
            except Exception as e:
                logger.warning(f"Failed to access {store_name} certificate store: {e}")
                
        return all_certs
    
    def export_certificates_to_pem(self, include_certifi: bool = True) -> Optional[str]:
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
            temp_bundle = tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.pem',
                delete=False,
                encoding='utf-8'
            )
            
            # Track for cleanup
            _temp_cert_files.append(temp_bundle.name)
            
            cert_count = 0
            
            # Start with certifi's bundle if requested
            if include_certifi:
                try:
                    import certifi
                    with open(certifi.where(), 'r', encoding='utf-8') as f:
                        temp_bundle.write(f.read())
                        temp_bundle.write('\n')
                    logger.info("Added certifi's default certificate bundle")
                except ImportError:
                    logger.warning("certifi not available, using only Windows certificates")
                except Exception as e:
                    logger.warning(f"Failed to include certifi bundle: {e}")
            
            # Get Windows certificates
            windows_certs = self.get_windows_certificates()
            
            # Export each certificate
            for cert_bytes, encoding_type, trust in windows_certs:
                # Only process X.509 ASN.1 encoded certificates
                if encoding_type == 'x509_asn':
                    try:
                        # Convert DER to PEM format
                        pem_cert = ssl.DER_cert_to_PEM_cert(cert_bytes)
                        temp_bundle.write(pem_cert)
                        temp_bundle.write('\n')
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
    
    def get_cert_bundle_path(self) -> Optional[str]:
        """Get path to certificate bundle, creating it if necessary.
        
        Returns:
            Path to certificate bundle file, or None if not available
        """
        if self._temp_bundle and os.path.exists(self._temp_bundle):
            return self._temp_bundle
            
        # Create new bundle
        return self.export_certificates_to_pem()


def get_system_cert_bundle() -> Optional[str]:
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


def get_combined_cert_bundle() -> Optional[str]:
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
def export_with_wincertstore() -> Optional[str]:
    """Export certificates using wincertstore package (fallback method).
    
    Returns:
        Path to certificate bundle file, or None if failed
    """
    try:
        import wincertstore
        import certifi
        
        temp_bundle = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.pem',
            delete=False,
            encoding='utf-8'
        )
        
        # Track for cleanup
        _temp_cert_files.append(temp_bundle.name)
        
        # Start with certifi's bundle
        with open(certifi.where(), 'r', encoding='utf-8') as f:
            temp_bundle.write(f.read())
            temp_bundle.write('\n')
        
        # Add Windows certificates
        cert_count = 0
        for store_name in ['ROOT', 'CA']:
            with wincertstore.CertSystemStore(store_name) as store:
                for cert in store.itercerts(usage=wincertstore.SERVER_AUTH):
                    pem = cert.get_pem()
                    temp_bundle.write(pem.decode('ascii'))
                    temp_bundle.write('\n')
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