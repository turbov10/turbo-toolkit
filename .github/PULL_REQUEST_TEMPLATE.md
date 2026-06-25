---
name: Pull request
about: Open a PR for one tool in the monorepo
title: "[<tool>] <short summary>"
---

## Tool

Which tool does this PR touch? (single tool per PR, please)

## Summary

What does this PR do and why?

## Type of change

- [ ] Bug fix
- [ ] New feature
- [ ] Refactor / cleanup
- [ ] Documentation
- [ ] CI / tooling

## How I tested

- [ ] `ruff check .` passes
- [ ] `ruff format --check .` passes
- [ ] `pytest -q` passes (added or updated tests)
- [ ] Manually verified (describe below)

Manual verification:

## Checklist

- [ ] No secrets committed (no real API keys, cookies, or credentials)
- [ ] Added/updated tests for behavior changes
- [ ] Updated the relevant tool's `README.md` if user-facing behavior changed
- [ ] Single tool per PR (no cross-tool changes)
