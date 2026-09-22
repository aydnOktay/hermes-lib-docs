"""Recent lookups under plugin-data."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PLUGIN_ID = "lib-docs"
MAX_RECENT = 20


def data_dir() -> Path:
    try:
        from plugins.plugin_storage import plugin_data_dir  # type: ignore

        return plugin_data_dir(PLUGIN_ID)
    except Exception:
        home = Path(os.environ.get("HERMES_HOME") or (Path.home() / ".hermes"))
        path = home / "plugin-data" / PLUGIN_ID
        path.mkdir(parents=True, exist_ok=True)
        return path


def state_path() -> Path:
    return data_dir() / "recent.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_state() -> dict[str, Any]:
    path = state_path()
    if not path.is_file():
        return {"items": []}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"items": []}
    if not isinstance(raw, dict):
        return {"items": []}
    items = raw.get("items")
    if not isinstance(items, list):
        raw["items"] = []
    return raw


def save_state(state: dict[str, Any]) -> None:
    path = state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def list_recent() -> list[dict[str, Any]]:
    state = load_state()
    items = state.get("items")
    if not isinstance(items, list):
        return []
    return [it for it in items if isinstance(it, dict) and it.get("package")]


def record_lookup(doc: dict[str, Any]) -> list[dict[str, Any]]:
    if not doc.get("ok"):
        return list_recent()
    entry = {
        "ecosystem": str(doc.get("ecosystem") or "")[:16],
        "package": str(doc.get("package") or "")[:214],
        "version": str(doc.get("version") or "")[:64],
        "description": str(doc.get("description") or "")[:200],
        "homepage": str(doc.get("homepage") or "")[:300],
        "ts": now_iso(),
    }
    state = load_state()
    items: list[dict[str, Any]] = [
        it for it in state.get("items", []) if isinstance(it, dict) and it.get("package")
    ]
    key = f"{entry['ecosystem']}:{entry['package']}".lower()
    items = [
        it
        for it in items
        if f"{it.get('ecosystem')}:{it.get('package')}".lower() != key
    ]
    items.append(entry)
    if len(items) > MAX_RECENT:
        items = items[-MAX_RECENT:]
    state["items"] = items
    save_state(state)
    return items


def clear_recent() -> None:
    save_state({"items": []})


def to_markdown_recent(items: list[dict[str, Any]] | None = None) -> str:
    rows = items if items is not None else list_recent()
    if not rows:
        return "(lib-docs recent is empty)"
    lines = []
    for i, it in enumerate(reversed(rows), 1):
        lines.append(
            f"{i}. `{it.get('package')}` ({it.get('ecosystem')}@{it.get('version') or '?'})"
        )
    return "\n".join(lines)


def to_markdown_doc(doc: dict[str, Any]) -> str:
    if not doc.get("ok"):
        return f"(error: {doc.get('error') or 'failed'})"
    lines = [
        f"# {doc.get('package')} `{doc.get('version')}` ({doc.get('ecosystem')})",
    ]
    if doc.get("description"):
        lines.append("")
        lines.append(str(doc["description"]))
    if doc.get("homepage"):
        lines.append("")
        lines.append(f"Homepage: {doc['homepage']}")
    readme = doc.get("readme") or ""
    if readme:
        lines.append("")
        lines.append("## README")
        lines.append("")
        lines.append(readme)
    return "\n".join(lines)
