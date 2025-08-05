"""PAC (Proxy Auto-Configuration) support for Windows/Chrome"""

import os
import platform
import logging
from typing import Optional, Dict, Any, Tuple
from urllib.parse import urlparse, unquote

logger = logging.getLogger(__name__)

# Try to import Windows-specific modules
try:
    import winreg
    WINDOWS_AVAILABLE = True
except ImportError:
    WINDOWS_AVAILABLE = False

# Try to import pypac
try:
    import pypac
    from pypac import PACSession
    PYPAC_AVAILABLE = True
except ImportError:
    PYPAC_AVAILABLE = False
    logger.warning("pypac not installed. PAC support will be limited.")


class PACProxyDetector:
    """Detect and use PAC scripts from Chrome/Windows configuration."""
    
    def __init__(self):
        self.pac_url = None
        self.pac_content = None
        self.pac_object = None
        
    def is_available(self) -> bool:
        """Check if PAC detection is available on this system."""
        return platform.system() == "Windows" and (WINDOWS_AVAILABLE or PYPAC_AVAILABLE)
    
    def get_pac_url_from_registry(self) -> Optional[str]:
        """Extract PAC URL from Windows Registry."""
        if not WINDOWS_AVAILABLE:
            return None
            
        try:
            # Chrome uses the same proxy settings as IE from Windows Internet Options
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                try:
                    pac_url, _ = winreg.QueryValueEx(key, "AutoConfigURL")
                    logger.info(f"Found PAC URL in registry: {pac_url}")
                    return pac_url
                except FileNotFoundError:
                    logger.debug("No AutoConfigURL in registry")
                except Exception as e:
                    logger.error(f"Error reading AutoConfigURL: {e}")
        except Exception as e:
            logger.error(f"Error accessing registry: {e}")
        
        return None
    
    def get_all_proxy_settings(self) -> Dict[str, Any]:
        """Get all proxy-related settings from Windows Registry."""
        if not WINDOWS_AVAILABLE:
            return {}
            
        proxy_settings = {}
        
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                # Get number of values
                _, value_count, _ = winreg.QueryInfoKey(key)
                
                # Iterate through all values
                for i in range(value_count):
                    try:
                        name, value, _ = winreg.EnumValue(key, i)
                        if name in ['ProxyEnable', 'ProxyServer', 'AutoConfigURL', 
                                   'ProxyOverride', 'AutoDetect']:
                            proxy_settings[name] = value
                    except Exception:
                        continue
                        
        except Exception as e:
            logger.error(f"Error reading registry: {e}")
        
        return proxy_settings
    
    def download_pac_content(self, pac_url: str) -> Optional[str]:
        """Download PAC script content from URL."""
        try:
            if pac_url.startswith('file://'):
                # Handle local files
                # Windows file URLs can be file:///C:/path or file://server/share
                if pac_url.startswith('file:///'):
                    # Local file
                    local_path = unquote(pac_url[8:])  # Remove file:///
                else:
                    # UNC path
                    local_path = unquote(pac_url[5:])  # Remove file:
                    
                # Convert forward slashes to backslashes on Windows
                if platform.system() == "Windows":
                    local_path = local_path.replace('/', '\\')
                    
                with open(local_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    logger.info(f"Successfully read PAC file from: {local_path}")
                    return content
            else:
                # Download from HTTP/HTTPS
                import requests
                response = requests.get(pac_url, timeout=30)
                response.raise_for_status()
                logger.info(f"Successfully downloaded PAC from: {pac_url}")
                return response.text
        except Exception as e:
            logger.error(f"Error downloading PAC from {pac_url}: {e}")
        
        return None
    
    def detect_pac_using_pypac(self) -> Optional[Any]:
        """Use pypac to automatically discover PAC configuration."""
        if not PYPAC_AVAILABLE:
            return None
            
        try:
            # PyPAC will automatically check Windows settings
            pac = pypac.get_pac()
            if pac:
                self.pac_object = pac
                if hasattr(pac, 'url'):
                    self.pac_url = pac.url
                logger.info("Successfully detected PAC using pypac")
                return pac
        except Exception as e:
            logger.error(f"Error using pypac: {e}")
        
        return None
    
    def extract_proxy_from_pac(self, target_url: str) -> Optional[str]:
        """Extract proxy for a specific URL from PAC script."""
        if not PYPAC_AVAILABLE or not self.pac_object:
            return None
            
        try:
            # Parse the target URL
            parsed = urlparse(target_url)
            host = parsed.hostname or parsed.netloc
            
            # Get proxy from PAC
            proxy_string = self.pac_object.find_proxy_for_url(target_url, host)
            
            if proxy_string and proxy_string != "DIRECT":
                # PAC can return multiple proxies separated by semicolons
                # Format: "PROXY proxy1:port; PROXY proxy2:port; DIRECT"
                proxies = proxy_string.split(';')
                for proxy in proxies:
                    proxy = proxy.strip()
                    if proxy.startswith("PROXY "):
                        proxy_addr = proxy[6:].strip()
                        # Return as http://proxy:port format
                        if not proxy_addr.startswith("http"):
                            proxy_addr = f"http://{proxy_addr}"
                        logger.info(f"PAC returned proxy for {host}: {proxy_addr}")
                        return proxy_addr
                    elif proxy.startswith("SOCKS "):
                        proxy_addr = proxy[6:].strip()
                        # Return as socks://proxy:port format
                        if not proxy_addr.startswith("socks"):
                            proxy_addr = f"socks://{proxy_addr}"
                        logger.info(f"PAC returned SOCKS proxy for {host}: {proxy_addr}")
                        return proxy_addr
                        
        except Exception as e:
            logger.error(f"Error extracting proxy from PAC: {e}")
        
        return None
    
    def get_proxy_for_url(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """Get HTTP and HTTPS proxy for a specific URL.
        
        Returns:
            Tuple of (http_proxy, https_proxy)
        """
        # Try to detect PAC
        pac_url = self.get_pac_url_from_registry()
        
        if not pac_url and PYPAC_AVAILABLE:
            # Try pypac auto-detection
            self.detect_pac_using_pypac()
            pac_url = self.pac_url
        
        if pac_url and not self.pac_content:
            # Download PAC content
            self.pac_content = self.download_pac_content(pac_url)
        
        if self.pac_content and PYPAC_AVAILABLE and not self.pac_object:
            # Create PAC object from content
            try:
                from pypac.parser import PACFile
                self.pac_object = PACFile(self.pac_content)
            except Exception as e:
                logger.error(f"Error parsing PAC content: {e}")
        
        # Extract proxy for the URL
        proxy = None
        if self.pac_object:
            proxy = self.extract_proxy_from_pac(url)
        
        # If no PAC or PAC returned DIRECT, check manual proxy settings
        if not proxy:
            settings = self.get_all_proxy_settings()
            if settings.get('ProxyEnable') and settings.get('ProxyServer'):
                proxy_server = settings['ProxyServer']
                # ProxyServer can be "server:port" or "http=server:port;https=server:port"
                if '=' in proxy_server:
                    # Parse different proxies for different protocols
                    proxy_dict = {}
                    for entry in proxy_server.split(';'):
                        if '=' in entry:
                            protocol, server = entry.split('=', 1)
                            proxy_dict[protocol.strip().lower()] = server.strip()
                    
                    http_proxy = proxy_dict.get('http')
                    https_proxy = proxy_dict.get('https', http_proxy)
                    
                    if http_proxy and not http_proxy.startswith('http'):
                        http_proxy = f"http://{http_proxy}"
                    if https_proxy and not https_proxy.startswith('http'):
                        https_proxy = f"http://{https_proxy}"
                        
                    return (http_proxy, https_proxy)
                else:
                    # Single proxy for all protocols
                    if not proxy_server.startswith('http'):
                        proxy_server = f"http://{proxy_server}"
                    return (proxy_server, proxy_server)
        
        # Return the PAC-detected proxy for both HTTP and HTTPS
        return (proxy, proxy)
    
    def create_pac_session(self) -> Optional[Any]:
        """Create a requests Session that uses PAC for proxy resolution."""
        if not PYPAC_AVAILABLE:
            logger.warning("pypac not available, cannot create PAC session")
            return None
            
        try:
            # Try to get PAC from Windows settings
            pac_url = self.get_pac_url_from_registry()
            
            if pac_url:
                # Download PAC content if not already done
                if not self.pac_content:
                    self.pac_content = self.download_pac_content(pac_url)
                
                if self.pac_content:
                    # Create PAC session with the content
                    from pypac import PACSession
                    session = PACSession(pac=self.pac_content)
                    logger.info("Created PAC session successfully")
                    return session
            
            # Try auto-detection
            from pypac import PACSession
            session = PACSession()
            logger.info("Created PAC session with auto-detection")
            return session
            
        except Exception as e:
            logger.error(f"Error creating PAC session: {e}")
        
        return None


def detect_and_configure_proxy() -> Dict[str, Optional[str]]:
    """Detect and return proxy configuration from Windows/Chrome.
    
    Returns:
        Dictionary with 'http' and 'https' proxy URLs
    """
    detector = PACProxyDetector()
    
    if not detector.is_available():
        logger.info("PAC detection not available on this system")
        return {'http': None, 'https': None}
    
    # Get all proxy settings for logging
    all_settings = detector.get_all_proxy_settings()
    if all_settings:
        logger.info("Windows proxy settings found:")
        for key, value in all_settings.items():
            logger.info(f"  {key}: {value}")
    
    # Get proxy for GitHub
    http_proxy, https_proxy = detector.get_proxy_for_url("https://api.github.com")
    
    return {
        'http': http_proxy,
        'https': https_proxy
    }