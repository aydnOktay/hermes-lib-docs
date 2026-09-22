"""Tool schemas — what the LLM sees."""

LIB_DOCS_RESOLVE = {
    "name": "lib_docs_resolve",
    "description": (
        "Search public npm and/or PyPI for a library name. Returns candidate "
        "packages with version and short description. Prefer this before "
        "lib_docs_get when the exact package id is unclear. No API key; "
        "HTTPS to registry.npmjs.org / pypi.org only."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Library name or search string, e.g. react, fastapi, lodash.",
            },
            "ecosystem": {
                "type": "string",
                "enum": ["auto", "npm", "pypi"],
                "description": "Which registry to search. auto tries both.",
                "default": "auto",
            },
            "limit": {
                "type": "integer",
                "description": "Max candidates (default 8, max 15).",
                "default": 8,
            },
        },
        "required": ["query"],
    },
}

LIB_DOCS_GET = {
    "name": "lib_docs_get",
    "description": (
        "Fetch current metadata and README for a package from npm or PyPI. "
        "Use when writing code against a library and training data may be stale. "
        "No API key. Prefer lib_docs_resolve first if the package id is ambiguous."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "package": {
                "type": "string",
                "description": "Exact package name (npm may be scoped @scope/name).",
            },
            "ecosystem": {
                "type": "string",
                "enum": ["auto", "npm", "pypi"],
                "description": "Registry. auto picks from the name shape.",
                "default": "auto",
            },
            "version": {
                "type": "string",
                "description": "Optional version pin (e.g. 19.0.0). Default: latest.",
            },
            "markdown": {
                "type": "boolean",
                "description": "If true, also include a short markdown summary.",
                "default": True,
            },
        },
        "required": ["package"],
    },
}

LIB_DOCS_RECENT = {
    "name": "lib_docs_recent",
    "description": (
        "List recent lib-docs lookups in this Hermes home (package, version, "
        "ecosystem). Does not fetch the network."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "markdown": {
                "type": "boolean",
                "description": "If true, also include a markdown list.",
                "default": True,
            }
        },
        "required": [],
    },
}
