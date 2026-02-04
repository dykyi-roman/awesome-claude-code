# Commands

Slash commands for Claude Code. Commands are user-invoked actions triggered by typing `/command-name` in the CLI.

## Meta-Instructions Support

All commands support optional meta-instructions via `--` separator:

```
/command <arguments> -- <meta-instructions>
```

**Examples:**
```bash
/acc-audit-ddd ./src -- focus on aggregate boundaries
/acc-write-test src/Order.php -- only unit tests, skip integration
/acc-commit v2.5.0 -- mention breaking changes
/acc-audit-architecture ./src -- на русском языке
```

Meta-instructions allow you to:
- Focus analysis on specific aspects
- Include/exclude certain checks
- Request specific output language
- Add custom context to the task

## Overview

| Command | Arguments | Purpose |
|---------|-----------|---------|
| `/acc-commit` | `[tag] [-- instructions]` | Auto-generate commit message and push |
| `/acc-write-claude-component` | `[type] [-- instructions]` | Create commands, agents, or skills |
| `/acc-audit-claude-components` | `[-- instructions]` | Audit `.claude/` folder quality |
| `/acc-audit-architecture` | `<path> [-- instructions]` | Multi-pattern architecture audit |
| `/acc-audit-ddd` | `<path> [-- instructions]` | DDD compliance analysis |
| `/acc-audit-psr` | `<path> [-- instructions]` | PSR compliance audit |
| `/acc-write-documentation` | `<path> [-- instructions]` | Generate documentation |
| `/acc-audit-documentation` | `<path> [-- instructions]` | Audit documentation quality |
| `/acc-write-test` | `<path> [-- instructions]` | Generate tests for PHP code |
| `/acc-audit-test` | `<path> [-- instructions]` | Audit test quality and coverage |
| `/acc-code-review` | `[branch] [level] [-- task]` | Multi-level code review with task matching |

---

## `/acc-write-claude-component`

**Path:** `commands/acc-write-claude-component.md`

Interactive wizard for creating Claude Code components.

**Arguments:**
```
/acc-write-claude-component [type] [-- instructions]
```

| Argument | Required | Description |
|----------|----------|-------------|
| `type` | No | Component type: `command`, `agent`, `skill`, `hook` |
| `-- instructions` | No | Additional context for generation |

**Examples:**
```bash
/acc-write-claude-component                        # Interactive mode
/acc-write-claude-component command                # Skip type selection
/acc-write-claude-component agent -- for DDD auditing
/acc-write-claude-component skill -- generates Value Objects
```

**Process:**
1. Asks what to create (command/agent/skill/hook) — skipped if type provided
2. Gathers requirements through questions
3. Uses `acc-claude-code-expert` agent with `acc-claude-code-knowledge` skill
4. Creates component with proper structure
5. Validates and shows result

---

## `/acc-audit-claude-components`

**Path:** `commands/acc-audit-claude-components.md`

Audit `.claude/` folder structure and configuration quality.

**Arguments:**
```
/acc-audit-claude-components [-- instructions]
```

| Argument | Required | Description |
|----------|----------|-------------|
| `-- instructions` | No | Focus audit on specific aspects |

**Examples:**
```bash
/acc-audit-claude-components                           # Full audit
/acc-audit-claude-components -- focus on agents only
/acc-audit-claude-components -- check for unused skills
```

**Analyzes:**
- Commands (YAML frontmatter, descriptions, tool restrictions)
- Agents (naming, skills references, tool permissions)
- Skills (structure, size, references)
- Settings (hooks, permissions, secrets)
- Cross-references integrity

**Output:**
- File tree with status indicators
- Detailed issues analysis
- Prioritized recommendations
- Ready-to-apply quick fixes

---

## `/acc-commit`

**Path:** `commands/acc-commit.md`

Auto-generate commit message from diff and push to current branch.

**Arguments:**
```
/acc-commit [tag-name] [-- instructions]
```

| Argument | Required | Description |
|----------|----------|-------------|
| `tag-name` | No | Version tag to create (e.g., `v2.5.0`) |
| `-- instructions` | No | Hints for commit message |

**Examples:**
```bash
/acc-commit                                      # Commit and push
/acc-commit v2.5.0                               # Commit, push, and tag
/acc-commit -- focus on security changes
/acc-commit v2.5.0 -- mention breaking changes
/acc-commit -- use Russian for commit message
```

---

## `/acc-audit-architecture`

**Path:** `commands/acc-audit-architecture.md`

Comprehensive multi-pattern architecture audit for PHP projects.

**Arguments:**
```
/acc-audit-architecture <path> [-- instructions]
```

| Argument | Required | Description |
|----------|----------|-------------|
| `path` | **Yes** | Path to project or folder to audit |
| `-- instructions` | No | Focus or customize the audit |

**Examples:**
```bash
/acc-audit-architecture ./src
/acc-audit-architecture ./src -- only check CQRS patterns
/acc-audit-architecture ./src -- generate fixes for violations
/acc-audit-architecture ./src -- на русском языке
```

**Analyzes:**
- DDD compliance
- CQRS patterns
- Clean Architecture
- Hexagonal Architecture
- Layered Architecture
- Event Sourcing
- Event-Driven Architecture
- Outbox Pattern
- Saga Pattern
- Stability Patterns

---

## `/acc-audit-ddd`

**Path:** `commands/acc-audit-ddd.md`

DDD compliance analysis for PHP projects.

**Arguments:**
```
/acc-audit-ddd <path> [-- instructions]
```

| Argument | Required | Description |
|----------|----------|-------------|
| `path` | **Yes** | Path to project or folder to audit |
| `-- instructions` | No | Focus on specific DDD aspects |

**Examples:**
```bash
/acc-audit-ddd ./src
/acc-audit-ddd ./src/Domain/Order -- focus on aggregate boundaries
/acc-audit-ddd ./src -- generate missing Value Objects
```

---

## `/acc-audit-psr`

**Path:** `commands/acc-audit-psr.md`

PSR compliance analysis for PHP projects.

**Arguments:**
```
/acc-audit-psr <path> [-- instructions]
```

| Argument | Required | Description |
|----------|----------|-------------|
| `path` | **Yes** | Path to project or folder to audit |
| `-- instructions` | No | Focus on specific PSR standards |

**Examples:**
```bash
/acc-audit-psr ./src
/acc-audit-psr ./src -- only PSR-12 style check
/acc-audit-psr ./src -- generate missing PSR interfaces
```

**Checks:**
- PSR-1/PSR-12 coding style compliance
- PSR-4 autoloading structure
- PSR interface implementations

---

## `/acc-write-documentation`

**Path:** `commands/acc-write-documentation.md`

Generate documentation for a file, folder, or project.

**Arguments:**
```
/acc-write-documentation <path> [-- instructions]
```

| Argument | Required | Description |
|----------|----------|-------------|
| `path` | **Yes** | Path to file/folder to document (`.` for project root) |
| `-- instructions` | No | Customize documentation output |

**Examples:**
```bash
/acc-write-documentation ./
/acc-write-documentation src/ -- focus on API documentation
/acc-write-documentation ./ -- create architecture doc with C4 diagrams
/acc-write-documentation src/Domain/Order -- document only public interfaces
/acc-write-documentation ./ -- на русском языке
```

**Generates:**
- README.md for projects
- ARCHITECTURE.md with diagrams
- API documentation
- Getting started guides

---

## `/acc-audit-documentation`

**Path:** `commands/acc-audit-documentation.md`

Audit documentation quality.

**Arguments:**
```
/acc-audit-documentation <path> [-- instructions]
```

| Argument | Required | Description |
|----------|----------|-------------|
| `path` | **Yes** | Path to documentation folder to audit |
| `-- instructions` | No | Focus on specific quality aspects |

**Examples:**
```bash
/acc-audit-documentation ./docs
/acc-audit-documentation ./docs -- only check code examples
/acc-audit-documentation ./ -- fix broken links
```

**Checks:**
- Completeness (all APIs documented)
- Accuracy (code matches docs)
- Clarity (no jargon, working examples)
- Consistency (uniform style)
- Navigation (working links)

---

## `/acc-write-test`

**Path:** `commands/acc-write-test.md`

Generate tests for PHP file or folder.

**Arguments:**
```
/acc-write-test <path> [-- instructions]
```

| Argument | Required | Description |
|----------|----------|-------------|
| `path` | **Yes** | Path to PHP file or folder to test |
| `-- instructions` | No | Customize test generation |

**Examples:**
```bash
/acc-write-test src/Domain/Order/Order.php
/acc-write-test src/Domain/Order/ -- only unit tests, skip integration
/acc-write-test src/Service/PaymentService.php -- include edge cases for null payments
/acc-write-test src/ -- create builders for all entities
/acc-write-test src/Application/ -- focus on happy path scenarios
```

**Generates:**
- Unit tests for Value Objects, Entities, Services
- Integration tests for Repositories, HTTP clients
- Test Data Builders and Object Mothers
- InMemory repository implementations
- Test doubles (Mocks, Stubs, Fakes, Spies)

---

## `/acc-audit-test`

**Path:** `commands/acc-audit-test.md`

Audit test quality and coverage.

**Arguments:**
```
/acc-audit-test <path> [-- instructions]
```

| Argument | Required | Description |
|----------|----------|-------------|
| `path` | **Yes** | Path to tests folder or project |
| `-- instructions` | No | Focus on specific quality aspects |

**Examples:**
```bash
/acc-audit-test ./tests
/acc-audit-test ./src -- check coverage gaps only
/acc-audit-test ./tests -- focus on test smells
/acc-audit-test ./tests/Unit/Domain -- generate missing tests
```

**Checks:**
- Coverage gaps (untested classes, methods, branches)
- Test smells (15 antipatterns)
- Naming convention compliance
- Test isolation issues

**Output:**
- Quality metrics with scores
- Prioritized issues list
- Skill recommendations for fixes

---

## `/acc-code-review`

**Path:** `commands/acc-code-review.md`

Multi-level code review with git diff analysis and task matching.

**Arguments:**
```
/acc-code-review [branch] [level] [-- task-description]
```

| Argument | Required | Description |
|----------|----------|-------------|
| `branch` | No | Branch to review (default: current branch) |
| `level` | No | Review depth: `low`, `medium`, `high` (default: high) |
| `-- task-description` | No | Expected task for matching analysis |

**Examples:**
```bash
/acc-code-review                                    # Current branch, high level
/acc-code-review feature/payment                    # feature/payment vs main, high
/acc-code-review medium                             # Current branch, medium level
/acc-code-review feature/payment medium             # feature/payment vs main, medium
/acc-code-review feature/payment -- add auth        # With task matching
/acc-code-review -- implement JWT auth              # Current branch + task matching
/acc-code-review feature/payment low -- add tests   # All options combined
```

**Review Levels:**

| Level | Checks | Use Case |
|-------|--------|----------|
| **LOW** | PSR compliance, test quality, encapsulation, code smells | Quick PR check |
| **MEDIUM** | LOW + bug detection, readability, SOLID violations | Standard review |
| **HIGH** | MEDIUM + security, performance, testability, DDD, architecture | Full audit |

**Output:**
- Change summary (files, commits, lines changed)
- Findings by severity (Critical/Major/Minor/Suggestion)
- Task match analysis with percentage score (if task provided)
- Verdict: APPROVE / APPROVE WITH COMMENTS / REQUEST CHANGES

---

## Navigation

[← Back to README](../README.md) | [Agents →](agents.md) | [Skills](skills.md) | [Component Flow](component-flow.md) | [Quick Reference](quick-reference.md)
