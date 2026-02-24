# WarRoom CLI

Overdesigned hacker-style task command center for OpenClaw.

## Install (npm)

```bash
npm install -g @teodorwaltervido/openclaw-warroom
openclaw-warroom
```

> Requires `python3` (the UI core is Textual).

## Local run (dev)

```bash
cd ~/.openclaw/workspace/tools/warroom-cli
./run-warroom.sh
```

## What it shows

- `🎯 CENTER` room: task board with statuses and SLA overview
- Intelligent per-task rooms (auto-named from intent/commands), e.g.:
  - `X: Publish / Engage`
  - `AETHER: Train <topic>`
  - `Infra: AWS Planning`
  - `Comms: Matrix Synapse`
- Milestone-by-milestone timeline for each task
- Optional TRACE rooms for raw logs:
  - `~/.openclaw/logs/commands.log`
  - `~/.openclaw/logs/gateway.log`
  - `~/.openclaw/logs/gateway.err.log`

## Controls

- `mouse click` select room
- `j / k` next / previous room
- `p` pin/unpin selected task
- `a` alert mode (show critical only)
- `r` reload
- `q` quit

## Data sources

- Session transcripts: `~/.openclaw/agents/main/sessions/*.jsonl`
- Gateway logs: `~/.openclaw/logs/*`
