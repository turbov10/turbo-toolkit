# Project Guidelines

## Architecture

This is a **monorepo of independent tools**. Each top-level directory (e.g., `web_search/`) is a self-contained tool.

### Key Rules

- **Each tool is independent.** Every top-level directory is a standalone project with its own language (Python, TypeScript, Rust, etc.), dependencies, config, README.md, and environment variables.
- **No cross-folder interference.** Tools do not share dependencies, virtual environments, `node_modules`, or configuration. Never install packages for one tool into another tool's directory.
- **Tool-specific conventions.** Always check each tool's own `README.md`, `requirements.txt`, `package.json`, `Cargo.toml`, `.env.example`, etc., for setup and usage instructions. Do not assume conventions from one tool apply to another.
