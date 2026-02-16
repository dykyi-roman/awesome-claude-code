---
paths:
  - commands/**
  - agents/**
  - skills/**
  - Makefile
---

# Troubleshooting

| Issue                     | Cause                                          | Fix                                                                      |
|---------------------------|------------------------------------------------|--------------------------------------------------------------------------|
| Skill not loading         | Missing from agent's `skills:` frontmatter     | Add skill name to agent's comma-separated `skills:` list                 |
| Agent not invoked         | Command uses wrong `subagent_type`             | Match `subagent_type` to `acc:agent-filename` (without `.md`)            |
| Validation fails          | Frontmatter missing or malformed               | Ensure file starts with `---` and has required fields                    |
| Plugin not loading        | Missing `.claude-plugin/plugin.json`           | Check `.claude-plugin/` directory has both `marketplace.json` and `plugin.json` |
| Orphaned skill in audit   | Skill folder exists but no agent references it | Add skill to appropriate agent's `skills:` frontmatter                   |
