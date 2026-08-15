---
name: "Hook wizard must only offer real events"
tags: ["regression", "meta", "smoke"]
runs: 3
max_turns: 6
timeout_seconds: 240
allowed_tools: ["Read", "Skill", "Grep", "Glob"]
---

I want a hook that reacts when a tool call fails, and another that runs before Claude processes
my prompt. Which Claude Code hook events do I use, and what does the `hooks.json` look like?
