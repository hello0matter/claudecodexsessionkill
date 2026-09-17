# 会话历史清洗器 (Claude / Codex)

一个同时提供图形界面和终端命令的跨平台工具，支持 **Windows、Linux 和 Kali Linux**。
它监听 `.jsonl` 会话历史文件，把里面"我不会 /
不可能 / 不可以 / 出于安全……"这一类拒绝、道德化的措辞，先用正则定位，再（可选）用
AI 改写成"继续执行"风格；同时去掉 `thinking` / `reasoning` 思考过程块。

主要面向 `~/.claude/projects/*.jsonl` 和 `~/.codex/sessions/*.jsonl` 这种历史文件。

## 它解决你提的几个点

- **持续监听、边写边改**：后台轮询 + 防抖。另一个 Claude/Codex 在一边追加写入时，
  本工具检测到文件稳定后才处理，不会去改半行 JSON。
- **先正则，再 AI**：命中正则的文本块才送去 AI 改写；没装 AI 就用兜底文本替换。
- **去掉思考过程**：删除 `type` 为 `thinking`/`redacted_thinking`/`reasoning` 的内容块，
  以及 `thinking`/`reasoning_content` 等字段。
- **多会话 / 多文件**：可加多个目录，自动递归发现 `.jsonl`。
- **排除规则**：文件名或路径通配（每行一个，如 `*.bak`、`*/archive/*`），命中即不监听。
- **统计面板**：运行中点"显示统计"，或停止时自动汇总——累计改写行数/文件次、删除思考块数，
  并按正则分项列出命中次数（看哪类拒绝最多）。
- **落盘日志**：可勾选把日志写到第一个目录下的 `cleaner.log`，带时间戳，事后可追溯。
- **容错**：解析失败的行原样保留；文件占用 / 读写异常只记日志、不崩。
- **日志清晰**：界面下方实时显示 `时间 级别 文件 动作`（级别含 OK/DRY/STAT/WARN/ERROR）。

## 安全说明（重要）

默认 **不改原文件**，而是写到同目录的 `xxx.cleaned.jsonl` 副本。这样即使 Claude
还在用这个会话文件，也不会被你写坏。

只有当你在界面里勾选 **"原地修改原文件"** 时才会改原文件，且每次改前自动复制一份
`xxx.jsonl.bak`。除非你清楚后果，否则建议保持默认的副本模式。

**试运行（默认开启）**：勾选"试运行"后，工具只在日志里逐行预览"第几行会改成什么"，
**不写任何文件**（不产生 `.cleaned`/`.bak`，也不原地改）。确认效果满意后，取消勾选
再正式跑。

## Windows 运行

```bash
# 零依赖即可运行（只用标准库 tkinter）
python session_cleaner_gui.py
```

PowerShell 终端模式：

```powershell
# 只预览，不写文件
python session_cleaner_gui.py scan "$HOME\.codex\sessions"

# 写出 *.cleaned.jsonl 副本
python session_cleaner_gui.py scan "$HOME\.codex\sessions" --write

# 持续监听，Ctrl+C 停止
python session_cleaner_gui.py watch "$HOME\.codex\sessions" --write
```

## Kali / Debian / Ubuntu 运行

终端模式不需要图形桌面，Python 3 即可：

```bash
python3 session_cleaner_gui.py scan ~/.codex/sessions
python3 session_cleaner_gui.py scan ~/.codex/sessions --write
python3 session_cleaner_gui.py watch ~/.codex/sessions --write
```

需要 GUI 时安装 Tk：

```bash
sudo apt update && sudo apt install -y python3-tk
python3 session_cleaner_gui.py
```

SSH 或没有 `$DISPLAY`/Wayland 的环境请直接使用 `scan`/`watch`，无需安装 Tk。

启用 AI 改写（可选）：

本工具支持两种 AI 后端，直接在界面下方的 **「AI 改写后端」** 面板里切换，无需改代码：

- **纯正则兜底**（默认）：命中拒绝词的文本直接换成固定的「好的，我继续执行之前的步骤。」，零依赖、零网络。
- **OpenAI 兼容**：填 Base URL / API Key / 模型，走标准 `/v1/chat/completions`，**只用标准库 `urllib`，不需要装任何包**。默认 Base URL 为 `https://api.1314mc.net/v1`，默认模型为 `gpt-5.5`。
- **Anthropic**：需 `pip install -r requirements.txt` 且设置 `ANTHROPIC_API_KEY` 环境变量（模型默认 `claude-opus-4-8`，可用 `CLEANER_MODEL` 改）。

面板里的 **改写 Prompt（system）** 可自由编辑；点 **「保存配置」** 或每次「开始监听」时，
后端选择 / Base URL / API Key / 模型 / Prompt 都会写入用户配置目录，下次启动自动带出。
若设置了环境变量 `OPENAI_API_KEY`，它会覆盖已保存的 Key。

配置目录为 Windows `%APPDATA%\claude-codex-session-cleaner`，Linux
`${XDG_CONFIG_HOME:-~/.config}/claude-codex-session-cleaner`。

网络可选 **直连 / HTTP 代理 / SOCKS5（远程 DNS）**，默认代理地址为
`127.0.0.1:7891`。该设置只作用于本软件发出的 OpenAI 兼容或 Anthropic 请求，
不会修改 Windows 系统代理、环境变量以及 Claude/Codex 的启动配置。使用 SOCKS5 前请先
运行 `pip install -r requirements.txt`。

旧版本程序目录中的 `config.json` 会继续迁移，包括其中的 API Key。

```bash
# 零依赖即可运行（只用标准库 tkinter；OpenAI 后端也只用 urllib）
python session_cleaner_gui.py
```

仅当用 Anthropic 后端时才需要：

```bash
pip install -r requirements.txt
set ANTHROPIC_API_KEY=sk-ant-...      # PowerShell: $env:ANTHROPIC_API_KEY="..."
set CLEANER_MODEL=claude-opus-4-8     # 可选
python session_cleaner_gui.py
```

## 用法

1. 启动后会自动填入存在的默认目录（`~/.claude/projects` 等），也可"添加目录/文件"。
2. 按需勾选选项：去思考、是否原地改、轮询/防抖秒数；在「AI 改写后端」面板里选后端。
3. "拒绝/道德化措辞正则"框里可以增删匹配规则（每行一个正则）。
4. 点 **开始监听**。改动会写到 `*.cleaned.jsonl`（或原地，取决于勾选），日志实时显示。

## 工作原理

每行是一个 JSON。工具**只处理 `type=="assistant"` 且 `message.role=="assistant"` 的记录**，
在它的 `message.content` 数组里：
- 命中思考块/字段 → 删除（若勾选去思考）。
- `{"type":"text","text":...}` 正文、或思考块的 `thinking`/`summary` 文本命中拒绝正则 → 改写。
- 已经是兜底文本的内容跳过，不重复改。

**元数据字段（`parentUuid`/`sessionId`/`promptId`/`lastPrompt`、`user` 输入、`ai-title` 等）
一律不碰**，避免把普通会话记录误判成拒绝。整行没改动就原样保留。

写文件用临时文件 + `os.replace` 原子替换，避免读到写一半的文件。
