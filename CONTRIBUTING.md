# Contributing to turbo-toolkit

Thanks for your interest in contributing! This monorepo contains several
independent tools. **Please open the issue or PR inside the relevant tool's
directory** so the right reviewers get notified.

## Ground rules

- Be respectful. See [`CODE_OF_CONDUCT.md`](./CODE_OF_CONDUCT.md).
- One tool per change set. Do not mix changes across tools in a single PR.
- Do not commit secrets. Use `.env.example` for templates and keep real keys
  out of git (see `.gitignore`).
- Tool independence is enforced: do not share dependencies, virtualenvs, or
  configuration between tools.

## Development workflow

### 1. Fork & clone

```bash
git clone https://github.com/<your-fork>/turbo-toolkit.git
cd turbo-toolkit
```

### 2. Pick a tool and set up its venv

```bash
cd <tool>
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install ruff pytest   # dev tooling
```

The repository pins Python 3.12 in `.python-version`. Use `pyenv` if you need
to switch versions.

### 3. Make your change

- Follow the existing style of the tool you are editing.
- Add or update tests when behavior changes.
- Keep commits focused; write clear messages (`feat:`, `fix:`, `docs:`, ...).

### 4. Run checks locally before pushing

```bash
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/pytest -q
```

CI runs the same checks on every PR.

### 5. Open a Pull Request

- Use the PR template (auto-populated).
- Reference the related issue (`Closes #123`).
- Make sure CI is green before requesting review.

## Reporting bugs

Use the **Bug report** issue template. Include:

- Tool name and version / commit
- Python version (`python --version`)
- Reproduction steps, expected vs. actual behavior
- Relevant logs (redact secrets)

## Suggesting features

Use the **Feature request** issue template. Describe the problem first, then
the proposed solution.

## Adding a new tool to the monorepo

1. Create a top-level directory (e.g. `my-tool/`).
2. Add its own `README.md`, `requirements.txt` / `package.json` / etc.,
   `.env.example` (if needed), and `pyrightconfig.json` (if Python).
3. Update the tool matrix in the root [`README.md`](./README.md).
4. Add CI coverage (the workflow auto-discovers Python tools via
   `*/requirements.txt`).
5. Do not introduce cross-tool dependencies.

## License

By contributing you agree that your contributions will be licensed under the
[MIT License](./LICENSE).
