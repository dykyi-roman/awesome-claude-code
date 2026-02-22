# Contributing to Awesome Claude Code

Thank you for your interest in contributing!

## How to Contribute

### Reporting Issues

1. Check existing issues to avoid duplicates
2. Use issue templates when available
3. Include: Claude Code version, OS, reproduction steps
4. Provide minimal reproduction steps

### Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Run validation: `make validate-claude`
5. Commit with descriptive message
6. Push and create a Pull Request

### Component Guidelines

**Commands (`commands/name.md`):**
- Include YAML frontmatter with `description`
- Document arguments and examples
- Use `/acc:name` syntax in examples
- Support `--` separator for meta-instructions
- Include pre-flight checks for required arguments

**Agents (`agents/name.md`):**
- Include `name`, `description`, `tools` in frontmatter
- Reference skills in `skills:` list (bare names, no `acc:` prefix)
- Max 15 skills per agent (over 15 = God-Agent, must split)
- Coordinators use `model: opus`; most specialists use `model: sonnet`
- Sub-auditors requiring deep analysis use `model: opus`

**Skills (`skills/name/SKILL.md`):**
- Keep under 500 lines
- Use `references/` folder for large templates and examples
- Include working examples
- Every skill must be referenced by at least one agent's `skills:` frontmatter

### Naming Conventions

- All components use `acc:` namespace prefix in invocation
- Filenames: lowercase with hyphens (`bug-fix-coordinator.md`)
- Agent categories: `*-coordinator`, `*-auditor`, `*-generator`, `*-reviewer`, `*-analyst`
- Skills: `create-*` (generators), `check-*` (analyzers), `*-knowledge` (knowledge bases)

### Count Synchronization

Component counts (commands, agents, skills) must be updated in **6 files** when changed:

| File | What to update |
|------|---------------|
| `README.md` | Documentation table |
| `docs/quick-reference.md` | Statistics + file tree |
| `.claude-plugin/marketplace.json` | Plugin description |
| `llms.txt` | Quick Facts + Project Structure |
| `CHANGELOG.md` | Release notes |
| `CLAUDE.md` | Architecture section |

### Validation and Release

Before submitting:

```bash
make validate-claude  # Validate plugin structure (required before every commit)
make list-commands    # Verify command count
make list-agents      # Verify agent count
make list-skills      # Verify skill count
make release          # Run validation + print git tag instructions
```

### Documentation Updates

When adding or modifying components, update the corresponding docs:

| Change | Files to update |
|--------|----------------|
| New command | `docs/commands.md`, `docs/component-flow.md` |
| New agent | `docs/agents.md`, `docs/component-flow.md` |
| New skill | `docs/skills.md` |
| New hook | `docs/hooks.md` |
| Dependency changes | `docs/component-flow.md` |

### Questions?

Open an issue with the "question" label.
