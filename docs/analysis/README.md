# Engineering Analysis Documentation

This directory contains internal engineering analysis documents and notes.

## Purpose

The files in `docs/analysis/` are **internal engineering documentation** that provide:

- Time-bound snapshots of analysis work
- Coverage reports and testing progress
- Architecture decision records
- Performance investigations
- Debugging and diagnostic information

## Important Notes

**These documents are NOT part of the stable public API or user-facing documentation.**

### Status Classification

All documents in this directory should be treated as:

- **Snapshots**: They represent a point in time and may become outdated
- **Engineering notes**: Internal technical discussions and analysis
- **Non-contractual**: Not guaranteed to remain accurate or maintained
- **Supplemental**: Complement but do not replace user-facing documentation

### User-Facing Documentation

For stable, user-facing documentation, see:

- `README.md` (main project documentation)
- `docs/user/` (user guides and tutorials)
- `docs/examples/` (copy-paste examples)
- `docs/cheat_sheet.md` (quick reference)

## Naming Convention

New analysis documents must follow this naming convention:

```
YYYY-MM-DD_<descriptive-name>.md
```

### Required Metadata Header

Each analysis document must include this metadata header at the top:

```markdown
<!-- 
Version: v1.0.0
Date: YYYY-MM-DD
Status: snapshot
Scope: <brief description of scope>
Notes: This document may be outdated. See docs/analysis/README.md for context.
-->
```

## Examples

Valid document names:
- `2024-01-15_coverage_analysis.md`
- `2024-02-20_performance_investigation.md`
- `2024-03-10_architecture_review.md`

Invalid document names:
- `coverage_analysis.md` (missing date prefix)
- `COVERAGE_REPORT.md` (wrong format)
- `temp_notes.md` (not descriptive enough)

## Maintenance

- **No guarantee of updates**: These documents are not actively maintained
- **May be outdated**: Information reflects the time of creation
- **Reference material**: Use as historical context, not current truth
- **No breaking change notifications**: Changes to these files do not follow semantic versioning

## Scratch Space

For temporary or experimental work, use `docs/analysis/_scratch/` (ignored by git).

This directory is intended for:
- Draft analysis documents
- Temporary investigation notes
- Work-in-progress documentation
- Experimental content

Files in `_scratch/` are not tracked and can be freely modified or deleted.

## Integration with CI

Analysis documents are:
- **Not required** for CI/CD processes
- **Not validated** by documentation tests
- **Not part of** the documentation contract
- **Excluded from** link checking and validation

## Contributing

When adding analysis documents:

1. Use the required naming convention
2. Include the metadata header
3. Focus on technical accuracy over polish
4. Reference the date and version clearly
5. Consider moving finished work to appropriate user-facing docs

## Related Directories

- `docs/user/` - Stable user documentation
- `docs/dev/` - Development setup and architecture
- `docs/internal/` - Internal team documentation
- `README.md` - Main project documentation
