# Project Guidelines

## Architecture

This is a **monorepo of independent tools**. Each top-level directory (e.g., `web_search/`) is a self-contained tool, except `playground/`.

### Key Rules

- **Each tool is independent.** Every top-level directory is a standalone project with its own language (Python, TypeScript, Rust, etc.), dependencies, config, README.md, and environment variables.
- **No cross-folder interference.** Tools do not share dependencies, virtual environments, `node_modules`, or configuration. Never install packages for one tool into another tool's directory.
- **Tool-specific conventions.** Always check each tool's own `README.md`, `requirements.txt`, `package.json`, `Cargo.toml`, `.env.example`, etc., for setup and usage instructions. Do not assume conventions from one tool apply to another.

### The `playground/` Directory

`playground/` is a **testing ground** — it contains experimental code, learning exercises, method explorations, and workflow validations. Subdirectories under `playground/` (e.g., `playground/a2a-adk/`, `playground/a2a-langgraph/`) are not standalone tools; they are temporary experiments that may depend on parent project conventions or external references.
