"""Dashboard/Desktop backend — mounted at /api/plugins/lib-docs/."""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi import APIRouter, Request

_ROOT = Path(__file__).resolve().parent.parent
_root_str = str(_ROOT)
if _root_str in sys.path:
    sys.path.remove(_root_str)
sys.path.insert(0, _root_str)

import docs_fetch  # noqa: E402
import docs_store  # noqa: E402

router = APIRouter()


def _payload(request_json: object) -> dict:
    if isinstance(request_json, dict):
        return request_json
    return {}


@router.get("/recent")
async def recent() -> dict:
    items = docs_store.list_recent()
    return {"ok": True, "count": len(items), "items": items}


@router.post("/clear")
async def clear() -> dict:
    docs_store.clear_recent()
    return {"ok": True, "count": 0, "items": []}


@router.post("/resolve")
async def resolve(request: Request) -> dict:
    try:
        body = _payload(await request.json())
    except Exception:
        body = {}
    query = str(body.get("query") or "").strip()
    if not query:
        return {"ok": False, "error": "query is required", "items": []}
    ecosystem = str(body.get("ecosystem") or "auto")
    try:
        limit = int(body.get("limit") or 8)
    except (TypeError, ValueError):
        limit = 8
    try:
        hits = docs_fetch.resolve(query, ecosystem=ecosystem, limit=limit)
        return {"ok": True, "count": len(hits), "query": query, "items": hits}
    except Exception as exc:
        return {"ok": False, "error": str(exc), "items": []}


@router.post("/get")
async def get_docs(request: Request) -> dict:
    try:
        body = _payload(await request.json())
    except Exception:
        body = {}
    package = str(body.get("package") or "").strip()
    if not package:
        return {"ok": False, "error": "package is required"}
    ecosystem = str(body.get("ecosystem") or "auto")
    version = body.get("version")
    version_s = str(version).strip() if version else None
    doc = docs_fetch.get_docs(package, ecosystem=ecosystem, version=version_s or None)
    if doc.get("ok"):
        docs_store.record_lookup(doc)
    return doc
