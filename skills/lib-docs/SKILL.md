---
name: lib-docs
description: >
  Use when the user asks how a library/API works, needs current docs for an npm
  or PyPI package, or when training data may be stale. Load with
  skill_view("lib-docs:lib-docs").
---

# lib-docs

Fetches **current** package metadata and README from public npm and PyPI.
No API key. Prefer this over inventing APIs from memory.

## When to use

- User: "react 19'da nasıl", "fastapi docs", "lodash debounce signature"
- Call `lib_docs_resolve` if the package id is unclear
- Then `lib_docs_get` and quote from the returned README / description
- Do not invent APIs that are not in the tool result
- If the result has `warning` / `also_on`, check the ecosystem — names like
  `react` exist on both npm and PyPI. Prefer the user's stack or force
  `ecosystem: "npm"` / `"pypi"`.

## Notes

- Network: `registry.npmjs.org` and `pypi.org` only
- Recent lookups: `lib_docs_recent`
- Auto probes both registries and prefers likely ecosystem with a warning
