"""Local checks that do not require Hermes or the network."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["HERMES_HOME"] = tempfile.mkdtemp(prefix="lib-docs-test-")

import docs_fetch
import docs_store
import docs_tools


def _fake_fetch(url: str) -> bytes:
    u = unquote(url)
    if "/-/v1/search" in u:
        return json.dumps(
            {
                "objects": [
                    {
                        "package": {
                            "name": "react",
                            "version": "19.0.0",
                            "description": "React library",
                            "links": {"homepage": "https://react.dev"},
                        }
                    }
                ]
            }
        ).encode()
    if "registry.npmjs.org/react" in u and "/-/" not in u:
        return json.dumps(
            {
                "name": "react",
                "description": "React",
                "dist-tags": {"latest": "19.0.0"},
                "versions": {
                    "19.0.0": {
                        "name": "react",
                        "version": "19.0.0",
                        "description": "React",
                        "readme": "# React\n\nHello hooks.",
                    }
                },
                "readme": "# React\n\nHello hooks.",
            }
        ).encode()
    if "pypi.org/pypi/react" in u:
        return json.dumps(
            {
                "info": {
                    "name": "react",
                    "version": "4.3.0",
                    "summary": "Server-side rendering of React components",
                    "description": "# python-react\n\nNot Facebook React.",
                    "home_page": "https://github.com/markfinger/python-react",
                    "license": "MIT",
                }
            }
        ).encode()
    if "pypi.org/pypi/fastapi" in u:
        return json.dumps(
            {
                "info": {
                    "name": "fastapi",
                    "version": "0.115.0",
                    "summary": "FastAPI framework",
                    "description": "# FastAPI\n\nGreat docs.",
                    "home_page": "https://fastapi.tiangolo.com",
                    "license": "MIT",
                }
            }
        ).encode()
    raise RuntimeError(f"unexpected url in test: {url}")


docs_fetch._FETCH_IMPL = _fake_fetch


def test_resolve_npm() -> None:
    hits = docs_fetch.resolve("react", ecosystem="npm", limit=5)
    assert hits and hits[0]["package"] == "react"
    assert hits[0]["ecosystem"] == "npm"


def test_get_npm() -> None:
    doc = docs_fetch.get_docs("react", ecosystem="npm")
    assert doc["ok"] is True
    assert doc["version"] == "19.0.0"
    assert "Hello hooks" in doc["readme"]
    docs_store.record_lookup(doc)
    recent = docs_store.list_recent()
    assert recent[-1]["package"] == "react"


def test_get_pypi() -> None:
    doc = docs_fetch.get_docs("fastapi", ecosystem="pypi")
    assert doc["ok"] is True
    assert doc["ecosystem"] == "pypi"
    assert "Great docs" in doc["readme"]


def test_auto_prefers_npm_on_collision() -> None:
    doc = docs_fetch.get_docs("react", ecosystem="auto")
    assert doc["ok"] is True
    assert doc["ecosystem"] == "npm"
    assert doc["version"] == "19.0.0"
    assert "also_on" in doc
    assert doc["also_on"]["ecosystem"] == "pypi"
    assert "warning" in doc
    assert "pypi" in doc["warning"].lower()
    md = docs_store.to_markdown_doc(doc)
    assert "Hello hooks" in md
    assert "Also on pypi" in md or "also exists" in md.lower()


def test_guess() -> None:
    assert docs_fetch.guess_ecosystem("@scope/pkg") == "npm"
    assert docs_fetch.guess_ecosystem("my_package") == "pypi"
    assert docs_fetch.guess_ecosystem("react") == "npm"


def test_tools_json() -> None:
    data = json.loads(docs_tools.lib_docs_resolve({"query": "react", "ecosystem": "npm"}, extra="x"))
    assert data["ok"] is True
    assert data["count"] >= 1
    got = json.loads(docs_tools.lib_docs_get({"package": "react", "ecosystem": "auto"}))
    assert got["ok"] is True
    assert got["ecosystem"] == "npm"
    assert "markdown" in got
    assert "warning" in got
    recent = json.loads(docs_tools.lib_docs_recent({}))
    assert recent["ok"] is True
    assert recent["count"] >= 1


def test_invalid_package() -> None:
    bad = docs_fetch.get_docs("http://evil.example", ecosystem="npm")
    assert bad["ok"] is False


if __name__ == "__main__":
    test_resolve_npm()
    test_get_npm()
    test_get_pypi()
    test_auto_prefers_npm_on_collision()
    test_guess()
    test_tools_json()
    test_invalid_package()
    print("ok")
