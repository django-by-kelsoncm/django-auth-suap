# Security Policy

## Supported Versions

The following versions of `django-suap-auth` are currently supported with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 1.6.x   | :white_check_mark: |
| < 1.6.0 | :x:                |

We strongly recommend upgrading to the latest `1.6.x` release to receive security updates.

---

## Reporting a Vulnerability

We take the security of `django-suap-auth` seriously. If you discover a security vulnerability, please report it responsibly:

1. **Private Vulnerability Reporting**: Use GitHub's [Private Vulnerability Reporting](https://github.com/django-by-kelsoncm/django-auth-suap/security/advisories/new) feature on this repository.
2. **Direct Contact**: If Private Vulnerability Reporting is unavailable, email **Kelson C. Medeiros** at [kelsoncm@gmail.com](mailto:kelsoncm@gmail.com) with details.

### Please Include:
- A description of the vulnerability and potential impact.
- Steps to reproduce the issue or a proof of concept (PoC).
- Affected versions.

### What NOT to do:
- Please **do not** open a public GitHub issue for security vulnerabilities.
- Please **do not** disclose the vulnerability publicly until a patch has been released.

---

## Response Process & Timelines

- **Acknowledgement**: We will acknowledge receipt of your report within 48 hours.
- **Triage & Patch**: We aim to investigate and develop a security patch within 7 business days.
- **Disclosure**: Once a fix is released, a public security advisory will be published detailing the vulnerability and fix.

---

## Security Best Practices for Production

When deploying `django-suap-auth` in production environments, ensure you follow these security guidelines:

1. **Keep Secrets Confidential**: Never commit `CLIENT_SECRET` to version control. Always load configuration from environment variables (e.g., `python-dotenv`, `django-environ`).
2. **Use HTTPS**: Always use HTTPS for both your application URL (`REDIRECT_URI`) and the SUAP server URL (`BASE_URL`) to prevent token interception.
3. **Session Security**: Keep `DIRECT_REDIRECT = True` or ensure proper state validation parameters are maintained across sessions.
4. **Regular Updates**: Keep Django and `django-suap-auth` updated to their latest security releases.
