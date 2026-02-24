#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Set

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Footer, Header, ListItem, ListView, RichLog, Static

BASE = Path.home() / ".openclaw"
SESSIONS_DIR = BASE / "agents" / "main" / "sessions"
LOGS_DIR = BASE / "logs"
MAX_LINES = 800
MAX_TASKS = 60
SLA_WARN_MIN = 10
SLA_ALERT_MIN = 30
PINS_FILE = BASE / "workspace" / "tools" / "warroom-cli" / "pins.json"


@dataclass
class Task:
    id: str
    title: str
    status: str = "RUNNING"  # RUNNING|DONE|BLOCKED
    session_name: str = ""
    request: str = ""
    milestones: List[str] = field(default_factory=list)
    started_at: str = ""
    updated_at: str = ""
    source_path: str = ""
    start_line: int = 0


@dataclass
class Room:
    key: str
    label: str
    kind: str  # center|task|coding|trace
    path: Optional[Path] = None
    task: Optional[Task] = None


def now_ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


def truncate(s: str, n: int = 140) -> str:
    s = " ".join(s.split())
    return s if len(s) <= n else s[: n - 1] + "…"


def parse_iso(ts: str) -> Optional[datetime]:
    if not ts:
        return None
    try:
        # Session timestamps are usually RFC3339 with Z
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None


def elapsed_minutes(task: Task) -> Optional[int]:
    base = parse_iso(task.started_at or task.updated_at)
    if base is None:
        return None
    now = datetime.now(timezone.utc)
    delta = now - base.astimezone(timezone.utc)
    return max(0, int(delta.total_seconds() // 60))


def sla_state(task: Task) -> str:
    if task.status != "RUNNING":
        return "ok"
    mins = elapsed_minutes(task)
    if mins is None:
        return "ok"
    if mins >= SLA_ALERT_MIN:
        return "alert"
    if mins >= SLA_WARN_MIN:
        return "warn"
    return "ok"


def load_pins() -> Set[str]:
    try:
        if not PINS_FILE.exists():
            return set()
        data = json.loads(PINS_FILE.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return {str(x) for x in data}
    except Exception:
        pass
    return set()


def save_pins(pins: Set[str]) -> None:
    try:
        PINS_FILE.parent.mkdir(parents=True, exist_ok=True)
        PINS_FILE.write_text(json.dumps(sorted(list(pins)), indent=2), encoding="utf-8")
    except Exception:
        pass


def orb(task: Task) -> str:
    if task.status == "DONE":
        return "🟢"
    if task.status == "BLOCKED":
        return "🔴"
    frames = ["◐", "◓", "◑", "◒"]
    return frames[int(datetime.now().timestamp()) % len(frames)]


def title_from_user_text(text: str, index: int) -> str:
    t = " ".join(text.strip().split())
    tl = t.lower()

    # Slash command-first naming (most precise)
    m = re.search(r"(?:^|\s)/train\s+([^\n]+)", t, flags=re.IGNORECASE)
    if m:
        return f"AETHER: Train {truncate(m.group(1), 36)}"

    m = re.search(r"(?:^|\s)/curate\s+([^\n]+)", t, flags=re.IGNORECASE)
    if m:
        topic = m.group(1).split("--max-pages")[0].strip()
        return f"AETHER: Curate {truncate(topic, 36)}"

    m = re.search(r"(?:^|\s)/query\s+([^\n]+)", t, flags=re.IGNORECASE)
    if m:
        return f"AETHER: Query {truncate(m.group(1), 36)}"

    m = re.search(r"(?:^|\s)/recall\s+([^\n]+)", t, flags=re.IGNORECASE)
    if m:
        return f"AETHER: Recall {truncate(m.group(1), 36)}"

    m = re.search(r"(?:^|\s)/eye\s+render\s+([^\n]+)", t, flags=re.IGNORECASE)
    if m:
        return f"AETHER: Eye Render {truncate(m.group(1), 26)}"

    # Intent-based naming
    if any(k in tl for k in ["tweet", "x post", "twitter", "virality", "reply on x", "like/repost"]):
        return "X: Publish / Engage"
    if any(k in tl for k in ["aws", "infrastructure", "ec2", "eks", "fargate", "cost draft"]):
        return "Infra: AWS Planning"
    if any(k in tl for k in ["discord", "server for us", "discord server"]):
        return "Comms: Discord Server"
    if any(k in tl for k in ["matrix", "synapse", "e2ee"]):
        return "Comms: Matrix Synapse"
    if any(k in tl for k in ["panic", "traceback", "error", "failed", "please fix", "doesnt work", "doesn't work"]):
        return "AETHER: Bug Fix"
    if any(k in tl for k in ["warroom", "cli app", "rooms", "task board", "logs"]):
        return "WarRoom: UI/UX Upgrade"

    # fallback = compact first words
    words = [w for w in re.split(r"\s+", t) if w]
    if words:
        return f"Task: {truncate(' '.join(words[:6]), 42)}"

    return f"Task #{index}"


def done_like(text: str) -> bool:
    t = text.lower()
    return any(
        w in t
        for w in [
            "done",
            "complete",
            "completed",
            "fixed",
            "resolved",
            "shipped",
            "implemented",
            "created",
            "committed",
            "all tests pass",
        ]
    )


def blocked_like(text: str) -> bool:
    t = text.lower()
    return any(w in t for w in ["failed", "panic", "error", "traceback", "blocked"])


def running_like(text: str) -> bool:
    t = text.lower()
    return any(w in t for w in ["still running", "running", "working on", "let me check", "in progress"])


def extract_primary_text(msg: dict) -> str:
    content = msg.get("content", [])
    if not isinstance(content, list):
        return ""
    parts: List[str] = []
    for item in content:
        if item.get("type") == "text":
            txt = item.get("text", "")
            if isinstance(txt, str) and txt.strip():
                parts.append(txt.strip())
    return "\n".join(parts)


def load_tasks_from_session(path: Path) -> List[Task]:
    tasks: List[Task] = []
    current: Optional[Task] = None

    try:
        with path.open("r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except Exception:
        return tasks

    task_index = 0
    session_name = path.stem[:8]

    for line_no, raw in enumerate(lines, start=1):
        raw = raw.strip()
        if not raw:
            continue
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            continue

        if obj.get("type") != "message":
            continue

        msg = obj.get("message", {})
        role = msg.get("role")
        ts = obj.get("timestamp", "")

        # New task starts on user messages.
        if role == "user":
            user_text = extract_primary_text(msg)
            if not user_text:
                continue
            task_index += 1
            current = Task(
                id=f"{path.stem}:{task_index}",
                title=title_from_user_text(user_text, task_index),
                status="RUNNING",
                session_name=session_name,
                request=truncate(user_text, 200),
                milestones=[f"🟡 Request received: {truncate(user_text, 120)}"],
                started_at=str(ts),
                updated_at=str(ts),
                source_path=str(path),
                start_line=line_no,
            )
            tasks.append(current)
            continue

        if current is None:
            continue

        content = msg.get("content", [])
        if not isinstance(content, list):
            continue

        for item in content:
            it = item.get("type")
            if it == "toolCall":
                name = item.get("name", "tool")
                current.milestones.append(f"🛠 Running: {name}")
                current.status = "RUNNING"
                current.updated_at = str(ts)
            elif it == "text":
                txt = str(item.get("text", "")).strip()
                if not txt:
                    continue
                if done_like(txt):
                    current.status = "DONE"
                    current.milestones.append(f"✅ {truncate(txt, 130)}")
                elif blocked_like(txt):
                    current.status = "BLOCKED"
                    current.milestones.append(f"❌ {truncate(txt, 130)}")
                elif running_like(txt):
                    current.status = "RUNNING"
                    current.milestones.append(f"🔄 {truncate(txt, 130)}")
                else:
                    # Keep only meaningful assistant updates to avoid noise
                    if any(k in txt.lower() for k in ["now", "next", "ready", "status", "plan", "summary"]):
                        current.milestones.append(f"ℹ️ {truncate(txt, 130)}")
                current.updated_at = str(ts)

        # Tool result entries come as role=toolResult in this transcript format
        if role == "toolResult":
            text = extract_primary_text(msg)
            if text:
                if "Process still running" in text or "Command still running" in text:
                    current.status = "RUNNING"
                    current.milestones.append("🔄 Command in progress")
                elif "exited with code 0" in text or "completed" in text.lower():
                    if current.status != "BLOCKED":
                        current.status = "DONE"
                    current.milestones.append("✅ Step completed")
                elif "error" in text.lower() or "failed" in text.lower():
                    current.status = "BLOCKED"
                    current.milestones.append(f"❌ {truncate(text, 120)}")
                current.updated_at = str(ts)

    # Cleanup milestone noise
    for t in tasks:
        compact: List[str] = []
        seen = set()
        for m in t.milestones:
            key = m[:80]
            if key in seen:
                continue
            seen.add(key)
            compact.append(m)
        t.milestones = compact[-30:]

    return tasks


def parse_plain_tail(path: Path, limit: int = MAX_LINES) -> List[str]:
    try:
        with path.open("r", encoding="utf-8", errors="replace") as f:
            return [ln.rstrip("\n") for ln in f.readlines()[-limit:]]
    except Exception as e:
        return [f"[{now_ts()}] [read-error] {e}"]


def build_rooms(pins: Optional[Set[str]] = None, alert_mode: bool = False) -> List[Room]:
    pins = pins or set()
    rooms: List[Room] = [Room(key="center", label="🎯 CENTER", kind="center")]

    all_tasks: List[Task] = []
    if SESSIONS_DIR.exists():
        session_files = sorted(
            [
                p
                for p in SESSIONS_DIR.iterdir()
                if p.suffix == ".jsonl"
                and ".deleted." not in p.name
                and not p.name.endswith(".lock")
            ],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        for p in session_files:
            all_tasks.extend(load_tasks_from_session(p))

    # Show pinned first, then recency
    all_tasks = sorted(all_tasks, key=lambda t: t.updated_at, reverse=True)
    all_tasks = sorted(all_tasks, key=lambda t: 0 if t.id in pins else 1)[:MAX_TASKS]

    if alert_mode:
        all_tasks = [t for t in all_tasks if t.status == "BLOCKED" or sla_state(t) == "alert"]

    for t in all_tasks:
        sla = sla_state(t)
        if t.status == "BLOCKED":
            icon = "🔴"
        elif t.status == "DONE":
            icon = "🟢"
        elif sla == "alert":
            icon = "🚨"
        elif sla == "warn":
            icon = "🟠"
        else:
            icon = "🟡"

        pin = "📌 " if t.id in pins else ""
        rooms.append(
            Room(
                key=f"task:{t.id}",
                label=f"{pin}{icon} {t.title}",
                kind="task",
                task=t,
            )
        )
        rooms.append(
            Room(
                key=f"coding:{t.id}",
                label=f"   ↳ {orb(t)} CODING",
                kind="coding",
                task=t,
            )
        )

    # Keep raw logs as trace rooms
    for log_name in ["commands.log", "gateway.log", "gateway.err.log"]:
        lp = LOGS_DIR / log_name
        if lp.exists():
            rooms.append(Room(key=f"trace:{log_name}", label=f"📟 TRACE {log_name}", kind="trace", path=lp))

    return rooms


class RoomItem(ListItem):
    def __init__(self, room: Room) -> None:
        super().__init__(Static(room.label))
        self.room = room


class WarRoomApp(App):
    CSS = """
    Screen {
      background: #05070a;
      color: #a8ffcf;
    }

    #left {
      width: 38;
      border: round #00ff99;
      padding: 0 1;
    }

    #right {
      border: round #00d4ff;
      padding: 0 1;
    }

    #title {
      content-align: center middle;
      color: #00ff99;
      height: 3;
      text-style: bold;
    }

    #status {
      color: #ffd166;
      height: 1;
    }

    RichLog {
      background: #000000;
      color: #eafff3;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "reload_rooms", "Reload"),
        ("j", "down", "Next"),
        ("k", "up", "Prev"),
        ("p", "toggle_pin", "Pin"),
        ("a", "toggle_alert_mode", "Alert"),
    ]

    selected_idx = reactive(0)

    def __init__(self) -> None:
        super().__init__()
        self.rooms: List[Room] = []
        self.pins: Set[str] = load_pins()
        self.alert_mode: bool = False
        self.last_render_snapshot: str = ""

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("⚡ CLAWDY WAR ROOM // TASK COMMAND CENTER ⚡", id="title")
        with Horizontal():
            with Vertical(id="left"):
                yield Static("ROOMS", classes="label")
                yield ListView(id="rooms")
            with Vertical(id="right"):
                yield Static("TASK VIEW", classes="label")
                yield RichLog(id="log", auto_scroll=True, highlight=True, markup=False)
        yield Static("[r] reload  [j/k] move  [p] pin  [a] alert mode  [mouse] click room  [q] quit", id="status")
        yield Footer()

    def on_mount(self) -> None:
        # Refresh detail pane frequently, but avoid constant list rebuild flicker.
        self.set_interval(2.0, self.refresh_tick)
        self.action_reload_rooms()

    def action_reload_rooms(self) -> None:
        prev_key = self.rooms[self.selected_idx].key if self.rooms else "center"
        self.rooms = build_rooms(self.pins, self.alert_mode)
        self.rebuild_room_list(prev_key=prev_key)
        self.load_selected_room()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if isinstance(event.item, RoomItem):
            self.selected_idx = self.rooms.index(event.item.room)
            self.load_selected_room()

    def action_down(self) -> None:
        if not self.rooms:
            return
        self.selected_idx = min(self.selected_idx + 1, len(self.rooms) - 1)
        self.query_one("#rooms", ListView).index = self.selected_idx
        self.load_selected_room()

    def action_up(self) -> None:
        if not self.rooms:
            return
        self.selected_idx = max(self.selected_idx - 1, 0)
        self.query_one("#rooms", ListView).index = self.selected_idx
        self.load_selected_room()

    def rebuild_room_list(self, prev_key: str = "center") -> None:
        # Keep same selected room when possible
        idx = 0
        for i, r in enumerate(self.rooms):
            if r.key == prev_key:
                idx = i
                break
        self.selected_idx = idx

        lv = self.query_one("#rooms", ListView)
        lv.clear()
        for room in self.rooms:
            lv.append(RoomItem(room))
        lv.index = self.selected_idx

    def refresh_tick(self) -> None:
        prev_key = self.rooms[self.selected_idx].key if self.rooms else "center"
        new_rooms = build_rooms(self.pins, self.alert_mode)

        old_sig = [(r.key, r.label) for r in self.rooms]
        new_sig = [(r.key, r.label) for r in new_rooms]

        self.rooms = new_rooms

        # Rebuild left pane only when room list actually changed (prevents flicker).
        if old_sig != new_sig:
            self.rebuild_room_list(prev_key=prev_key)
        else:
            # keep selection index synchronized
            for i, r in enumerate(self.rooms):
                if r.key == prev_key:
                    self.selected_idx = i
                    self.query_one("#rooms", ListView).index = i
                    break

        self.load_selected_room(refresh_only=True)

    def action_toggle_alert_mode(self) -> None:
        self.alert_mode = not self.alert_mode
        self.action_reload_rooms()

    def action_toggle_pin(self) -> None:
        if not self.rooms:
            return
        room = self.rooms[self.selected_idx]
        if room.kind not in {"task", "coding"} or not room.task:
            return
        task_id = room.task.id
        if task_id in self.pins:
            self.pins.remove(task_id)
        else:
            self.pins.add(task_id)
        save_pins(self.pins)
        self.action_reload_rooms()

    def load_selected_room(self, refresh_only: bool = False) -> None:
        if not self.rooms:
            return

        room = self.rooms[self.selected_idx]
        lines: List[str]
        if room.kind == "center":
            lines = self.render_center()
        elif room.kind == "task" and room.task:
            lines = self.render_task(room.task)
        elif room.kind == "coding" and room.task:
            lines = self.render_coding(room.task)
        elif room.kind == "trace" and room.path:
            lines = self.render_trace(room)
        else:
            lines = ["No data"]

        snapshot = "\n".join(lines)
        if snapshot != self.last_render_snapshot:
            log = self.query_one("#log", RichLog)
            log.clear()
            for ln in lines:
                log.write(ln)
            self.last_render_snapshot = snapshot

        if not refresh_only:
            self.title = f"WAR ROOM — {room.label}"

    def render_center(self) -> List[str]:
        lines: List[str] = []
        tasks = [r.task for r in self.rooms if r.kind == "task" and r.task]

        running = [t for t in tasks if t.status == "RUNNING"]
        blocked = [t for t in tasks if t.status == "BLOCKED"]
        done = [t for t in tasks if t.status == "DONE"]
        alerts = [t for t in tasks if sla_state(t) == "alert"]

        mode = "ALERT MODE" if self.alert_mode else "NORMAL MODE"
        lines.append(f"CENTER // Task Command View ({mode})")
        lines.append("=" * 80)
        lines.append(
            f"Running: {len(running)}   Blocked: {len(blocked)}   SLA Alerts: {len(alerts)}   Done: {len(done)}   Total: {len(tasks)}"
        )
        lines.append("")

        if not tasks:
            lines.append("No tasks found yet. Send a request and it will appear here.")
            return lines

        lines.append("Latest tasks:")
        for t in tasks[:20]:
            sla = sla_state(t)
            if t.status == "BLOCKED":
                icon = "🔴"
            elif t.status == "DONE":
                icon = "🟢"
            elif sla == "alert":
                icon = "🚨"
            elif sla == "warn":
                icon = "🟠"
            else:
                icon = "🟡"

            pin = "📌 " if t.id in self.pins else ""
            age = elapsed_minutes(t)
            age_str = f"{age}m" if age is not None else "n/a"
            lines.append(f"{pin}{icon} {t.title:<20}  [{t.status:<7}]  age={age_str:<5}  {t.request}")

        lines.append("")
        lines.append("Tip: click task rooms for milestone progress. [p]=pin  [a]=alert mode")
        return lines

    def render_task(self, task: Task) -> List[str]:
        lines: List[str] = []
        sla = sla_state(task)
        if task.status == "BLOCKED":
            icon = "🔴"
        elif task.status == "DONE":
            icon = "🟢"
        elif sla == "alert":
            icon = "🚨"
        elif sla == "warn":
            icon = "🟠"
        else:
            icon = "🟡"

        lines.append(f"{icon} TASK: {task.title}")
        lines.append("=" * 80)
        lines.append(f"Status: {task.status}")
        lines.append(f"Pinned: {'yes' if task.id in self.pins else 'no'}")
        lines.append(f"Session: {task.session_name}")
        lines.append(f"Request: {task.request}")
        age = elapsed_minutes(task)
        if age is not None:
            lines.append(f"SLA timer: {age}m (warn>{SLA_WARN_MIN}m, alert>{SLA_ALERT_MIN}m)")
        lines.append("")
        lines.append(f"Live coding room: coding:{task.id}")
        lines.append("Milestones:")

        if not task.milestones:
            lines.append("  (no milestones yet)")
            return lines

        for i, m in enumerate(task.milestones, start=1):
            lines.append(f"  {i:02d}. {m}")
        return lines

    def render_coding(self, task: Task) -> List[str]:
        lines: List[str] = []
        o = orb(task)
        lines.append(f"{o} CODING // {task.title}")
        lines.append("=" * 80)
        lines.append(f"Status: {task.status}   Session: {task.session_name}   Start line: {task.start_line}")
        lines.append("Live stream:")

        if not task.source_path:
            lines.append("No source transcript available for this task.")
            return lines

        p = Path(task.source_path)
        if not p.exists():
            lines.append(f"Transcript missing: {p}")
            return lines

        try:
            raw_lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception as e:
            lines.append(f"Read error: {e}")
            return lines

        feed: List[str] = []
        start = max(0, task.start_line - 1)
        for raw in raw_lines[start:]:
            try:
                obj = json.loads(raw)
            except Exception:
                continue
            if obj.get("type") != "message":
                continue

            msg = obj.get("message", {})
            role = msg.get("role", "?")
            ts = obj.get("timestamp", "")
            content = msg.get("content", [])
            if not isinstance(content, list):
                continue

            for item in content:
                it = item.get("type")
                if it == "toolCall":
                    name = item.get("name", "tool")
                    feed.append(f"[{ts}] {role}: 🛠 {name}")
                elif it == "text":
                    txt = str(item.get("text", "")).strip()
                    if txt:
                        feed.append(f"[{ts}] {role}: {truncate(txt, 220)}")
                elif it == "thinking":
                    thinking = str(item.get("thinking", "")).strip()
                    if thinking:
                        feed.append(f"[{ts}] {role}: 💭 {truncate(thinking, 180)}")

        if not feed:
            lines.append("  (waiting for coding events)")
            return lines

        lines.extend(feed[-120:])
        return lines

    def render_trace(self, room: Room) -> List[str]:
        lines = [f"TRACE ROOM: {room.label}", "=" * 80]
        lines.extend(parse_plain_tail(room.path))
        return lines


if __name__ == "__main__":
    WarRoomApp().run()
