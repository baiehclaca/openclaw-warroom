<p align="center">
  <h1 align="center">⚡ OpenClaw WarRoom</h1>
  <p align="center">
    Terminal-first operations cockpit for OpenClaw — intelligent task rooms, milestone timelines, and live coding visibility.
  </p>
</p>

<p align="center">
  <a href="https://github.com/baiehclaca/openclaw-warroom/releases"><img src="https://img.shields.io/github/v/release/baiehclaca/openclaw-warroom?label=release" alt="release"></a>
  <a href="https://www.npmjs.com/package/@sendroon/openclaw-warroom"><img src="https://img.shields.io/npm/v/@sendroon/openclaw-warroom" alt="npm"></a>
  <a href="https://www.npmjs.com/package/@sendroon/openclaw-warroom"><img src="https://img.shields.io/npm/dm/@sendroon/openclaw-warroom" alt="downloads"></a>
  <a href="./LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue" alt="license"></a>
</p>

---

## What is WarRoom?

**OpenClaw WarRoom** is a high-signal TUI for supervising autonomous agent execution.

Instead of reading raw logs, you get:
- a **CENTER** mission board
- **intelligently named** task rooms
- per-task **milestone progression**
- nested **CODING rooms** with live implementation stream
- SLA-style urgency cues for fast intervention

Built for founders/operators running many parallel agent tasks.

---

## Why it feels different

Most dashboards are either too shallow (just statuses) or too noisy (raw logs everywhere).
WarRoom gives a layered model:

1. **CENTER** → global awareness (what matters now)
2. **TASK room** → intent + milestones
3. **CODING room** → what the agent is actually doing line-by-line

This keeps you in control without context-switch fatigue.

---

## Core features

### 🎯 CENTER room
- Running / Blocked / Done / SLA summary
- Priority-oriented list of active tasks
- Pin support for mission-critical threads

### 🧠 Intelligent task naming
Automatic naming from real intent and commands, e.g.:
- `AETHER: Train Conversations`
- `AETHER: Curate Memory Systems`
- `X: Publish / Engage`
- `Infra: AWS Planning`
- `Comms: Matrix Synapse`

### 🪜 Milestone timeline
Every task builds a compact timeline of:
- request received
- tool execution
- progress updates
- completion / error events

### 🧩 Split view (milestones + live feed)
Task and coding rooms render as:
- **Left pane:** milestones + metadata
- **Right pane:** live coding / execution feed
- Smooth horizontal pan (`h` / `l`) for long lines

### 🔔 PINGS room (memory + follow-ups)
Dedicated room for "ping me when done" workflows:
- shared ping memory stream
- manual watch pings from any selected room (`g`)
- visible completion/blocker outcomes

### ⚙️ Customization menu
Open `CONFIG` room (`m`) to control visible windows and layout.
Window toggles:
- `1` CENTER
- `2` PINGS
- `3` TASKS
- `4` CODING
- `5` TRACE

### 🛰 Nested `↳ CODING` room
Each task has a child implementation room with real-time stream of:
- tool calls
- coding updates
- execution events

### 🚨 Operator controls
- SLA warning and alert thresholds
- Pin/unpin task rooms
- Alert-only mode
- Seamless refresh strategy to reduce flicker/reload jitter

---

## Install

```bash
npm install -g @sendroon/openclaw-warroom
openclaw-warroom
```

> Requires `python3` (UI core is Textual).

---

## Usage (local dev)

```bash
cd ~/.openclaw/workspace/tools/warroom-cli
./run-warroom.sh
```

### Multi-terminal linking + custom layouts

Use **same link id** to share ping memory between terminals, and different profiles for different window layouts:

```bash
# Operator layout
./run-warroom.sh --profile ops --link team1

# Executive layout (separate terminal)
./run-warroom.sh --profile exec --link team1
```

Equivalent npm command:

```bash
openclaw-warroom --profile exec --link team1
```

---

## Keybindings

- `mouse click` select room
- `j / k` next / previous room
- `h / l` horizontal pan left/right
- `p` pin / unpin selected task
- `g` add ping entry from selected room
- `m` open customization menu (`CONFIG` room)
- `1..5` toggle windows (center, pings, tasks, coding, trace)
- `a` toggle alert mode
- `r` reload
- `q` quit

---

## Data sources

- Session transcripts: `~/.openclaw/agents/main/sessions/*.jsonl`
- Gateway logs: `~/.openclaw/logs/*`

---

## Bug reporting

Use GitHub Issues (templates included):

- 🐞 Report bug: `https://github.com/baiehclaca/openclaw-warroom/issues/new?template=bug_report.yml`
- 💡 Feature request: `https://github.com/baiehclaca/openclaw-warroom/issues/new?template=feature_request.yml`

### Maintainer notifications

To get instant notifications for new reports:
1. Open repo on GitHub → **Watch**
2. Choose **Custom**
3. Enable **Issues** (and optionally **Pull requests**)

---

## Positioning

OpenClaw WarRoom is not a generic log tailer.
It is an **operator UX layer** for real-time human-in-the-loop control of autonomous execution.

If OpenClaw is your engine, WarRoom is your cockpit.
