# Security Policy

## Supported Versions

| Version | Supported |
|---|---|
| Latest `main` | ✅ |
| Older releases | ❌ |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please report it responsibly.

### How to Report

**⚠️ Please do NOT open a public GitHub issue for security vulnerabilities.**

Instead, please report vulnerabilities by emailing:

📧 **security@openjustice.lk**

Alternatively, you can use [GitHub's private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability) feature on this repository.

### What to Include

- A description of the vulnerability
- Steps to reproduce the issue
- Potential impact assessment
- Any suggested fixes (if available)

### What to Expect

- **Acknowledgment**: We will acknowledge your report within **48 hours**
- **Assessment**: We will assess the severity and impact within **5 business days**
- **Resolution**: We aim to resolve critical vulnerabilities within **14 days**
- **Disclosure**: We will coordinate with you on public disclosure timing

### Scope

The following are in scope for security reports:

- Authentication and authorization bypasses
- SQL injection, XSS, CSRF vulnerabilities
- Sensitive data exposure
- API security issues
- Dependency vulnerabilities with known exploits

### Out of Scope

- Issues in third-party services (OpenAI, Twilio, Azure) — report those directly to the provider
- Social engineering attacks
- Denial of service (DoS) attacks
- Issues requiring physical access

## Security Best Practices for Contributors

- Never commit secrets, API keys, or credentials to the repository
- Use environment variables for all sensitive configuration
- Keep dependencies updated and review security advisories
- Follow the principle of least privilege in code and infrastructure

## Acknowledgments

We appreciate security researchers who help keep OpenJustice and its users safe. With your permission, we will acknowledge your contribution in our security advisories.
