#!/usr/bin/env python3
"""Append each user prompt and the final assistant response to .agent-logs/.

Cursor runs this on its own:
  beforeSubmitPrompt  -> prompt, verbatim
  afterAgentResponse  -> latest assistant text (overwrites earlier bubbles)
  stop                -> write that latest text as the response for the turn

Thinking (afterAgentThought) and tool calls are not hooked.
"""

from __future__ import annotations

import fcntl
import json
import os
import re
import sys
import traceback
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

AUTHOR = "Sona-28"
TOOL = "cursor"
PROJECT = "amazon-clone"
PROMPT_ENTRY_RE = re.compile(r"^\[LOG_ENTRY type=PROMPT num=\d+ session=", re.M)


def utc_now() -> str:
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"


def model_name(data: dict) -> str:
    model_id = str(data.get("model_id") or "").strip()
    model = str(data.get("model") or "").strip()
    if model_id and model and model_id != model:
        return f"{model_id} ({model})"
    return model_id or model or "unknown"


def short_id(conversation_id: str) -> str:
    head = conversation_id.split("-", 1)[0]
    return head or conversation_id[:8] or "session"


def workspace_root(data: dict) -> Path:
    roots = data.get("workspace_roots") or []
    if roots:
        return Path(roots[0])
    return Path.cwd()


def emit(event: str) -> None:
    if event == "beforeSubmitPrompt":
        sys.stdout.write(json.dumps({"continue": True}) + "\n")
    else:
        sys.stdout.write("{}\n")


def log_error(root: Path, message: str) -> None:
    try:
        state_dir = root / ".cursor" / "hooks" / ".state"
        state_dir.mkdir(parents=True, exist_ok=True)
        with (state_dir / "capture-errors.log").open("a", encoding="utf-8") as handle:
            handle.write(f"{utc_now()} {message}\n")
    except Exception:
        pass


def state_path(root: Path, conversation_id: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", conversation_id)
    return root / ".cursor" / "hooks" / ".state" / f"{safe}.json"


def load_state(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def find_log(root: Path, conversation_id: str) -> Path | None:
    logs = root / ".agent-logs"
    if not logs.exists():
        return None
    matches = sorted(logs.glob(f"*_{conversation_id}.md"))
    return matches[-1] if matches else None


def new_log_path(root: Path, conversation_id: str, started: str) -> Path:
    stamp = started[:19].replace(":", "-").replace("T", "_")
    return root / ".agent-logs" / f"{stamp}_{conversation_id}.md"


def initial_log(conversation_id: str, started: str, model: str) -> str:
    day = started[:10]
    short = short_id(conversation_id)
    return (
        "---\n"
        f"session_id: {conversation_id}\n"
        f"date: {day}\n"
        f"author: {AUTHOR}\n"
        f"model: {model}\n"
        f"tool: {TOOL}\n"
        f"project: {PROJECT}\n"
        "total_exchanges: 0\n"
        f"first_prompt_time: {started}\n"
        f"last_prompt_time: {started}\n"
        "---\n"
        "\n"
        f"# Session Log - {day}\n"
        "\n"
        f"Session: `{short}` | Project: `{PROJECT}` | Author: `{AUTHOR}`\n"
        "\n"
        "---\n"
    )


def update_frontmatter(text: str, updates: dict[str, str]) -> str:
    if not text.startswith("---\n"):
        return text
    end = text.find("\n---\n", 4)
    if end < 0:
        return text
    front = text[4:end]
    rest = text[end + 5 :]
    lines = front.split("\n")
    seen = set()
    for index, line in enumerate(lines):
        key = line.split(":", 1)[0]
        if key in updates:
            lines[index] = f"{key}: {updates[key]}"
            seen.add(key)
    for key, value in updates.items():
        if key not in seen:
            lines.append(f"{key}: {value}")
    return "---\n" + "\n".join(lines) + "\n---\n" + rest


def prompt_count(text: str) -> int:
    return len(PROMPT_ENTRY_RE.findall(text))


def format_entry(kind: str, num: int, conversation_id: str, timestamp: str, model: str, body: str) -> str:
    if body is None:
        body = ""
    if not body.endswith("\n"):
        body += "\n"
    return (
        f"[LOG_ENTRY type={kind} num={num} session={short_id(conversation_id)}]\n"
        f"timestamp: {timestamp}\n"
        f"model: {model}\n"
        "\n"
        f"{body}\n"
    )


def ensure_log(root: Path, state: dict, conversation_id: str, model: str, started: str) -> Path:
    existing = state.get("log_path")
    if existing:
        path = Path(existing)
        if path.exists():
            return path
    found = find_log(root, conversation_id)
    if found:
        state["log_path"] = str(found)
        return found
    path = new_log_path(root, conversation_id, started)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(initial_log(conversation_id, started, model), encoding="utf-8")
    state["log_path"] = str(path)
    return path


def upsert_response(root: Path, state: dict, conversation_id: str) -> None:
    """Write the latest assistant text once. Later bubbles replace that entry."""
    pending = state.get("pending") or {}
    text = pending.get("text")
    num = pending.get("num")
    if text is None or not num:
        return
    model = pending.get("model") or "unknown"
    timestamp = pending.get("timestamp") or utc_now()
    path = ensure_log(root, state, conversation_id, model, timestamp)
    entry = format_entry("RESPONSE", int(num), conversation_id, timestamp, model, text)
    current = path.read_text(encoding="utf-8")
    start = pending.get("response_start")
    if isinstance(start, int) and 0 <= start <= len(current):
        path.write_text(current[:start] + entry, encoding="utf-8")
    else:
        prefix = current.rstrip("\n") + "\n\n"
        pending["response_start"] = len(prefix)
        path.write_text(prefix + entry, encoding="utf-8")
    state["pending"] = pending


def handle_prompt(root: Path, data: dict, conversation_id: str) -> None:
    path = state_path(root, conversation_id)
    state = load_state(path)
    upsert_response(root, state, conversation_id)

    started = utc_now()
    model = model_name(data)
    prompt = data.get("prompt")
    if prompt is None:
        prompt = ""
    prompt = str(prompt)

    log_path = ensure_log(root, state, conversation_id, model, started)
    current = log_path.read_text(encoding="utf-8")
    num = prompt_count(current) + 1
    updated = update_frontmatter(
        current,
        {
            "total_exchanges": str(num),
            "last_prompt_time": started,
        },
    )
    entry = format_entry("PROMPT", num, conversation_id, started, model, prompt)
    log_path.write_text(updated.rstrip("\n") + "\n\n" + entry, encoding="utf-8")

    state["conversation_id"] = conversation_id
    state["pending"] = {
        "generation_id": data.get("generation_id"),
        "num": num,
        "model": model,
        "text": None,
        "timestamp": None,
        "response_start": None,
    }
    save_state(path, state)


def handle_response(root: Path, data: dict, conversation_id: str) -> None:
    text = data.get("text")
    if text is None:
        return
    path = state_path(root, conversation_id)
    state = load_state(path)
    pending = state.get("pending") or {}
    if not pending.get("num"):
        return
    pending["text"] = str(text)
    pending["model"] = model_name(data)
    pending["timestamp"] = utc_now()
    pending["generation_id"] = data.get("generation_id") or pending.get("generation_id")
    state["pending"] = pending
    state["conversation_id"] = conversation_id
    upsert_response(root, state, conversation_id)
    save_state(path, state)


def handle_stop(root: Path, data: dict, conversation_id: str) -> None:
    path = state_path(root, conversation_id)
    state = load_state(path)
    if not state:
        return
    upsert_response(root, state, conversation_id)
    save_state(path, state)


@contextmanager
def conversation_lock(root: Path, conversation_id: str):
    lock_path = state_path(root, conversation_id).with_suffix(".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    handle = lock_path.open("a", encoding="utf-8")
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()


def main() -> int:
    raw = sys.stdin.read()
    try:
        data = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        emit("")
        return 0

    event = str(data.get("hook_event_name") or "")
    root = workspace_root(data)
    conversation_id = str(data.get("conversation_id") or data.get("session_id") or "").strip()
    if not conversation_id:
        conversation_id = "unknown-session"

    try:
        with conversation_lock(root, conversation_id):
            if event == "beforeSubmitPrompt":
                handle_prompt(root, data, conversation_id)
            elif event == "afterAgentResponse":
                handle_response(root, data, conversation_id)
            elif event == "stop":
                handle_stop(root, data, conversation_id)
    except Exception:
        log_error(root, traceback.format_exc())

    emit(event)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.stdout.write("{}\n")
        sys.exit(0)
