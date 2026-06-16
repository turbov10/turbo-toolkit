# web_trigger — 定时网页触发与自动化 CLI

基于 **Playwright** 的定时网页自动化工具。按时间表达式（cron / 时间段）开启"触发窗口"，窗口内高频轮询目标元素并触发，触发成功后执行自定义后续流程。

> ⚠️ 仅用于自动化你**有权操作**的网站/账户，请遵守目标站点条款与当地法律。

---

## 目录

- [安装与初始化](#安装与初始化)
- [快速开始](#快速开始)
- [配置文件参考](#配置文件参考)
- [CLI 命令参考](#cli-命令参考)
- [完整使用场景](#完整使用场景)
- [工作原理](#工作原理)
- [常见问题与排错](#常见问题与排错)
- [本地测试](#本地测试)

---

## 安装与初始化

### 环境要求

- Python **3.12+**
- 依赖包（见 `requirements.txt`）：

| 包 | 用途 | 必需 |
|---|---|---|
| `playwright>=1.44` | 浏览器自动化内核 | ✅ |
| `PyYAML>=6.0` | YAML 配置解析 | ✅ |
| `croniter>=2.0` | cron 时间表达式解析 | ✅ |
| `requests>=2.31` | Webhook 通知 | ❌（可选，默认引用） |

### 安装步骤

```bash
# 1. 进入工具目录（独立环境）
cd web_trigger

# 2. 安装 Python 依赖
pip install -r requirements.txt

# 3. 安装 Playwright 浏览器（Chromium）
python -m playwright install chromium

# 4. 验证安装
python web_trigger.py -c config.yaml check
```

> 本工具是独立项目，与其他目录**不共享** `venv` / `node_modules`。

---

## 快速开始

### 1️⃣ 校验配置

```bash
python web_trigger.py -c config.yaml check
```

输出示例：

```
当前时间: 2026-06-15 13:50:13.487175+08:00
窗口状态: idle
窗口区间: 2026-06-15 21:00:00+08:00 ~ 2026-06-15 21:05:00+08:00
```

- `active` — 当前在触发窗口内，可以进行触发操作
- `idle` — 等待中，显示下一窗口时间

### 2️⃣ 登录并保存会话（登录态站点）

```bash
python web_trigger.py -c config.yaml login
```

会弹出浏览器窗口，手动完成登录后回到终端按回车，会话自动保存到 `storage_state` 指定路径（如 `auth.json`）。后续运行自动复用此会话。

### 3️⃣ 试运行（安全模式）

```bash
python web_trigger.py -c config.yaml --dry-run -v run
```

只检测元素+打印日志，**不执行**点击、填表、提交等写操作。适用于验证选择器是否匹配、时机是否准确。

### 4️⃣ 正式运行

```bash
python web_trigger.py -c config.yaml
```

启动后：
1. 打开浏览器，跳转至 `target_url` 并等待加载
2. 等待时间窗口开启（按 60s 切片 sleep 并刷新窗口状态）
3. 窗口内按 `poll_interval_ms` 高频轮询：若启用 `reload_each_poll` 则每次轮询**前**先 `page.reload` 并等待渲染
4. 找到目标元素并点击
5. 验证成功条件
6. 执行后续流程（截图、填表、通知等）
7. 窗口结束 / 达到 `max_try` / 触发成功 → 若 `stay_after_success=true` 则停留在页面等待回车，否则按 `exit_after_success` 决定退出或继续等下一窗口

### 5️⃣ 可视化调试

```bash
python web_trigger.py -c config.yaml --headful -v
```

强制显示浏览器窗口，便于观察执行过程。配合 `-v` 输出详细日志。

---

## 配置文件参考

配置为 YAML 格式，完整示例见 `config.yaml`。所有字段说明如下：

### 顶层字段

```yaml
target_url: "https://example.com/page"   # 目标页面 URL（必需）
headless: true                            # 是否无头模式（调试时设为 false）
slow_mo_ms: 0                             # 操作间延迟（毫秒），模拟人类操作
storage_state: "auth.json"                # 登录态文件路径，存在则复用
save_storage_state: "auth.json"           # 退出时保存登录态到此文件
# user_agent: "Mozilla/5.0 ..."           # 自定义 User-Agent（可选）
```

### schedule — 调度配置

```yaml
schedule:
  timezone: "Asia/Shanghai"      # 时区（Python zoneinfo 支持的任意时区）
  poll_interval_ms: 300           # 轮询间隔（毫秒）
  jitter_ms: 150                  # 随机抖动（毫秒），在每次轮询间增加随机延迟
  max_try: 1                      # 每次窗口内最大轮询次数（0 表示不限制）
  exit_after_success: true        # 触发成功后是否退出程序
  stay_after_success: false       # 触发成功后是否停留在页面（保持浏览器打开，等待用户回车）
  reload_each_poll: false         # 每次轮询周期开始前是否刷新页面
  windows:                        # 触发窗口列表（可同时配置多个）
```

### windows — 触发窗口（两种模式）

**方式一：cron 表达式（精确时间点 + 持续时长）**

```yaml
windows:
  - cron: "0 10 * * *"           # 每天 10:00 开启窗口
    duration_seconds: 120         # 窗口持续 120 秒
```

适合精确到秒的定时任务（如抢购、定时签到）。

cron 格式：`分 时 日 月 周` （标准 5 字段，由 `croniter` 解析）

**方式二：时间段（简单 HH:MM，支持跨午夜）**

```yaml
windows:
  - range: "21:00-21:05"         # 每天 21:00~21:05 开启窗口
```

适合每天的固定时段。

> 两种方式可混用，**任一窗口激活**则进入触发状态。

### trigger — 触发元素配置

```yaml
trigger:
  selectors:                      # CSS 选择器列表（顺序兜底）
    - "button#buy-now:not([disabled])"
    - "text=立即购买"
  wait_state: "visible"           # 等待条件：visible | enabled | attached
  click_method: "click"           # 点击方式：click | js_click | dispatch
  post_click_wait_ms: 800         # 点击后等待（毫秒），再验证成功条件
```

| 点击方式 | 说明 |
|---|---|
| `click` | Playwright 标准点击（模拟真实鼠标事件） |
| `js_click` | 通过 `element.click()` 直接调用 DOM 方法 |
| `dispatch` | 通过 `dispatchEvent` 派发 click 事件 |

选择器列表按顺序匹配，第一个命中的生效。适合有多个备选文案/选择器的场景。

### success — 成功条件

```yaml
success:
  any_of:                         # 列表中的任一条件满足即视为成功
    - url_contains: "/order/confirm"     # URL 包含指定字符串
    - selector_visible: "text=下单成功"   # 页面出现指定元素
    - js: "() => window.__ORDER_OK__ === true"  # JS 表达式返回 true
```

> 不配置 `success` 则点击即视为成功。

### on_success — 后续流程

```yaml
on_success:
  - action: screenshot                     # 截图
    path: "success_{ts}.png"               # 路径，{ts} 替换为时间戳
    full_page: false                       # 是否截取全页（可选，默认 false）
  - action: eval_js                        # 执行 JavaScript
    script: "() => console.log('done')"
  - action: goto                           # 导航到新页面
    url: "https://example.com/next"
  - action: fill                           # 填写输入框
    selector: "#coupon"
    value: "VIP2026"
  - action: click                          # 点击元素
    selector: "#submit-order"
  - action: wait_for                       # 等待元素出现
    selector: "text=支付"
    state: "visible"                       # visible | attached | hidden（可选）
    timeout_ms: 15000                      # 超时（毫秒，可选）
  - action: sleep                          # 等待指定秒数
    seconds: 2
  - action: notify                         # 通知（日志+可选 Webhook）
    message: "🎉 触发成功！"
    webhook: "https://open.feishu.cn/open-apis/bot/v2/hook/xxxx"  # 可选 Webhook URL
    payload:                               # 自定义请求体（可选，默认自动适配）
      msg_type: "text"
      content:
        text: "🎉 触发成功！"
```

> `--dry-run` 模式下，除 `screenshot` 外所有后续步骤都会被跳过。

---

## CLI 命令参考

```bash
python web_trigger.py [-h] -c CONFIG [--dry-run] [--headful] [-v] {run,login,check}
```

### 全局参数

| 参数 | 说明 |
|---|---|
| `-c, --config CONFIG` | YAML 配置文件路径（**必需**） |
| `--dry-run` | 安全模式：检测元素但不执行写操作 |
| `--headful` | 强制显示浏览器窗口（覆盖配置中的 `headless`） |
| `-v, --verbose` | 输出 DEBUG 级别详细日志 |

### 子命令

| 命令 | 说明 |
|---|---|
| `run`（默认） | 按计划运行，等待窗口 → 触发 → 后续流程 |
| `login` | 手动登录并保存会话到 `storage_state` |
| `check` | 校验配置格式和时间窗口解析，不开浏览器 |

---

## 完整使用场景

### 场景一：定时抢购/秒杀

```yaml
target_url: "https://shop.example.com/product/123"
headless: true
schedule:
  windows:
    - cron: "59 9 * * *"        # 09:59 开启窗口
      duration_seconds: 120      # 持续 2 分钟
  poll_interval_ms: 100           # 高频率轮询
  jitter_ms: 50
trigger:
  selectors:
    - "button#buy-now:not([disabled])"
  wait_state: "enabled"           # 等待按钮可用
  click_method: "click"
success:
  any_of:
    - url_contains: "/order/confirm"
    - selector_visible: "text=下单成功"
on_success:
  - action: screenshot
    path: "order_{ts}.png"
  - action: notify
    message: "🎉 已抢到！"
    webhook: "https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
```

### 场景二：定时签到 + 截图验证

```yaml
target_url: "https://example.com/daily-checkin"
headless: true
schedule:
  timezone: "Asia/Shanghai"
  windows:
    - cron: "0 8 * * *"
      duration_seconds: 300
  max_try: 1
trigger:
  selectors:
    - "button.checkin-btn"
    - "text=签到"
  click_method: "click"
success:
  any_of:
    - selector_visible: "text=已签到"
on_success:
  - action: sleep
    seconds: 2
  - action: screenshot
    path: "checkin_{ts}.png"
    full_page: true
  - action: notify
    message: "✅ 签到完成"
```

### 场景三：表单自动填写提交

```yaml
target_url: "https://example.com/form"
headless: true
schedule:
  windows:
    - range: "10:00-10:30"
  exit_after_success: false       # 可多次触发
  max_try: 5
trigger:
  selectors:
    - "button#start"
success: {}                       # 点击即成功
on_success:
  - action: fill
    selector: "#name"
    value: "张三"
  - action: fill
    selector: "#email"
    value: "zhangsan@example.com"
  - action: click
    selector: "#submit"
  - action: wait_for
    selector: "text=提交成功"
  - action: screenshot
    path: "submit_{ts}.png"
```

---

## 工作原理

```
┌──────────────────────────────────────────────────────────────────┐
│  cmd_run()                                                       │
│    │                                                             │
│    ├─ 加载 YAML 配置                                              │
│    ├─ 初始化 Playwright Chromium（headless / headful）             │
│    ├─ 加载 storage_state（存在则复用登录态）                        │
│    │                                                             │
│    ├─ 进入主循环                                                  │
│    │   ├─ next_state() → 计算当前窗口状态                         │
│    │   │   ├─ cron 窗口：croniter 解析 + duration_seconds         │
│    │   │   └─ range 窗口：HH:MM-HH:MM 解析，支持跨午夜             │
│    │   │                                                         │
│    │   ├─ 状态 = active                                          │
│    │   │   ├─ goto(target_url) + _wait_page_ready()              │
│    │   │   ├─ run_window()                                       │
│    │   │   │   ├─ while now < end_time and tried < max_try:      │
│    │   │   │   │   ├─ [reload_each_poll?] page.reload() +       │
│    │   │   │   │   │              _wait_page_ready()             │
│    │   │   │   │   ├─ find_and_click()                           │
│    │   │   │   │   │   ├─ 遍历 selectors                          │
│    │   │   │   │   │   ├─ 检查 wait_state 条件                    │
│    │   │   │   │   │   └─ 按 click_method 点击                    │
│    │   │   │   │   ├─ post_click_wait_ms 等待                     │
│    │   │   │   │   ├─ check_success() → 任一 any_of 命中          │
│    │   │   │   │   ├─ 成功 → run_post_flow() (on_success 列表)  │
│    │   │   │   │   └─ sleep(poll + random jitter)                │
│    │   │   │   └─ 返回 True(成功) / False(到时/到 max_try)       │
│    │   │   ├─ exit_after_success? → 退出 / 继续                   │
│    │   │                                                         │
│    │   └─ 状态 = idle                                             │
│    │       └─ 等待至下一窗口开始（最多 60s 切片 sleep）             │
│    │                                                             │
│    └─ 退出时保存 save_storage_state（可选）                        │
│       关闭浏览器                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 关键设计点

- **多窗口聚合**：多个 `windows` 配置同时生效，任一激活即进入 active 状态
- **选择器兜底**：`selectors` 列表按顺序匹配，适合多文案场景
- **reload_each_poll 语义**：开启后，**每次轮询周期开始前**调用 `page.reload` 并等待触发选择器渲染（最大 15s）；关闭则整个窗口内复用同一页面（首次由 `cmd_run` 初始 goto 加载）
- **max_try 计数**：上限是**轮询周期数**（无论是否命中元素），`0` 表示无限制；用于在窗口结束前提前止损
- **抖动防检测**：`jitter_ms` 在固定轮询间隔上叠加随机延迟，不易被风控识别
- **点击 ≠ 成功**：点击后还需 `success.any_of` 条件验证，防止误判
- **dry-run 安全**：只读不写，可放心在生产配置上试运行

---

## 常见问题与排错

### Q: 浏览器一闪而过，什么都没发生

检查 `target_url` 是否正确。先手动访问确认页面可打开。

### Q: "Target page, context or browser has been closed"

常见原因：
- 页面加载失败（URL 错误、网络不通、404）
- 目标页面触发了一次导航导致原页面关闭
- 使用 `headful` 模式下手动关闭了浏览器窗口

先用 `--dry-run -v` 运行观察日志。

### Q: 找不到目标元素

- 确认 `selectors` 在当前页面中真实存在
- 打开浏览器开发者工具，用选择器测试
- 检查 `wait_state` 是否匹配元素实际状态（`visible` / `enabled` / `attached`）
- 可先用 `--headful -v` 观察浏览器实际渲染结果

### Q: 点击后总显示"未达成功条件"

- 确认 `success.any_of` 条件能真实命中
- 增大 `post_click_wait_ms` 给页面足够的响应时间
- 可以用 `--headful -v` 观察点击后的页面变化

### Q: 需要登录的站点

```bash
# 1. 首次：手动登录并保存
python web_trigger.py -c config.yaml login

# 2. 后续运行自动复用会话
python web_trigger.py -c config.yaml
```

### Q: macOS 没有 `timeout` 命令

macOS 不自带 `timeout`，如需超时控制：
```bash
# 使用 Python 自身的超时
python -c "__import__('subprocess').run('python web_trigger.py -c config.yaml run', shell=True, timeout=120)"
```

### Q: 触发成功后想手动核对页面再关闭，怎么保留浏览器？

设置 `schedule.stay_after_success: true`。触发成功并执行完 `on_success` 后，浏览器**保持打开**停留在当前页面，程序挂起等待你在终端按回车再关闭。配合 `--headful` 使用效果最佳：

```yaml
schedule:
  exit_after_success: true
  stay_after_success: true   # 触发成功后停在页面，按回车才关闭
```

> 优先级：`stay_after_success=true` 时无视 `exit_after_success`，强制进入"停留等待"分支。非交互环境（nohup / CI / docker）若 stdin 不是 tty，会捕获 `EOFError` 后直接退出。

---

## 本地测试

项目自带一个测试页面 `test_page.html`，可快速验证整套流程。

### 测试页面说明

`test_page.html` 模拟了一个"定时开抢"场景：

- 打开页面时按钮为 `disabled` 状态
- 3 秒后 JavaScript 自动启用按钮
- 点击按钮后：
  - 设置 `window.__ORDER_OK__ = true`（匹配 `success.js` 条件）
  - 页面显示"下单成功"（匹配 `success.selector_visible` 条件）
  - URL 变为 `/order/confirm`（匹配 `success.url_contains` 条件）

### 测试步骤

```bash
# 1. 启动 HTTP 服务器
cd web_trigger
python -m http.server 8000

# 2. 另开终端，校验配置
python web_trigger.py -c config.yaml check

# 3. 试运行（安全模式）
python web_trigger.py -c config.yaml --dry-run -v run

# 4. 正式运行
python web_trigger.py -c config.yaml run

# 5. 可视化调试
python web_trigger.py -c config.yaml --headful -v
```

测试时可将 `config.yaml` 的窗口改为当前时间附近的 `range`，例如：

```yaml
windows:
  - range: "00:00-23:59"   # 全天窗口
```

---

> 更多问题请提交 Issue 或查看 `web_trigger.py` 源码注释。