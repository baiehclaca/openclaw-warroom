# OpenClaw WarRoom

A terminal-first operations cockpit for OpenClaw.

OpenClaw WarRoom turns raw session logs into an actionable command center: **intelligent task names**, **live milestones**, **SLA awareness**, and **nested CODING rooms** so you can watch implementation flow in real time.

---

## Name

**Package:** `@sendroon/openclaw-warroom`  
**CLI command:** `openclaw-warroom`

---

## Why this exists

When OpenClaw is doing serious work, transcripts and logs are too low-level for fast operator awareness.
WarRoom provides a high-signal interface that answers:

- What is running right now?
- Which task is blocked?
- What changed in the last minute?
- Which task needs intervention first?
- What is the agent actually coding at this moment?

---

## Core features

### 1) 🎯 CENTER room (mission control)
- Real-time task overview
- Status rollups: Running / Blocked / Done / SLA alerts
- Quick operator triage

### 2) Intelligent task naming
Auto-generates human-useful names from intent and command patterns, e.g.:
- `AETHER: Train Conversations`
- `AETHER: Curate Memory Systems`
- `X: Publish / Engage`
- `Infra: AWS Planning`
- `Comms: Matrix Synapse`

### 3) Milestone timeline per task
Each task room shows a clean progression:
- request received
- tool execution steps
- progress updates
- completion / failure markers

### 4) Nested `↳ CODING` room per task
For every task room, there is a child CODING room with a live stream of:
- tool calls
- assistant coding updates
- execution flow events

Running tasks display an animated orb (`◐◓◑◒`) for immediate visual state.

### 5) SLA and prioritization
- Warn and alert thresholds for long-running tasks
- Pin tasks to keep critical work on top
- Alert-only mode for focused incident handling

### 6) Trace rooms (raw logs)
Optional deep observability via:
- `~/.openclaw/logs/commands.log`
- `~/.openclaw/logs/gateway.log`
- `~/.openclaw/logs/gateway.err.log`

---

## Install (npm)

```bash
npm install -g @sendroon/openclaw-warroom
openclaw-warroom
```

> Requires `python3` (UI core is Textual).

---

## Local dev run

```bash
cd ~/.openclaw/workspace/tools/warroom-cli
./run-warroom.sh
```

---

## Controls

- `mouse click` select room
- `j / k` next / previous room
- `p` pin / unpin selected task
- `a` alert mode (critical focus)
- `r` reload
- `q` quit

---

## Data sources

- Session transcripts: `~/.openclaw/agents/main/sessions/*.jsonl`
- Gateway logs: `~/.openclaw/logs/*`

---

## Positioning

WarRoom is not a generic log viewer. It is an **operator UX layer for OpenClaw**, designed for high-velocity builders who need to supervise autonomous execution without drowning in noise.
