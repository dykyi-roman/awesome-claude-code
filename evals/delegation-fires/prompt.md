---
name: "Audit command actually delegates to its agent"
tags: ["smoke", "wiring"]
runs: 2
max_turns: 4
timeout_seconds: 240
allowed_tools: ["Read", "Grep", "Glob", "Task"]
---

Run a quick DDD architecture audit of the `src/` directory.
