# Support & Maintenance

## Supported Python Versions

- **Python 3.9+** - Minimum supported version
- **Python 3.10, 3.11, 3.12** - Fully tested
- **Python 3.13+** - Expected to work but not yet tested

## What "Stable API" Means

For v1.x releases, stability applies to symbols exported in `__all__`:

```python
from ai_utilities import __all__
print(__all__)
# These symbols are guaranteed stable in v1.x
```

**Stable Public API:**
- `AiClient`, `AsyncAiClient`, `AiSettings`, `create_client`
- `AskResult`, `UploadedFile`
- `JsonParseError`, `parse_json_from_text`
- Audio processing: `AudioProcessor`, `load_audio_file`, `save_audio_file`, etc.

**Internal Modules:**
- Providers, cache backends, utilities may change in minor releases
- Not part of the stability guarantee
- Use at your own risk

## Breaking Changes Policy

**v1.x Releases:**
- No breaking changes to stable public API
- Internal modules may change between minor releases
- Deprecation warnings for any future breaking changes

**v2.0+ Releases:**
- Breaking changes may occur with proper deprecation cycle
- Migration guide provided
- Clear upgrade path documented

## Issue Scope

**In Scope:**
- Bug reports for stable API
- Security vulnerabilities
- Documentation issues
- Installation problems

**Out of Scope:**
- Internal module changes
- Feature requests that require API changes
- Provider-specific issues (OpenAI, Anthropic, etc.)
- Usage questions (use GitHub Discussions)

## Maintenance Expectations

**Active Maintenance:**
- Security patches for v1.x
- Bug fixes for stable API
- Documentation updates
- Python version compatibility

**Best Effort:**
- Provider updates for external API changes
- Performance improvements
- Internal refactoring

**No Maintenance:**
- Deprecated features (after deprecation period)
- EOL Python versions
- Third-party provider issues

## Getting Help

1. **Documentation** - Check README and docs/ first
2. **GitHub Issues** - For bugs and security issues
3. **GitHub Discussions** - For questions and community support
4. **Examples** - See examples/ directory for common patterns

## Release Schedule

- **Patch releases** (1.0.x): As needed for bugs and security
- **Minor releases** (1.x.0): Feature updates, no breaking changes
- **Major releases** (2.x.0): Breaking changes with migration guide

---

*This document reflects our current maintenance commitments and may evolve over time.*
