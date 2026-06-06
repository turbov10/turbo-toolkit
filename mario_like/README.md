# Terminal Pixel Adventure

一个跑在终端里的像素风横版平台跳跃小游戏，用 Node.js + TypeScript + React + [Ink](https://github.com/vadimdemedes/ink) 写成。**没有浏览器、没有 Canvas、没有后端、没有网络、没有数据库**，全部逻辑都在本地项目内完成。

致敬经典横版平台跳跃游戏，但使用原创名字、原创字符图形和原创两关布局。玩法简单：向右跑，跳过沟壑，躲开蘑菇敌人，触碰终点旗帜即可通关。

---

## 特性

- 内置 **2 个手工关卡**（第一关 160 tiles 宽教学关，第二关 220 tiles 宽进阶关）
- 基于 tile 的 AABB 碰撞、重力、跳跃
- 蘑菇敌人会左右巡逻，遇到墙和平台边缘自动掉头
- 横向摄像机跟随玩家，并限制在地图边界内
- 完整状态机：`START_SCREEN` / `LEVEL_INTRO` / `PLAYING` / `PAUSED` / `LEVEL_CLEAR` / `PLAYER_DEAD` / `GAME_OVER` / `GAME_WIN`
- 生命数、死亡次数、通关数统计
- 暂停 / 继续、重开整局、退出
- **彩色 ASCII 渲染**：旗帜绿色、金币亮黄、敌人红色、玩家亮青，地形按类型着色
- **可选音效**：跳跃、死亡、通关时发送 `BEL`（终端铃），可在暂停界面按 `M` 关闭
- **死亡 / 通关界面可按 Enter 立即跳过**（也可以等 1.5 秒自动过）
- 状态切换时自动重置输入，不会出现「死的时候按住右箭头、下一关一上来就向右冲」这种穿帮
- 纯 ASCII 渲染，兼容 macOS Terminal、iTerm2、Linux Terminal 等任何现代 TTY

---

## 环境要求

- macOS 或 Linux
- Node.js **>= 18**
- 一个至少 **80 × 24** 字符的终端

---

## 安装

```bash
cd mario_like
npm install
```

---

## 运行

开发模式（文件改动自动重启）：

```bash
npm run dev
```

或者：

```bash
npm start
```

进入开始界面后按 **Enter** 开始。

---

## 操作

| 按键 | 作用 |
| --- | --- |
| ← / → | 左右移动 |
| Space | 跳跃（仅在地面时） |
| Enter | 开始 / 确认 / **跳过当前过场画面** |
| P | 暂停 / 继续 |
| M | 切换音效（仅在暂停界面） |
| Q | 退出游戏 |
| R | 重新开始（仅在 `GAME_OVER` / `GAME_WIN` 界面） |

> **关于按住方向键：** 终端 raw 模式不会发出「按键抬起」事件，所以按住方向键是通过「150ms 内没收到重复事件就视为松开」的方式模拟的。短按一下就是一小步移动，长按就是持续移动。

---

## 玩法

- 初始 **3 条命**
- 碰到蘑菇敌人直接死
- 掉进沟壑直接死
- 触碰终点旗帜 `F` 通关当前关卡
- 通关第 2 关 = 胜利
- 死亡后会从当前关卡重新开始，并扣一条命
- 命数归 0 进入 `GAME_OVER`

无二段跳、无踩怪、无射击、无存档。保持简单。

---

## 字符图例

| 字符 | 含义 |
| --- | --- |
| `@` | 玩家 |
| `g` | 蘑菇敌人 |
| `F` | 终点旗帜 |
| `#` | 固体地面 / 平台 |
| `B` | 砖块 |
| `?` | 问号块（装饰） |
| `o` | 金币（装饰，无收集） |
| `~` | 背景云朵（无碰撞） |
| ` ` | 空气 |

---

## 项目结构

```
mario_like/
├── package.json
├── tsconfig.json
├── README.md
└── src/
    ├── index.tsx                # 入口
    ├── App.tsx                  # 顶层 React/Ink 组件 + 游戏主循环
    ├── game/
    │   ├── constants.ts         # 可调常量（FPS、物理、时间）
    │   ├── types.ts             # 所有 TypeScript 类型（含 Tile 联合类型）
    │   ├── levels.ts            # 内置关卡 + parseLevel / getLevel
    │   ├── input.ts             # InputState 辅助
    │   ├── physics.ts           # 玩家 / 敌人 / 摄像机更新
    │   ├── collision.ts         # 固体 tile + AABB 检测
    │   ├── renderer.ts          # 渲染成 80×24 彩色 span 帧
    │   └── gameState.ts         # 纯函数状态机
    └── components/
        ├── StartScreen.tsx
        ├── LevelIntro.tsx
        ├── GameView.tsx
        ├── PauseScreen.tsx
        ├── LevelClearScreen.tsx
        ├── PlayerDeadScreen.tsx
        ├── GameOverScreen.tsx
        └── GameWinScreen.tsx
```

---

## 简单实现原理

- `App.tsx` 持有一个 `GameState`，用 `setInterval` 以 **30 FPS** 推进
- `useInput` 捕获键盘事件，左右方向键的「持续按住」靠 150ms 超时模拟
- `physics.ts` 做「X 轴 / Y 轴分离」移动 + 碰到固体回弹，保证玩家不会穿墙
- 蘑菇敌人遇到前方是墙、或者前方脚下是空气时自动反向
- `renderer.ts` 渲染 80×24 字符 buffer，把地图、敌人、玩家按顺序叠加，每行再把同色相邻格子合并成 span
- `gameState.ts` 是上一状态 + 输入 + 时间戳的纯函数，方便单元测试
- 关卡用 `string[]` 存储；`parseLevel` 会把 `P` / `G` 从静态格子中抽出来，放到 metadata 里

---

## 扩展建议

- 收集金币：渲染 `o` tile，碰到就移除并加 HUD 计数
- 新增敌人类型：扩展 `Enemy` 联合，再加一个 `type` 字段
- 新增关卡：把 `RAW_MAPS` 数组再追加一个 `string[]`，或在 `levels.ts` 的 `createRawLevel` config 里多写一段
- 存档：把最高分写到 `os.homedir() + '/.terminal-pixel-runner.json'`
- 真正的 BGM / 音效：用 `process.stdout.write('\x07')` 触发终端铃已经够用；要更复杂可以接 `play-sound` 之类的库

---

## 已知限制

- 物理参数针对 30 FPS 调过；改 `FPS` 后跳跃手感会变
- 只有蘑菇敌人一种；无踩怪、无攻击、无道具
- 没有存档 / checkpoint，Restart = 回到 World 1
- 第一关终点之后没有太多缓冲带，给玩家一种「差点够到」的紧迫感（如果你想更宽松，把 `MAP1_RAW` 的 `goal.x` 改大一点即可）

---

## 许可

MIT。
