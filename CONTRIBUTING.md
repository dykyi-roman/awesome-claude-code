# Contributing to Awesome Claude Code

Thank you for your interest in contributing!

## How to Contribute

### Reporting Issues

1. Check existing issues to avoid duplicates
2. Use issue templates when available
3. Include: PHP version, Composer version, Claude Code version
4. Provide minimal reproduction steps

### Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Run validation: `make validate-claude`
5. Commit with descriptive message
6. Push and create a Pull Request

### Code Style

- Follow PSR-12 coding standards
- Use `declare(strict_types=1)` in all PHP files
- Write self-documenting code
- Add PHPDoc for public methods

### Component Guidelines

**Commands:**
- Use `acc-` prefix
- Include YAML frontmatter with `description`
- Document arguments and examples

**Agents:**
- Include `name`, `description`, `tools` in frontmatter
- Reference skills in `skills:` list
- Keep to max 15 skills per agent

**Skills:**
- Keep under 500 lines
- Use `references/` folder for templates
- Include working examples

### Testing

Before submitting:

```bash
make validate-claude  # Validate .claude structure
make test            # Run in Docker test environment
```

### Questions?

Open an issue with the "question" label.
