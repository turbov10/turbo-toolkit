# convert-audio

一个零依赖、纯 Python 标准库实现的**音频 ↔ Base64** 双向转换工具集。

包含两个互为反向的 CLI 脚本：

| 脚本 | 方向 | 用途 |
| --- | --- | --- |
| [`audio_to_base64.py`](#audio_to_base64py) | 音频 → Base64 | 把 mp3 / wav / flac / m4a / aac / ogg / opus / webm / aiff 等音频文件编码为 Base64 文本或 Data URI |
| [`base64_to_audio.py`](#base64_to_audiopy) | Base64 → 音频 | 把 Base64 文本（纯文本、带换行、Data URI、JSON 字段）还原为二进制音频文件 |

典型场景：把音频嵌入 JSON / 配置文件、跨文本协议传递音频、按需还原原始文件。

---

## 环境与依赖

- **Python**：3.12（项目根 `.python-version` 锁定）
- **依赖**：仅使用 Python 标准库（`base64`、`argparse`、`mimetypes`、`json`、`dataclasses` 等），**无需 `pip install`**
- **虚拟环境**：本工具独立 `.venv/`（如果尚未创建，可执行 `python -m venv .venv`），运行脚本时建议使用 `convert-audio/.venv/bin/python ...`
- **入口即用**：直接 `python audio_to_base64.py ...` / `python base64_to_audio.py ...` 即可

---

## `audio_to_base64.py`

### 支持的音频扩展名

`.mp3`、`.wav`、`.flac`、`.m4a`、`.aac`、`.ogg`、`.opus`、`.webm`、`.aiff`、`.aif`

可通过 `--no-strict-extension` 跳过扩展名校验。

### 命令行参数

| 参数 | 说明 |
| --- | --- |
| `input`（位置参数） | 输入音频文件路径 |
| `-o`, `--output` | 输出文本文件路径；不指定则打印到 stdout |
| `--data-uri` | 输出 `data:<mime>;base64,<content>` 格式的 Data URI |
| `--wrap <N>` | 每行 Base64 字符数，默认 `76`；设为 `0` 表示不换行 |
| `--no-wrap` | 等价于 `--wrap 0`，输出单行 Base64 |
| `--no-strict-extension` | 跳过音频扩展名白名单校验 |
| `--show-info` | 在 stderr 输出文件大小、MIME Type、Base64 字符数等诊断信息 |

### 输出格式

- 默认输出按 `76` 字符换行的纯 Base64 文本
- 加上 `--data-uri` 会自动根据扩展名推断 MIME（mp3 → `audio/mpeg`、wav → `audio/wav`、flac → `audio/flac`、m4a → `audio/mp4`、aac → `audio/aac`、ogg → `audio/ogg`、opus → `audio/opus`、webm → `audio/webm`、aiff/aif → `audio/aiff`）
- MIME 推断走 `mimetypes.guess_type`，失败时回落到内置字典兜底

### 示例

```bash
# 1. 打印到终端
python audio_to_base64.py ./samples/demo.mp3

# 2. 保存到文本文件
python audio_to_base64.py ./samples/demo.mp3 -o ./outputs/demo.base64.txt

# 3. 输出 Data URI（适合贴进 HTML/CSS 或 JSON）
python audio_to_base64.py ./samples/demo.mp3 --data-uri

# 4. 保存 Data URI 到文件
python audio_to_base64.py ./samples/demo.mp3 -o ./outputs/demo.data-uri.txt --data-uri

# 5. 单行 Base64（便于嵌入单行字符串）
python audio_to_base64.py ./samples/demo.mp3 --no-wrap

# 6. 自定义换行宽度
python audio_to_base64.py ./samples/demo.mp3 --wrap 100

# 7. 跳过扩展名校验（处理不常见但确实是音频的文件）
python audio_to_base64.py ./samples/demo.xyz --no-strict-extension
```

退出码：`0` 成功 / `1` 失败（错误信息写到 stderr）。

---

## `base64_to_audio.py`

### 支持的输入形式

脚本会自动识别以下输入类型：

1. **纯 Base64 文本**（可带任意换行 / 空白）
2. **Data URI**：`data:audio/mpeg;base64,xxxx`
3. **JSON 文本**（通过 `--json-key` 指定字段名，支持点路径，如 `data.audio_base64`）

解码时会自动：

- 去除所有空白字符
- 自动补齐 `=` padding
- 严格校验非法字符（`base64.b64decode(validate=True)`）
- 可选 URL-safe 模式（兼容 `-` 和 `_`）

### 命令行参数

| 参数 | 说明 |
| --- | --- |
| `input`（位置参数） | 输入 Base64 文本 / Data URI / JSON 文件路径 |
| `-o`, `--output` | 输出音频文件路径；不传则基于输入文件名生成；若输入是 Data URI 且输出无扩展名，会按 MIME Type 自动补扩展名 |
| `--json-key <KEY>` | 从 JSON 中按字段名（支持点路径）读取 Base64 |
| `--urlsafe` | 按 URL-safe Base64 解码 |
| `--force` | 允许覆盖已存在的输出文件 |
| `--validate-only` | 只校验 Base64 是否可解码，不写文件 |
| `--show-info` | 在 stderr 输出输入类型、MIME Type、解码后字节数等诊断信息 |

### 输出扩展名推断规则

- 显式传 `-o`：以传入路径为准
- 未传 `-o` 时：以输入文件名为基础去掉原扩展名
- Data URI 输入且输出无扩展名：按 `MIME_TO_EXTENSION` 字典补全（mp3 / wav / flac / m4a / aac / ogg / opus / webm / aiff）
- 仍无扩展名：兜底为 `.bin`

### 示例

```bash
# 1. 还原为 mp3
python base64_to_audio.py ./outputs/demo.base64.txt -o ./outputs/restored.mp3

# 2. Data URI 输入 → 自动按 MIME 补扩展名
python base64_to_audio.py ./outputs/demo.data-uri.txt -o ./outputs/restored

# 3. 强制覆盖已有文件
python base64_to_audio.py ./outputs/demo.base64.txt -o ./outputs/restored.mp3 --force

# 4. 只校验 Base64，不写文件
python base64_to_audio.py ./outputs/demo.base64.txt --validate-only

# 5. 从 JSON 字段读取（点路径）
python base64_to_audio.py ./outputs/demo.json -o ./outputs/restored.mp3 --json-key audio.base64

# 6. URL-safe Base64 解码
python base64_to_audio.py ./outputs/urlsafe.txt -o ./outputs/restored.mp3 --urlsafe

# 7. 调试：显示输入类型、MIME、大小
python base64_to_audio.py ./outputs/demo.data-uri.txt -o ./outputs/restored --show-info
```

退出码：`0` 成功 / `1` 失败（错误信息写到 stderr）；输出文件已存在且未传 `--force` 时也会以非零码退出。

---

## 端到端往返示例

```bash
# 1. 编码
python audio_to_base64.py ./samples/demo.mp3 -o ./outputs/demo.base64.txt

# 2. 解码
python base64_to_audio.py ./outputs/demo.base64.txt -o ./outputs/demo.restored.mp3

# 3. （可选）用 diff 验证二进制一致
cmp ./samples/demo.mp3 ./outputs/demo.restored.mp3 && echo "OK: 字节级一致"
```

Data URI 往返：

```bash
python audio_to_base64.py ./samples/demo.wav --data-uri -o ./outputs/demo.uri.txt
python base64_to_audio.py ./outputs/demo.uri.txt -o ./outputs/demo.restored.wav
```

---

## 常见问题

- **输出文件已存在？** `base64_to_audio.py` 默认拒绝覆盖，需加 `--force`。
- **扩展名不在白名单？** `audio_to_base64.py` 会拒绝；加 `--no-strict-extension` 跳过校验。
- **MIME 推断不准确？** 内置对常见音频格式有兜底映射；如需自定义，建议先转成 Data URI 文本再解码。
- **超大音频？** 脚本一次性把整个文件读入内存。几百 MB 以内没问题；GB 级文件建议改成分块流式处理。
- **Windows / Linux 路径？** 使用 `pathlib.Path`，跨平台无差异；`~` 会被自动展开。
