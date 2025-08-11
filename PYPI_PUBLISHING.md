# PyPI Publishing Setup

## Overview
The project now uses uv's native build backend (`uv_build`) and GitHub Actions for automated PyPI publishing.

## Setup Instructions

### 1. Configure PyPI Trusted Publishing

Go to https://pypi.org/manage/account/publishing/ and add this repository:

- **PyPI Project Name**: `gitbridge`
- **Owner**: `nevedomski`
- **Repository name**: `gitbridge`
- **Workflow name**: `publish.yml`
- **Environment name**: `pypi`

### 2. Configure TestPyPI (Optional)

For testing, also configure on https://test.pypi.org/manage/account/publishing/:

- **PyPI Project Name**: `gitbridge`
- **Owner**: `nevedomski`
- **Repository name**: `gitbridge`
- **Workflow name**: `publish.yml`
- **Environment name**: `testpypi`

## Publishing Process

### Automatic Release (Recommended)

1. Update version in `pyproject.toml`
2. Commit and push changes
3. Create and push a version tag:
   ```bash
   git tag v0.5.2
   git push origin v0.5.2
   ```
4. The workflow will automatically:
   - Build the package
   - Publish to PyPI
   - Create a GitHub Release with artifacts

### Manual TestPyPI Publishing

1. Go to Actions → "Publish to PyPI" workflow
2. Click "Run workflow"
3. Check "Publish to TestPyPI instead of PyPI"
4. Run the workflow

## Build System Changes

- **Old**: `hatchling` build backend with flat layout (`gitbridge/`)
- **New**: `uv_build` backend with src layout (`src/gitbridge/`)

### Benefits of uv_build:
- Native integration with uv toolchain
- Faster builds
- Simpler configuration
- Better workspace support

## Testing Locally

```bash
# Build packages
uv build

# Check dist contents
ls -la dist/

# Install locally for testing
uv pip install dist/gitbridge-*.whl
```

## Workflow Features

- **Trusted Publishing**: No API tokens needed
- **Automatic triggers**: On version tags or GitHub releases
- **TestPyPI support**: Manual workflow dispatch
- **GitHub Release**: Automatic creation with built artifacts
- **Multi-environment**: Separate PyPI and TestPyPI environments