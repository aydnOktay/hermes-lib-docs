"""Tool handlers — always return JSON strings, never raise."""

from __future__ import annotations

import json

import docs_fetch
import docs_store


def lib_docs_resolve(args: dict, **kwargs) -> str:
    del kwargs
    try:
        payload = args if isinstance(args, dict) else {}
        query = str(payload.get("query") or "").strip()
        if not query:
            return json.dumps({"ok": False, "error": "query is required"})
        ecosystem = str(payload.get("ecosystem") or "auto")
        limit = payload.get("limit", 8)
        try:
            limit_i = int(limit)
        except (TypeError, ValueError):
            limit_i = 8
        hits = docs_fetch.resolve(query, ecosystem=ecosystem, limit=limit_i)
        return json.dumps(
            {"ok": True, "count": len(hits), "query": query, "items": hits},
            ensure_ascii=False,
        )
    except Exception as exc:
        return json.dumps({"ok": False, "error": str(exc)})


def lib_docs_get(args: dict, **kwargs) -> str:
    del kwargs
    try:
        payload = args if isinstance(args, dict) else {}
        package = str(payload.get("package") or "").strip()
        if not package:
            return json.dumps({"ok": False, "error": "package is required"})
        ecosystem = str(payload.get("ecosystem") or "auto")
        version = payload.get("version")
        version_s = str(version).strip() if version else None
        doc = docs_fetch.get_docs(package, ecosystem=ecosystem, version=version_s or None)
        if doc.get("ok"):
            docs_store.record_lookup(doc)
        out = dict(doc)
        markdown = True
        if payload.get("markdown") is False:
            markdown = False
        if markdown:
            out["markdown"] = docs_store.to_markdown_doc(doc)
        return json.dumps(out, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": str(exc)})


def lib_docs_recent(args: dict, **kwargs) -> str:
    del kwargs
    try:
        payload = args if isinstance(args, dict) else {}
        items = docs_store.list_recent()
        out: dict = {"ok": True, "count": len(items), "items": items}
        markdown = True
        if payload.get("markdown") is False:
            markdown = False
        if markdown:
            out["markdown"] = docs_store.to_markdown_recent(items)
        return json.dumps(out, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": str(exc)})
