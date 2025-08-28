# PyPI Publishing Guide

## Overview
GitBridge v1.0.0 uses `uv_build` backend with automated GitHub Actions for PyPI publishing. The project distributes a universal wheel with platform-specific dependencies handled via markers.

## Setup Instructions

### 1. Configure PyPI Trusted Publishing

Go to https://pypi.org/manage/account/publishing/ and add this repository:

- **PyPI Project Name**: `gitbridge`
- **Owner**: `nevedomski`
- **Repository name**: `gitbridge`
- **Workflow name**: `publish.yml`
- **Environment name**: `pypi`

### 2. Configure TestPyPI (For Testing)

For testing releases, configure on https://test.pypi.org/manage/account/publishing/:

- **PyPI Project Name**: `gitbridge`
- **Owner**: `nevedomski`
- **Repository name**: `gitbridge`
- **Workflow name**: `ci.yml` (auto-publishes from main)
- **Environment name**: `testpypi`

### 3. GitHub Repository Settings

Configure environments in your repository (Settings → Environments):

- **pypi**: Production PyPI releases
- **testpypi**: Test PyPI releases (auto-deployed from main)

## Publishing Process

### Production Release to PyPI

#### Option 1: GitHub Release (Recommended)
1. Update version in `pyproject.toml` to `1.0.0`
2. Commit and push changes
3. Create a GitHub Release:
   ```bash
   git tag -a v1.0.0 -m "Release v1.0.0"
   git push origin v1.0.0
   gh release create v1.0.0 --title "v1.0.0" --notes "First stable release"
   ```
4. The workflow automatically:
   - Builds the universal wheel
   - Publishes to PyPI
   - Uploads artifacts to GitHub Release

#### Option 2: Manual Workflow Dispatch
1. Go to Actions → "Publish to PyPI" workflow
2. Click "Run workflow"
3. Select `pypi` from the dropdown
4. Run the workflow

### Automatic TestPyPI Publishing

Every push to `main` automatically:
- Builds the wheel
- Tests installation across platforms
- Publishes to TestPyPI (if tests pass)

Install from TestPyPI:
```bash
pip install -i https://test.pypi.org/simple/ gitbridge
```

## Package Distribution

### Universal Wheel Strategy
GitBridge uses a **single universal wheel** (`gitbridge-1.0.0-py3-none-any.whl`) that works on all platforms:

- **Windows**: Automatically installs pypac, wincertstore, pywin32
- **Linux/macOS**: Installs only cross-platform dependencies
- **Platform detection**: Via `sys_platform == 'win32'` markers in `pyproject.toml`

### Testing Locally

```bash
# Build the universal wheel
uv build

# Check build artifacts
ls -la dist/
# Should show:
#   gitbridge-1.0.0-py3-none-any.whl
#   gitbridge-1.0.0.tar.gz

# Test installation
pip install dist/gitbridge-1.0.0-py3-none-any.whl

# Test with extras
pip install "dist/gitbridge-1.0.0-py3-none-any.whl[browser]"
```

## CI/CD Workflow Features

### Continuous Integration (`ci.yml`)
- **Wheel testing**: Every push/PR tests across Windows, Linux, macOS
- **Python versions**: Tests on Python 3.10, 3.11, 3.12
- **Auto-publish**: Main branch commits go to TestPyPI
- **Platform verification**: Ensures Windows deps only install on Windows

### Publishing Workflow (`publish.yml`)
- **Trusted Publishing**: No API tokens needed (uses OIDC)
- **Dual triggers**: GitHub releases or manual dispatch
- **Environment protection**: Separate pypi/testpypi environments
- **Asset upload**: Automatically attaches wheel to GitHub releases