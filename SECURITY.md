# Security Policy

## Supported Versions

This project follows semantic versioning. Security updates are provided for:

| Version | Supported |
|---------|------------|
| 1.0.x   | Yes        |
| < 1.0   | No         |

## Reporting Vulnerabilities

Please report security vulnerabilities privately to ensure they can be addressed before disclosure.

### How to Report

Send email to: security@audkus.com

Include:
- Vulnerability description
- Steps to reproduce (if applicable)
- Potential impact assessment
- Any proposed mitigations (optional)

### Response Expectations

- **Initial response**: Within 48 hours
- **Assessment**: Within 7 days
- **Resolution**: As appropriate based on severity
- **Disclosure**: After fix is available

### What to Include

- Detailed description of the vulnerability
- Proof of concept or reproduction steps
- Environment details (Python version, dependencies)
- Any relevant logs or error messages

### What Not to Include

- Do not open public issues for security vulnerabilities
- Do not disclose vulnerabilities publicly before coordination
- Do not exploit vulnerabilities in production systems

## Security Best Practices

Users should follow these security practices:

- Keep dependencies updated
- Use environment variables for API keys
- Review provider-specific security guidelines
- Monitor for security advisories
- Use principle of least privilege for API keys

## Dependency Security

This project:
- Scans dependencies for known vulnerabilities
- Updates dependencies when security issues are found
- Provides security updates in patch releases
- Documents any security-related changes

## Security-Related Features

- API keys are loaded from environment variables only
- No credentials are logged or stored in cache
- SSL/TLS verification is enforced by default
- Provider-specific security configurations are supported

## Contact

For security-related questions not requiring vulnerability disclosure:
- Create an issue with "security" label
- Check existing security discussions
- Review documentation for security guidance
