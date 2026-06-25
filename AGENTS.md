# Project Guidelines

## 架构概述

这是一个**独立工具的 monorepo**。每个顶层目录（如 `web-search/`、`web-trigger/`）都是一个自包含的工具，拥有自己的语言、依赖、配置和 README。

---

## 项目目录一览

| 目录 | 语言 | 用途 | 关键文件 |
|---|---|---|---|
| `web-search/` | Python | CLI 搜索引擎聚合工具，支持 Google / Bing / Baidu / Gemini，输出 JSON 结果 | `cli.py`, `engines/*.py`, `.env` |
| `web-trigger/` | Python | 基于 Playwright 的定时网页自动化工具，按 cron/时间段开窗 → 轮询元素 → 触发 → 后续流程 | `web_trigger.py`, `config.yaml`, `test_page.html` |

---

## 核心规则

### 1. 工具独立性

- 每个工具目录是**独立的项目**，拥有自包含的语言、依赖、配置、`README.md` 和环境变量
- **禁止跨目录干扰**：工具间不共享依赖、虚拟环境、`node_modules` 或配置
- 切勿为一个工具安装包到另一个工具的目录中
- 始终查阅各工具自有 `README.md` / `requirements.txt` / `package.json` / `Cargo.toml` / `.env.example` 等获取设置和使用说明

### 2. Python 版本约定

- 项目 Python 版本锁定在根目录 `.python-version` 中（当前：**3.12.12**）
- 所有 Python 工具统一使用 **Python 3.12**
- 优先使用 **pyenv** 管理项目本地 Python 环境
- 使用 `pyenv local 3.12.12` 设定工具目录的局部版本（如果尚未设置）

### 3. Python 虚拟环境约定

- 每个 Python 工具的虚拟环境在**该工具自身目录**内的 `.venv/`（已加入 `.gitignore`）
- 判断流程：
  1. 检查工具根目录下是否存在 `.venv/`
  2. 如果**存在** → 执行 Python 程序时**始终使用此 venv**（`tool_dir/.venv/bin/python`）
  3. 如果**不存在** → 用工具本地 Python 创建：`python -m venv .venv`
- `.venv/` 不会跨工具复用，也不在项目根目录共享

### 4. 工具专属约定

- 始终先检查各工具的 `README.md` 了解具体用法
- `.env` 文件（API 密钥等）只在各自工具目录下，不在根目录共享
- `.python-version` 文件在各工具根目录下可选，缺失时以项目根目录为准
