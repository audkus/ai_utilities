# Release Guide

This document describes the manual steps for releasing AI Utilities v1.0.0b1.

## Prerequisites

- Clean working tree with no uncommitted changes
- All tests passing
- Version updated in `pyproject.toml` and `__init__.py`
- CHANGELOG.md updated with release notes

## Release Steps

### 1. Update Version
```bash
# Ensure version is set to 1.0.0b1 in pyproject.toml
# Ensure __version__ is updated in src/ai_utilities/__init__.py
```

### 2. Run Tests
```bash
# Run full test suite
python -m pytest

# Run manual testing harness (optional but recommended)
./manual_tests/run_manual_tests.sh
```

### 3. Build Artifacts
```bash
# Install build tools
python -m pip install -U build

# Build source distribution and wheel
python -m build

# Verify artifacts
ls -la dist/
```

### 4. Tag Release
```bash
# Create and push tag
git tag -a v1.0.0b1 -m "Release v1.0.0b1"
git push origin v1.0.0b1
```

### 5. Create GitHub Release
1. Go to https://github.com/audkus/ai_utilities/releases/new
2. Choose tag: `v1.0.0b1`
3. Target: `main` branch
4. Title: `Release v1.0.0b1`
5. Description: Copy changelog entry from CHANGELOG.md
6. ✅ Check "This is a pre-release"
7. Publish release

### 6. Optional: Publish to PyPI (Pre-release)
```bash
# Install twine if not already installed
python -m pip install -U twine

# Upload to PyPI (test first)
python -m twine upload --repository testpypi dist/*

# Upload to PyPI (production)
python -m twine upload dist/*
```

## Verification

After release:
- [ ] GitHub release created and marked as pre-release
- [ ] Tag pushed to repository
- [ ] Artifacts built successfully
- [ ] (Optional) Package published to PyPI

## Post-Release

- Update version to next development version (e.g., 1.0.0b2.dev0)
- Update CHANGELOG.md with new "Unreleased" section
- Create next release branch if needed

## Notes

- This is a beta pre-release - mark as pre-release in GitHub
- Manual testing harness should be run before final release
- No breaking changes introduced in this release
- All existing tests must continue to pass

## PyPI Trusted Publishing Setup

### Prerequisites (one-time setup)
Before automatic publishing will work, the PyPI Trusted Publisher must be configured manually in the PyPI UI:

1. Go to https://pypi.org/project/ai-utilities/settings/publishing/
2. Add a new trusted publisher with:
   - **Owner**: `audkus` (GitHub organization/username)
   - **Repository**: `ai_utilities`
   - **Workflow**: `.github/workflows/publish.yml`
   - **Environment**: (leave blank for default)

### Pre-release Validation Checklist
Before tagging a release:

- [ ] Version bumped in `pyproject.toml` (e.g., `1.0.0b1`)
- [ ] Version updated in `src/ai_utilities/__init__.py`
- [ ] CHANGELOG.md updated with release notes
- [ ] All tests passing: `python -m pytest`
- [ ] Build artifacts created: `python -m build`
- [ ] PyPI Trusted Publisher configured (one-time setup)

### Publishing Process
```bash
# Create and push tag - this triggers automatic publishing
git tag -a v1.0.0b1 -m "Release v1.0.0b1"
git push origin v1.0.0b1

# Monitor: https://github.com/audkus/ai_utilities/actions/workflows/publish.yml
# Check: https://pypi.org/project/ai-utilities/
```

**Important**: Publishing is fully automatic after tag push - no manual PyPI upload needed.
