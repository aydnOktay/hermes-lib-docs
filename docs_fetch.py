"""HTTPS fetch helpers for public npm / PyPI registries (stdlib only)."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

USER_AGENT = "hermes-lib-docs/0.1 (+https://github.com/aydnOktay/hermes-lib-docs)"
TIMEOUT = 20
MAX_BODY = 2_000_000
MAX_README = 12_000

# Injected in tests
_FETCH_IMPL = None

_PKG_RE = re.compile(r"^(@[a-z0-9._-]+/)?[a-z0-9._-]+$", re.IGNORECASE)
_PY_RE = re.compile(r"^[a-z0-9]([a-z0-9._-]*[a-z0-9])?$", re.IGNORECASE)


def normalize_package(raw: str) -> str | None:
    text = (raw or "").strip()
    if not text or len(text) > 214:
        return None
    if "://" in text or " " in text or "\n" in text:
        return None
    return text


def guess_ecosystem(package: str) -> str:
    name = package.strip()
    if name.startswith("@"):
        return "npm"
    if "_" in name and "-" not in name:
        return "pypi"
    return "npm"


def http_get_json(url: str) -> dict[str, Any]:
    raw = http_get_bytes(url)
    data = json.loads(raw.decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError("expected JSON object")
    return data


def http_get_bytes(url: str) -> bytes:
    if _FETCH_IMPL is not None:
        return _FETCH_IMPL(url)
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json, text/plain, */*",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = resp.read(MAX_BODY + 1)
    except urllib.error.HTTPError as exc:
        body = ""
        try:
            body = exc.read(200).decode("utf-8", errors="replace")
        except Exception:
            pass
        raise RuntimeError(f"HTTP {exc.code} for {url}: {body[:120]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"network error for {url}: {exc.reason}") from exc
    if len(data) > MAX_BODY:
        raise RuntimeError("response too large")
    return data


def truncate_readme(text: str) -> str:
    cleaned = (text or "").strip()
    if len(cleaned) <= MAX_README:
        return cleaned
    return cleaned[: MAX_README - 1] + "…"


def search_npm(query: str, limit: int = 8) -> list[dict[str, Any]]:
    q = urllib.parse.quote(query.strip())
    size = max(1, min(int(limit), 15))
    url = f"https://registry.npmjs.org/-/v1/search?text={q}&size={size}"
    data = http_get_json(url)
    out: list[dict[str, Any]] = []
    for hit in data.get("objects") or []:
        if not isinstance(hit, dict):
            continue
        pkg = hit.get("package") if isinstance(hit.get("package"), dict) else {}
        name = pkg.get("name")
        if not isinstance(name, str):
            continue
        out.append(
            {
                "ecosystem": "npm",
                "package": name,
                "version": str(pkg.get("version") or ""),
                "description": str(pkg.get("description") or "")[:240],
                "homepage": _homepage_npm(pkg),
            }
        )
    return out


def search_pypi(query: str, limit: int = 8) -> list[dict[str, Any]]:
    """PyPI has no stable public search JSON; try exact name first."""
    del limit
    name = query.strip().replace(" ", "-")
    if not _PY_RE.match(name):
        return []
    try:
        meta = get_pypi(name)
    except Exception:
        return []
    return [
        {
            "ecosystem": "pypi",
            "package": meta["package"],
            "version": meta.get("version") or "",
            "description": (meta.get("description") or "")[:240],
            "homepage": meta.get("homepage") or "",
        }
    ]


def get_npm(package: str, version: str | None = None) -> dict[str, Any]:
    name = normalize_package(package)
    if not name or not _PKG_RE.match(name):
        raise ValueError(f"invalid npm package name: {package!r}")
    enc = urllib.parse.quote(name, safe="@/")
    url = f"https://registry.npmjs.org/{enc}"
    data = http_get_json(url)
    tags = data.get("dist-tags") if isinstance(data.get("dist-tags"), dict) else {}
    latest = str(tags.get("latest") or "")
    ver = (version or latest or "").strip()
    versions = data.get("versions") if isinstance(data.get("versions"), dict) else {}
    if ver and ver not in versions and latest:
        ver = latest
    info = versions.get(ver) if ver else None
    if not isinstance(info, dict):
        info = {}
    readme = ""
    if isinstance(info.get("readme"), str) and info["readme"].strip():
        readme = info["readme"]
    elif isinstance(data.get("readme"), str):
        readme = data["readme"]
    if not readme and ver:
        readme = _try_jsdelivr_readme(name, ver)
    desc = str(info.get("description") or data.get("description") or "")
    return {
        "ok": True,
        "ecosystem": "npm",
        "package": name,
        "version": ver or latest,
        "description": desc[:500],
        "homepage": _homepage_npm(info) or _homepage_npm(data),
        "license": str(info.get("license") or data.get("license") or "")[:80],
        "readme": truncate_readme(readme),
        "source": "registry.npmjs.org",
    }


def get_pypi(package: str, version: str | None = None) -> dict[str, Any]:
    name = normalize_package(package)
    if not name or not re.match(r"^[A-Za-z0-9][A-Za-z0-9._-]*$", name):
        raise ValueError(f"invalid PyPI package name: {package!r}")
    enc = urllib.parse.quote(name)
    if version:
        url = f"https://pypi.org/pypi/{enc}/{urllib.parse.quote(version)}/json"
    else:
        url = f"https://pypi.org/pypi/{enc}/json"
    data = http_get_json(url)
    info = data.get("info") if isinstance(data.get("info"), dict) else {}
    ver = str(info.get("version") or version or "")
    desc = str(info.get("summary") or "")
    body = ""
    if isinstance(info.get("description"), str) and info["description"].strip():
        body = info["description"]
    homepage = ""
    for key in ("home_page", "project_url"):
        val = info.get(key)
        if isinstance(val, str) and val.startswith("http"):
            homepage = val
            break
    urls = info.get("project_urls")
    if not homepage and isinstance(urls, dict):
        for key in ("Homepage", "Documentation", "Source", "Repository"):
            val = urls.get(key)
            if isinstance(val, str) and val.startswith("http"):
                homepage = val
                break
    return {
        "ok": True,
        "ecosystem": "pypi",
        "package": str(info.get("name") or name),
        "version": ver,
        "description": desc[:500],
        "homepage": homepage[:300],
        "license": str(info.get("license") or "")[:80],
        "readme": truncate_readme(body),
        "source": "pypi.org",
    }


def _homepage_npm(pkg: dict[str, Any]) -> str:
    for key in ("homepage", "url"):
        val = pkg.get(key)
        if isinstance(val, str) and val.startswith("http"):
            return val[:300]
    links = pkg.get("links")
    if isinstance(links, dict):
        for key in ("homepage", "repository", "npm"):
            val = links.get(key)
            if isinstance(val, str) and val.startswith("http"):
                return val[:300]
    repo = pkg.get("repository")
    if isinstance(repo, dict) and isinstance(repo.get("url"), str):
        return str(repo["url"])[:300]
    if isinstance(repo, str) and repo.startswith("http"):
        return repo[:300]
    return ""


def _try_jsdelivr_readme(package: str, version: str) -> str:
    enc = urllib.parse.quote(package, safe="@/")
    ver = urllib.parse.quote(version)
    url = f"https://cdn.jsdelivr.net/npm/{enc}@{ver}/README.md"
    try:
        raw = http_get_bytes(url)
        text = raw.decode("utf-8", errors="replace")
        return text
    except Exception:
        return ""


def resolve(query: str, ecosystem: str = "auto", limit: int = 8) -> list[dict[str, Any]]:
    q = (query or "").strip()
    if not q:
        return []
    eco = (ecosystem or "auto").lower()
    lim = max(1, min(int(limit or 8), 15))
    hits: list[dict[str, Any]] = []
    if eco in {"auto", "npm"}:
        try:
            hits.extend(search_npm(q, lim))
        except Exception:
            pass
    if eco in {"auto", "pypi"}:
        try:
            hits.extend(search_pypi(q, lim))
        except Exception:
            pass
    # Dedup by ecosystem+package
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for hit in hits:
        key = f"{hit.get('ecosystem')}:{hit.get('package')}"
        if key in seen:
            continue
        seen.add(key)
        out.append(hit)
        if len(out) >= lim:
            break
    return out


def get_docs(package: str, ecosystem: str = "auto", version: str | None = None) -> dict[str, Any]:
    name = normalize_package(package)
    if not name:
        return {"ok": False, "error": "invalid package name"}
    eco = (ecosystem or "auto").lower()
    if eco == "auto":
        eco = guess_ecosystem(name)
    try:
        if eco == "pypi":
            return get_pypi(name, version)
        if eco == "npm":
            return get_npm(name, version)
        return {"ok": False, "error": f"unknown ecosystem: {ecosystem}"}
    except Exception as exc:
        # auto fallback: try the other registry once
        if (ecosystem or "auto").lower() == "auto":
            other = "pypi" if eco == "npm" else "npm"
            try:
                if other == "pypi":
                    return get_pypi(name, version)
                return get_npm(name, version)
            except Exception as exc2:
                return {"ok": False, "error": str(exc2)}
        return {"ok": False, "error": str(exc)}
