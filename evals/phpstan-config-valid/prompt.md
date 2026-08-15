---
name: "Generated phpstan.neon must load on PHPStan 2.x"
tags: ["regression", "generator", "ci"]
runs: 2
max_turns: 6
timeout_seconds: 240
allowed_tools: ["Read", "Skill", "Grep", "Glob"]
---

Generate a strict `phpstan.neon` for a PHP 8.4 DDD project with `src/` and `tests/`,
using the create-phpstan-config skill. I run the current PHPStan release.
