# Security Policy

## Supported versions

Only the latest commit on `main` receives security fixes. Older commits are
not maintained.

## Reporting a vulnerability

**Please do not open a public GitHub issue for security vulnerabilities.**

Report privately via one of the following channels:

1. **GitHub Security Advisories:** open a
   [private security advisory](https://github.com/turbov10/turbo-toolkit/security/advisories/new)
   on this repository.
2. **Email:** the contact address listed on the maintainers' GitHub profiles.

Please include:

- Tool name and affected file(s)
- Reproduction steps or proof-of-concept
- Impact assessment
- Suggested fix (optional)

You should receive an acknowledgement within 72 hours.

## Secrets and API keys

This repository's `.gitignore` excludes `.env` and `*.local.*` files, and
GitHub Secret Scanning is enabled. **If you accidentally commit a secret:**

1. **Revoke / rotate the credential immediately** at the provider (do not wait
   for a PR to be merged).
2. Open a private security advisory with the file path and commit SHA. Do not
   reference the secret value in the report.
3. Do not push force-rewrites of git history yourself unless explicitly
   requested by a maintainer — force-pushes of `main` are disruptive.

## Scope

In-scope reports:

- Credential or secret exposure (`.env`, `auth.local.json`, etc.)
- Command injection / path traversal in any CLI
- Dependency vulnerabilities with a realistic impact
- Unsafe deserialization or shell execution

Out of scope:

- Denial of service against your own machine
- Issues requiring the attacker to already have local code execution
- Missing rate limiting on third-party APIs (provider's responsibility)
- Misuse of `web-trigger` against sites where the operator does not have
  permission to automate (this is a usage-policy issue, not a code defect)

## Recognition

We are happy to credit reporters in the advisory release notes unless they
prefer to remain anonymous.
