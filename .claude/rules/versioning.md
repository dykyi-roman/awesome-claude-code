---
paths:
  - CHANGELOG.md
  - README.md
  - docs/**/*.md
  - llms.txt
---

# Versioning

1. Update `CHANGELOG.md` creating a new section (format: `[X.Y.Z] - YYYY-MM-DD`)
2. Run `make validate-claude`
3. Update component counts in `README.md`, `docs/quick-reference.md` if changed
4. Add comparison link at bottom of `CHANGELOG.md`
5. Run `make release` (validates + prints git tag instructions)

## Documentation Files

| File                      | What to Update                                                          |
|---------------------------|-------------------------------------------------------------------------|
| `docs/commands.md`        | New/changed slash commands — overview table + detailed section          |
| `docs/agents.md`          | New/changed agents — category table + description section               |
| `docs/skills.md`          | New/changed skills — categorized by type (knowledge/analyzer/generator) |
| `docs/hooks.md`           | New hooks for `hooks/hooks.json`                                        |
| `docs/component-flow.md`  | Dependency graph when adding command→agent→skill chains                 |
| `docs/quick-reference.md` | Component counts, file structure diagram, statistics table              |
| `llms.txt`                | Quick Facts, commands, agents, skills counts, project structure         |

## Count Sync Files

Component counts (26 commands, 68 agents, 283 skills) must be synchronized across:
- `README.md` (Documentation table)
- `docs/quick-reference.md` (Statistics + file tree)
- `.claude-plugin/marketplace.json` (plugin description)
- `llms.txt` (Quick Facts + Project Structure)
- `CHANGELOG.md`
- `CLAUDE.md` (Architecture section)
