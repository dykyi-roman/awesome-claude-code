# Memory and Rules Reference

Complete guide to CLAUDE.md hierarchy, rules files, imports, and memory management.

## CLAUDE.md Hierarchy

### File Locations and Priority

Files are loaded top-to-bottom; higher priority overrides lower:

| Priority | File | Location | Scope | Versioned |
|----------|------|----------|-------|-----------|
| 1 (highest) | Managed CLAUDE.md | Enterprise system dirs | Organization | Yes (admin) |
| 2 | User CLAUDE.md | `~/.claude/CLAUDE.md` | All user projects | No |
| 3 | User rules | `~/.claude/rules/*.md` | All user projects | No |
| 4 | Project CLAUDE.md | `CLAUDE.md` (project root) | This project | Yes |
| 5 | Project rules | `.claude/rules/*.md` | This project | Yes |
| 6 | Local CLAUDE.md | `CLAUDE.local.md` (project root) | This machine | No (gitignored) |
| 7 | Nested CLAUDE.md | `src/CLAUDE.md`, etc. | Subdirectory | Yes |

### What Each Level Is For

**User CLAUDE.md (`~/.claude/CLAUDE.md`):**
- Personal preferences (language, coding style)
- Global rules that apply to all projects
- Example: "Respond in Russian", "Use vim keybindings"

**User rules (`~/.claude/rules/*.md`):**
- Modular user-level rules
- Each file = one topic
- Loaded into all sessions

**Project CLAUDE.md (root `CLAUDE.md`):**
- Project-specific instructions
- Architecture decisions, tech stack
- Coding conventions, testing rules
- Shared with team (committed to git)

**Project rules (`.claude/rules/*.md`):**
- Modular project rules
- Path-scoped rules (with `paths` frontmatter)
- Always loaded into system prompt

**Local CLAUDE.md (`CLAUDE.local.md`):**
- Machine-specific overrides
- Local paths, environment variables
- Auto-added to `.gitignore`
- Not shared with team

**Nested CLAUDE.md (`src/CLAUDE.md`, `tests/CLAUDE.md`):**
- Subdirectory-specific context
- Loaded when working in that directory
- Example: `tests/CLAUDE.md` — testing conventions for this directory

## Rules Files

### Basic Rules

```
.claude/
└── rules/
    ├── coding-standards.md    # PSR-12, strict types
    ├── architecture.md        # DDD, Clean Architecture
    ├── testing.md             # Test conventions
    └── security.md            # Security guidelines
```

Each `.md` file is loaded into the system prompt automatically.

### Path-Specific Rules

```yaml
---
paths:
  - src/Domain/**
  - src/Application/**
---

# Domain Layer Rules

- All classes must be final and readonly
- No infrastructure dependencies
- Use Value Objects for all domain concepts
- Events must be immutable
```

**Path matching:**
- Uses glob patterns (gitignore-style)
- `**` matches any depth
- `*` matches single level
- Rules only loaded when working with matching files

### Multiple Path Rules

```yaml
---
paths:
  - tests/**
  - spec/**
---

# Testing Rules

- Use AAA pattern (Arrange-Act-Assert)
- One assertion per test method
- Mock external dependencies
```

## Import Syntax (@path)

### Relative Import

```markdown
# CLAUDE.md

@docs/architecture.md
@.claude/rules/custom.md
```

Paths are relative to the file containing the `@` import.

### Absolute Import

```markdown
@/Users/shared/company-standards.md
```

### Home Directory Import

```markdown
@~/my-rules/personal-preferences.md
```

### Import Rules

1. **Max recursion depth:** 5 hops (A imports B imports C... max 5 levels)
2. **Circular imports:** Detected and prevented
3. **Missing files:** Warning logged, import skipped
4. **File types:** Only `.md` files
5. **Import position:** Inline — content inserted at import location

### Import Example

```markdown
# CLAUDE.md

## Project Overview
This is a DDD project with PHP 8.4.

## Standards
@.claude/rules/coding-standards.md
@.claude/rules/architecture.md

## Local Overrides
@CLAUDE.local.md
```

## Commands

### /memory

View and manage memory files:
- Shows all CLAUDE.md files in hierarchy
- Allows viewing content of each file
- Navigate between memory levels

### /init

Generate initial CLAUDE.md from project analysis:
- Scans project structure
- Detects tech stack (composer.json, package.json, etc.)
- Identifies architecture patterns
- Generates starter CLAUDE.md with project-specific instructions
- Non-destructive — does not overwrite existing files

### --add-dir Flag

```bash
claude --add-dir /path/to/other/project
```

**What it does:**
- Adds another directory's CLAUDE.md to context
- Environment variable: `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD`
- Useful for monorepos or shared configurations

## Nested Directory Discovery

Claude discovers CLAUDE.md files as it navigates the project:

```
project/
├── CLAUDE.md              # Always loaded
├── src/
│   ├── CLAUDE.md          # Loaded when working in src/
│   └── Domain/
│       └── CLAUDE.md      # Loaded when working in src/Domain/
└── tests/
    └── CLAUDE.md          # Loaded when working in tests/
```

**Discovery behavior:**
- Root CLAUDE.md always loaded
- Subdirectory CLAUDE.md loaded when Claude reads/modifies files in that directory
- Multiple levels stack (root + src + src/Domain)
- Nested rules supplement, not replace, parent rules

## Auto-Memory

Claude Code has a persistent auto-memory directory:

```
~/.claude/projects/<project-hash>/memory/
├── MEMORY.md              # Auto-loaded into system prompt
├── debugging.md           # Topic-specific notes
├── patterns.md            # Patterns discovered
└── architecture.md        # Architecture notes
```

**MEMORY.md behavior:**
- First ~200 lines loaded into system prompt
- Updated by Claude as it learns about the project
- Persists across conversations
- Topic files linked from MEMORY.md

## Best Practices

### Content Guidelines

1. **Keep CLAUDE.md under 500 lines** — it's always in context
2. **Be specific, not general** — "Use PSR-12" not "Follow best practices"
3. **Use rules/ for modularity** — split large CLAUDE.md into rule files
4. **Use paths for scoping** — avoid loading irrelevant rules
5. **Use CLAUDE.local.md for personal** — machine-specific settings
6. **Import shared standards** — `@` import for DRY configuration

### Organization Pattern

```
CLAUDE.md                      # Project overview + key rules (< 200 lines)
├── @.claude/rules/arch.md     # Architecture rules
├── @.claude/rules/testing.md  # Testing rules
└── @.claude/rules/security.md # Security rules

CLAUDE.local.md                # Local overrides (gitignored)
└── Machine-specific paths, env vars
```

### What NOT to Put in CLAUDE.md

- Entire API documentation (use skills instead)
- Full code examples (use skills with references/)
- Frequently changing information (use auto-memory)
- Machine-specific paths (use CLAUDE.local.md)
- Sensitive information (use environment variables)
