# turbo-toolkit

A monorepo of small, self-contained, single-purpose CLI utilities. Each top-level
directory is its own project with its own language, dependencies, configuration
and README — they share no state.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](./.python-version)

---

## Tools

| Tool | Language | Description | Status |
| --- | --- | --- | --- |
| [`convert-audio/`](./convert-audio/) | Python | Audio ⇄ Base64 converters for embedding audio in JSON payloads, LLM prompts, etc. | Stable |
| [`web-search/`](./web-search/) | Python | Multi-engine search CLI (Google / Bing / Baidu / Gemini) with JSON output. | Stable |
| [`web-trigger/`](./web-trigger/) | Python | Playwright-based windowed web automation: open window by cron / time range → poll element → trigger → post-flow. | Stable |

See each tool's own `README.md` for setup and usage.

---

## Quick start

Requirements: Python 3.12 (see `.python-version`). `pyenv` is recommended.

```bash
git clone https://github.com/turbov10/turbo-toolkit.git
cd turbo-toolkit

# Each tool has its own virtualenv; create one per tool:
cd web-search && python -m venv .venv && .venv/bin/pip install -r requirements.txt
cd ../web-trigger && python -m venv .venv && .venv/bin/pip install -r requirements.txt
cd ../convert-audio && python -m venv .venv && .venv/bin/pip install -r requirements.txt
```

---

## Repository conventions

- **Tool independence.** Tools do not share dependencies, virtualenvs, or
  configuration. Never install packages from one tool into another.
- **Python version.** All Python tools target the version pinned in the
  repository root `.python-version` (3.12). Tools may opt in to a local
  `.python-version` to pin a different minor if needed.
- **Virtualenvs.** Each tool owns its own `.venv/` (already in `.gitignore`).
- **Environment variables.** Tool-specific secrets live in the tool's `.env`
  (gitignored). Templates go in `.env.example`.
- **AI agent guidance.** See [`AGENTS.md`](./AGENTS.md).

---

## Contributing

Contributions are welcome. Please read
[`CONTRIBUTING.md`](./CONTRIBUTING.md) before opening an issue or PR.
By participating you agree to follow the
[Code of Conduct](./CODE_OF_CONDUCT.md).

## Security

Report vulnerabilities privately per [`SECURITY.md`](./SECURITY.md).
**Do not file public issues for security bugs.**

## License

[MIT](./LICENSE) © 2026 turbo-toolkit contributors.
