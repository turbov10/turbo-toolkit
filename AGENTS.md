# Project Guidelines

## 架构概述

这是一个**独立工具的 monorepo**。每个顶层目录（如 `web-search/`、`web-trigger/`、`convert-audio/`、`image-ocr/`）都是一个自包含的工具，拥有自己的语言、依赖、配置和 README。

`agent-gateway/` 是一个特殊例外：它是**仓库级的 MCP stdio server**，负责把每个工具目录的 `mcp_tools.py` 聚合起来，对外暴露给 LLM Agent（详见§5）。

---

## 项目目录一览

| 目录 | 语言 | 用途 | 关键文件 |
|---|---|---|---|
| `web-search/` | Python | CLI 搜索引擎聚合工具，支持 Google / Bing / Baidu / Gemini，输出 JSON 结果 | `cli.py`, `engines/*.py`, `.env` |
| `web-trigger/` | Python | 基于 Playwright 的定时网页自动化工具，按 cron/时间段开窗 → 轮询元素 → 触发 → 后续流程 | `web_trigger.py`, `config.yaml`, `test_page.html` |
| `convert-audio/` | Python | 纯标准库音频 ⇄ Base64 双工转换（无第三方依赖） | `audio_to_base64.py`, `base64_to_audio.py`, `mcp_tools.py` |
| `image-ocr/` | Python | 提取图片中的文字（PNG / JPEG / WebP / HEIC），macOS Vision + 跨平台 rapidocr | `mcp_tools.py`, `image_ocr/cli.py` |
| `agent-gateway/` | Python | 仓库级 MCP stdio server：聚合所有工具的 `mcp_tools.py` | `agent_gateway/{cli,discovery,runner,schema,mcp_server,config}.py`, `tests/` |

---

## 核心规则

### 1. 工具独立性

- 每个工具目录是**独立的项目**，拥有自包含的语言、依赖、配置、`README.md` 和环境变量
- **禁止跨目录干扰**：工具间不共享依赖、虚拟环境、`node_modules` 或配置
- 切勿为一个工具安装包到另一个工具的目录中
- 始终查阅各工具自有 `README.md` / `requirements.txt` / `package.json` / `Cargo.toml` / `.env.example` 等获取设置和使用说明
- **`agent-gateway/` 是唯一的"非独立例外"**：它显式地引用 `mcp[cli]` 和 `PyYAML`，且是 *调用* 其他工具 subprocess 的入口。它本身不实现业务能力，所以"被别人依赖"也不会污染业务工具。

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
- agent-gateway 通过 `subprocess.run([<tool_dir>/.venv/bin/python, <tool_dir>/mcp_tools.py, ...], cwd=<tool_dir>)` 切到目标工具的 venv 执行

### 4. 工具专属约定

- 始终先检查各工具的 `README.md` 了解具体用法
- `.env` 文件（API 密钥等）只在各自工具目录下，不在根目录共享
- `.python-version` 文件在各工具根目录下可选，缺失时以项目根目录为准

### 5. MCP 集成（`mcp_tools.py` 契约）

任何 Python 工具若想通过 `agent-gateway` 暴露给 LLM Agent，**必须**在工具根目录下提供一个 `mcp_tools.py`，满足以下契约（与 [`docs/superpowers/specs/2026-07-03-agent-gateway-mcp-integration-design.md`](docs/superpowers/specs/2026-07-03-agent-gateway-mcp-integration-design.md) §4 同步）：

#### 5.1 文件布局

```
<tool_dir>/mcp_tools.py     # 必须存在
<tool_dir>/.venv/           # 工具自己的 venv（agent-gateway 通过 .venv/bin/python 调用）
<tool_dir>/tests/test_mcp_tools.py   # 推荐：覆盖 MCP tool 函数的烟测
```

#### 5.2 必须的导出

```python
TOOL_NAMESPACE: str          # 例如 "convert-audio"、"image-ocr"。全局唯一。

def <tool_fn_1>(...) -> dict:   # 纯 Python 可 import 可单测
    ...
def <tool_fn_2>(...) -> dict:
    ...

def register(mcp):              # gateway 启动时调用一次
    mcp.tool(name=f"{TOOL_NAMESPACE}__<bare_name>",
             description="...")(<tool_fn>)

if __name__ == "__main__":      # subprocess 入口；gateway 用其分发 tool call
    # 解析 --name / --args，调用对应函数，json.dump 到 stdout
```

#### 5.3 强约束

1. **禁止在 `mcp_tools.py` 顶层 `import`** 任何运行时重依赖（如 Pillow、rapidocr-onnxruntime、Playwright 等）。重依赖在 `register()` 内部或 `__main__` 入口**延迟 import**，从而：
   - agent-gateway 的 `discovery` 阶段在工具的 venv 缺失时不会硬抛；
   - gateway 本身无须安装工具的重依赖。
2. 工具函数必须是**纯 Python**（不依赖 MCP SDK），可被 `from mcp_tools import <tool_fn>` 直接单元测。
3. `register(mcp)` 注册的 name 形如 `f"{TOOL_NAMESPACE}__{fn.__name__}"`。
4. `python mcp_tools.py call --name <bare> --args '<json>'`：
   - 成功 → 退出 0，stdout = JSON 结果
   - 未知工具名 → 退出 2，stderr 写 `unknown tool: <name>`
   - 函数抛异常 → 退出 1，stderr 写 `<ExceptionClass>: <msg>`
5. **命名空间必须全局唯一**。gateway 检测到冲突时记 WARNING 保留第一个（设计稿 §9 碰撞策略）。

#### 5.4 端到端验证流程

完成 `mcp_tools.py` 后，必须用 gateway CLI 验收：

```bash
cd agent-gateway
.venv/bin/python -m agent_gateway list   --root .. | grep <TOOL_NAMESPACE>
.venv/bin/python -m agent_gateway info  <TOOL_NAMESPACE>__<tool> --root ..
.venv/bin/python -m agent_gateway call  <TOOL_NAMESPACE>__<tool> \
    --args '<json>' --root ..
```

并在工具自己的 `tests/` 里加 `test_mcp_tools.py`，覆盖：
- 工具函数直接调用；
- `mcp_tools.py call --name <bare> --args '<json>'` 作为 subprocess 跑通；
- 未知工具名退码 2。

#### 5.5 现有状态

| 工具 | mcp_tools.py | 测试 | 计划阶段 |
|---|---|---|---|
| `convert-audio/` | ✅ | `tests/test_mcp_tools.py` 17 项 | P3 已完成 |
| `image-ocr/`    | ✅ | `tests/test_mcp_tools.py` + 业务测试 31 项 | P2 已完成 |
| `web-search/`   | ❌ | — | P4 待办 |
| `web-trigger/`  | ❌ | — | P5 待办 |
