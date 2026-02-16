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

**Agents (`agents/name.md`):**
- Include `name`, `description`, `tools` in frontmatter
- Reference skills in `skills:` list (without prefix)
- Keep to max 15 skills per agent

**Skills (`skills/name/SKILL.md`):**
- Keep under 500 lines
- Use `references/` folder for templates
- Include working examples

### Testing

Before submitting:

```bash
make validate-claude  # Validate plugin structure
```

### Questions?

Open an issue with the "question" label.
