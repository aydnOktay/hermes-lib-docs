"""lib-docs — current library docs from public npm / PyPI (no API keys)."""

from __future__ import annotations

import sys
from pathlib import Path

_DIR = str(Path(__file__).resolve().parent)
if _DIR in sys.path:
    sys.path.remove(_DIR)
sys.path.insert(0, _DIR)

import docs_context
import docs_schemas
import docs_tools


def _handle_slash(ctx, raw_args: str) -> str:
    parts = (raw_args or "").strip().split()
    if not parts or parts[0].lower() in {"recent", "list", "show"}:
        return ctx.dispatch_tool("lib_docs_recent", {"markdown": True})
    if parts[0].lower() in {"help", "?"}:
        return (
            "Usage:\n"
            "  /docs                 — recent lookups\n"
            "  /docs <package>       — fetch docs (auto npm/pypi)\n"
            "  /docs npm <package>   — force npm\n"
            "  /docs pypi <package>  — force PyPI"
        )
    ecosystem = "auto"
    name = parts[0]
    if parts[0].lower() in {"npm", "pypi", "auto"} and len(parts) >= 2:
        ecosystem = parts[0].lower()
        name = parts[1]
    return ctx.dispatch_tool(
        "lib_docs_get",
        {"package": name, "ecosystem": ecosystem, "markdown": True},
    )


def register(ctx) -> None:
    docs_context.set_ctx(ctx)

    ctx.register_tool(
        name="lib_docs_resolve",
        toolset="lib_docs",
        schema=docs_schemas.LIB_DOCS_RESOLVE,
        handler=docs_tools.lib_docs_resolve,
    )
    ctx.register_tool(
        name="lib_docs_get",
        toolset="lib_docs",
        schema=docs_schemas.LIB_DOCS_GET,
        handler=docs_tools.lib_docs_get,
    )
    ctx.register_tool(
        name="lib_docs_recent",
        toolset="lib_docs",
        schema=docs_schemas.LIB_DOCS_RECENT,
        handler=docs_tools.lib_docs_recent,
    )
    try:
        ctx.register_command(
            "docs",
            handler=lambda raw: _handle_slash(ctx, raw),
            description="Library docs from npm / PyPI (no API key)",
            args_hint="[npm|pypi] <package>|recent",
        )
    except TypeError:
        ctx.register_command(
            "docs",
            handler=lambda raw: _handle_slash(ctx, raw),
            description="Library docs from npm / PyPI (no API key)",
        )

    skill_md = Path(__file__).parent / "skills" / "lib-docs" / "SKILL.md"
    if skill_md.is_file():
        try:
            ctx.register_skill("lib-docs", skill_md)
        except TypeError:
            ctx.register_skill("lib-docs", str(skill_md))
