---
paths:
  - .claude/**
  - src/*.php
  - Makefile
---

# Troubleshooting

| Issue                     | Cause                                          | Fix                                                                      |
|---------------------------|------------------------------------------------|--------------------------------------------------------------------------|
| Skill not loading         | Missing from agent's `skills:` frontmatter     | Add skill name to agent's comma-separated `skills:` list                 |
| Agent not invoked         | Command uses wrong `subagent_type`             | Match `subagent_type` to agent filename (without `.md`)                  |
| Validation fails          | Frontmatter missing or malformed               | Ensure file starts with `---` and has required fields                    |
| Plugin doesn't copy files | Plugin not allowed in Composer                 | Run `composer config allow-plugins.dykyi-roman/awesome-claude-code true` |
| Orphaned skill in audit   | Skill folder exists but no agent references it | Add skill to appropriate agent's `skills:` frontmatter                   |
