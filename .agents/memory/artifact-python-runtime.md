---
name: Python runtime inside web artifacts
description: The managed web artifact can preview a Flask app through its development command even when the bootstrap template is Vite-based.
---

The preview workflow is the reliable runtime boundary for a Python/Flask app placed inside a web artifact; keep the generated artifact routing intact unless a production process mode is explicitly accepted by the artifact schema.

**Why:** The artifact validator rejected a hand-authored production process configuration while the managed development workflow served the Flask app correctly.

**How to apply:** For future Python web apps in this workspace, prioritize the managed preview workflow and validate any production TOML change through the artifact replacement callback before relying on it.