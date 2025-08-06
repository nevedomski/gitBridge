# Testing Architecture for gitBridge

This document explains how to use the cross-platform testing architecture for the gitBridge project.

## Overview

The gitBridge project includes platform-specific functionality for Windows (PAC proxy support, Windows certificate store access) that needs to work reliably across all platforms during testing. Our testing architecture uses comprehensive mocking and platform detection to ensure:

- Tests pass on all platforms (Windows, Linux, macOS)
- Windows-specific functionality is thoroughly tested via mocking on all platforms
- Platform-specific tests can be selectively run or skipped
- CI/CD pipelines work correctly across different operating systems

## Platform-Specific Markers

We use pytest markers to categorize tests by platform requirements:

- `@pytest.mark.windows` - Tests that require Windows-specific functionality
- `@pytest.mark.linux` - Tests that require Linux-specific functionality  
- `@pytest.mark.macos` - Tests that require macOS-specific functionality
- `@pytest.mark.platform_specific` - Tests that handle platform-specific logic

## Running Tests

### Run All Tests
```bash
uv run pytest
```

### Run Only Windows-Specific Tests
```bash
uv run pytest -m "windows"
```

### Skip Windows-Specific Tests (useful on Linux/macOS)
```bash
uv run pytest -m "not windows"
```

### Run Platform-Specific Tests
```bash
uv run pytest -m "platform_specific"
```

## Platform Detection Utilities

The `tests/platform_utils.py` module provides utilities for platform detection and test management:

### Platform Detection Functions
```python
from tests.platform_utils import is_windows, is_linux, is_macos

if is_windows():
    # Windows-specific test logic
    pass
```

### Test Skip Decorators
```python
from tests.platform_utils import skip_on_non_windows, skip_on_windows

@skip_on_non_windows("Requires Windows registry access")
def test_windows_registry():
    # This test only runs on Windows
    pass

@skip_on_windows("POSIX-specific functionality")  
def test_posix_functionality():
    # This test skips on Windows
    pass
```

### Mock Utilities for Windows Modules
```python
from tests.platform_utils import mock_windows_modules, WindowsModuleMocker

# Mock all Windows modules at once
with patch.dict("sys.modules", mock_windows_modules()):
    # Test code that imports Windows-specific modules
    pass

# Or create individual mocks
winreg_mock = WindowsModuleMocker.create_winreg_mock()
pypac_mock = WindowsModuleMocker.create_pypac_mock()
```

## Test Fixtures

The `conftest.py` file provides several platform-specific fixtures:

- `windows_mock_modules` - Complete set of Windows module mocks
- `mock_winreg` - Mock Windows registry module
- `mock_pypac` - Mock PAC proxy detection module
- `mock_wincertstore` - Mock Windows certificate store module
- `mock_ssl` - Mock SSL module with Windows-specific functionality
- `platform_windows/linux/macos` - Mock platform detection
- `windows_test_environment` - Complete Windows test environment setup

### Example Usage
```python
def test_pac_detection(windows_mock_modules):
    """Test PAC detection with mocked Windows modules."""
    with patch.dict("sys.modules", windows_mock_modules):
        from gitbridge.pac_support import PACProxyDetector
        detector = PACProxyDetector()
        # Test logic here
```

## Writing Platform-Specific Tests

### Windows-Only Test
```python
import pytest
from tests.platform_utils import skip_on_non_windows

@pytest.mark.windows
@skip_on_non_windows("Requires Windows certificate store")
def test_windows_certificates():
    """Test Windows certificate store access."""
    # This test runs only on Windows
    from gitbridge.cert_support import WindowsCertificateDetector
    detector = WindowsCertificateDetector()
    assert detector.is_available()
```

### Cross-Platform Test with Platform-Specific Behavior
```python
import pytest
from unittest.mock import patch
from tests.platform_utils import is_windows

@pytest.mark.platform_specific
def test_cross_platform_behavior(windows_mock_modules):
    """Test that behaves differently on different platforms."""
    if is_windows():
        # Test native Windows behavior
        pass
    else:
        # Test with mocked Windows modules
        with patch.dict("sys.modules", windows_mock_modules):
            # Test logic with mocks
            pass
```

## CI/CD Integration

The GitHub Actions workflow automatically:

1. **Runs tests on multiple platforms** (Ubuntu, Windows, macOS)
2. **Conditionally executes platform-specific tests**:
   - On Windows: Runs all tests including Windows-specific ones
   - On Linux/macOS: Skips Windows-specific tests with `-m "not windows"`
3. **Uses consistent tooling** (uv) across all platforms
4. **Provides coverage reports** for each platform

## Module Structure

```
tests/
├── conftest.py                 # Global fixtures and configuration
├── platform_utils.py          # Platform detection and mocking utilities
├── test_platform_integration.py # Cross-platform integration tests
├── test_pac_support.py         # PAC proxy tests (Windows-specific)
├── test_cert_support.py        # Certificate support tests (Windows-specific)
└── README.md                   # This file
```

## Key Benefits

1. **Reliability**: Tests pass consistently on all platforms
2. **Comprehensive Coverage**: Windows functionality tested even on non-Windows systems
3. **Selective Execution**: Run only relevant tests for each platform
4. **CI/CD Compatibility**: Automated testing across multiple platforms
5. **Developer Friendly**: Easy to write and maintain platform-specific tests

## Troubleshooting

### Test Fails on Non-Windows Platform
Make sure the test is properly marked and uses appropriate mocks:
```python
@pytest.mark.windows
def test_windows_feature(windows_mock_modules):
    with patch.dict("sys.modules", windows_mock_modules):
        # Test code here
```

### Import Error for Windows Module
Use the platform detection and mocking:
```python
from tests.platform_utils import mock_windows_modules

with patch.dict("sys.modules", mock_windows_modules()):
    # Now Windows modules can be imported safely
    import winreg  # This works even on Linux/macOS
```

### Test Should Skip on Certain Platform
Use the skip decorators:
```python
from tests.platform_utils import skip_on_windows

@skip_on_windows("Not supported on Windows")
def test_unix_feature():
    # This test is skipped on Windows
    pass
```