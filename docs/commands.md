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
/acc-generate-test src/Order.php -- only unit tests, skip integration
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
| `/acc-generate-claude-component` | `[type] [-- instructions]` | Create commands, agents, or skills |
| `/acc-audit-claude-components` | `[level] [-- instructions]` | Audit `.claude/` folder quality |
| `/acc-audit-architecture` | `<path> [level] [-- instructions]` | Multi-pattern architecture audit |
| `/acc-audit-ddd` | `<path> [level] [-- instructions]` | DDD compliance analysis |
| `/acc-audit-psr` | `<path> [level] [-- instructions]` | PSR compliance audit |
| `/acc-audit-security` | `<path> [level] [-- instructions]` | OWASP Top 10 + PHP security audit |
| `/acc-audit-performance` | `<path> [level] [-- instructions]` | N+1, memory, caching, complexity audit |
| `/acc-audit-patterns` | `<path> [level] [-- instructions]` | Design patterns + SOLID/GRASP audit |
| `/acc-generate-ddd` | `<type> <name> [-- instructions]` | Generate DDD components (entity, VO, aggregate, etc.) |
| `/acc-generate-psr` | `<psr> <name> [-- instructions]` | Generate PSR-compliant components |
| `/acc-generate-patterns` | `<pattern> <name> [-- instructions]` | Generate design pattern implementations |
| `/acc-refactor` | `<path> [-- instructions]` | Guided refactoring with analysis |
| `/acc-generate-documentation` | `<path> [-- instructions]` | Generate documentation |
| `/acc-audit-documentation` | `<path> [level] [-- instructions]` | Audit documentation quality |
| `/acc-generate-test` | `<path> [-- instructions]` | Generate tests for PHP code |
| `/acc-audit-test` | `<path> [level] [-- instructions]` | Audit test quality and coverage |
| `/acc-code-review` | `[branch] [level] [-- task]` | Multi-level code review with task matching |
| `/acc-bug-fix` | `<description\|file:line\|trace>` | Diagnose and fix bug with regression testing |
| `/acc-ci-setup` | `<platform> [path] [-- instructions]` | Setup CI pipeline from scratch |
| `/acc-ci-fix` | `<pipeline-url\|log-file\|description> [-- instructions]` | Fix CI pipeline issues with interactive approval |
| `/acc-ci-optimize` | `[path] [-- focus areas]` | Optimize CI pipeline performance |
| `/acc-audit-ci` | `[path] [level] [-- instructions]` | Comprehensive CI/CD audit |
| `/acc-audit-docker` | `[path] [level] [-- instructions]` | Audit Docker config: Dockerfile, Compose, security, performance |
| `/acc-generate-docker` | `<type> [name] [-- instructions]` | Generate Docker components (Dockerfile, Compose, Nginx, etc.) |
| `/acc-explain` | `<path\|route\|command> [mode] [-- instructions]` | Explain code: structure, business logic, data flows, architecture |

---

## `/acc-generate-claude-component`

**Path:** `commands/acc-generate-claude-component.md`

Interactive wizard for creating Claude Code components.

**Arguments:**
```
/acc-generate-claude-component [type] [-- instructions]
```

| Argument | Required | Description |
|----------|----------|-------------|
| `type` | No | Component type: `command`, `agent`, `skill`, `hook` |
| `-- instructions` | No | Additional context for generation |

**Examples:**
```bash
/acc-generate-claude-component                        # Interactive mode
/acc-generate-claude-component command                # Skip type selection
/acc-generate-claude-component agent -- for DDD auditing
/acc-generate-claude-component skill -- generates Value Objects
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
/acc-audit-claude-components [level] [-- instructions]
```

| Argument | Required | Description |
|----------|----------|-------------|
| `level` | No | Audit depth: `quick`, `standard`, `deep` (default: standard) |
| `-- instructions` | No | Focus audit on specific aspects |

**Examples:**
```bash
/acc-audit-claude-components                           # Standard audit
/acc-audit-claude-components deep                      # Deep audit
/acc-audit-claude-components quick                     # Quick audit
/acc-audit-claude-components deep -- focus on agents only
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
/acc-audit-architecture <path> [level] [-- instructions]
```

| Argument | Required | Description |
|----------|----------|-------------|
| `path` | **Yes** | Path to project or folder to audit |
| `level` | No | Audit depth: `quick`, `standard`, `deep` (default: standard) |
| `-- instructions` | No | Focus or customize the audit |

**Examples:**
```bash
/acc-audit-architecture ./src
/acc-audit-architecture ./src deep
/acc-audit-architecture ./src quick
/acc-audit-architecture ./src deep -- only check CQRS patterns
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
- Stability Patterns (Circuit Breaker, Retry, Rate Limiter, Bulkhead)
- Behavioral Patterns (Strategy, State, Chain, Decorator, Null Object, Template Method, Visitor, Iterator, Memento)
- GoF Structural Patterns (Adapter, Facade, Proxy, Composite, Bridge, Flyweight)

---

## `/acc-audit-ddd`

**Path:** `commands/acc-audit-ddd.md`

DDD compliance analysis for PHP projects.

**Arguments:**
```
/acc-audit-ddd <path> [level] [-- instructions]
```

| Argument | Required | Description |
|----------|----------|-------------|
| `path` | **Yes** | Path to project or folder to audit |
| `level` | No | Audit depth: `quick`, `standard`, `deep` (default: standard) |
| `-- instructions` | No | Focus on specific DDD aspects |

**Examples:**
```bash
/acc-audit-ddd ./src
/acc-audit-ddd ./src deep
/acc-audit-ddd ./src/Domain/Order deep -- focus on aggregate boundaries
```

---

## `/acc-audit-psr`

**Path:** `commands/acc-audit-psr.md`

PSR compliance analysis for PHP projects.

**Arguments:**
```
/acc-audit-psr <path> [level] [-- instructions]
```

| Argument | Required | Description |
|----------|----------|-------------|
| `path` | **Yes** | Path to project or folder to audit |
| `level` | No | Audit depth: `quick`, `standard`, `deep` (default: standard) |
| `-- instructions` | No | Focus on specific PSR standards |

**Examples:**
```bash
/acc-audit-psr ./src
/acc-audit-psr ./src deep
/acc-audit-psr ./src quick -- only PSR-12 style check
```

**Checks:**
- PSR-1/PSR-12 coding style compliance
- PSR-4 autoloading structure
- PSR interface implementations

---

## `/acc-generate-documentation`

**Path:** `commands/acc-generate-documentation.md`

Generate documentation for a file, folder, or project.

**Arguments:**
```
/acc-generate-documentation <path> [-- instructions]
```

| Argument | Required | Description |
|----------|----------|-------------|
| `path` | **Yes** | Path to file/folder to document (`.` for project root) |
| `-- instructions` | No | Customize documentation output |

**Examples:**
```bash
/acc-generate-documentation ./
/acc-generate-documentation src/ -- focus on API documentation
/acc-generate-documentation ./ -- create architecture doc with C4 diagrams
/acc-generate-documentation src/Domain/Order -- document only public interfaces
/acc-generate-documentation ./ -- на русском языке
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
/acc-audit-documentation <path> [level] [-- instructions]
```

| Argument | Required | Description |
|----------|----------|-------------|
| `path` | **Yes** | Path to documentation folder to audit |
| `level` | No | Audit depth: `quick`, `standard`, `deep` (default: standard) |
| `-- instructions` | No | Focus on specific quality aspects |

**Examples:**
```bash
/acc-audit-documentation ./docs
/acc-audit-documentation ./docs deep
/acc-audit-documentation ./docs quick -- only check code examples
```

**Checks:**
- Completeness (all APIs documented)
- Accuracy (code matches docs)
- Clarity (no jargon, working examples)
- Consistency (uniform style)
- Navigation (working links)

---

## `/acc-generate-test`

**Path:** `commands/acc-generate-test.md`

Generate tests for PHP file or folder.

**Arguments:**
```
/acc-generate-test <path> [-- instructions]
```

| Argument | Required | Description |
|----------|----------|-------------|
| `path` | **Yes** | Path to PHP file or folder to test |
| `-- instructions` | No | Customize test generation |

**Examples:**
```bash
/acc-generate-test src/Domain/Order/Order.php
/acc-generate-test src/Domain/Order/ -- only unit tests, skip integration
/acc-generate-test src/Service/PaymentService.php -- include edge cases for null payments
/acc-generate-test src/ -- create builders for all entities
/acc-generate-test src/Application/ -- focus on happy path scenarios
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
/acc-audit-test <path> [level] [-- instructions]
```

| Argument | Required | Description |
|----------|----------|-------------|
| `path` | **Yes** | Path to tests folder or project |
| `level` | No | Audit depth: `quick`, `standard`, `deep` (default: standard) |
| `-- instructions` | No | Focus on specific quality aspects |

**Examples:**
```bash
/acc-audit-test ./tests
/acc-audit-test ./tests deep
/acc-audit-test ./tests quick -- check coverage gaps only
/acc-audit-test ./tests deep -- focus on test smells
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

## `/acc-bug-fix`

**Path:** `commands/acc-bug-fix.md`

Automated bug diagnosis, fix generation, and regression testing.

**Arguments:**
```
/acc-bug-fix <description|file:line|stack-trace> [-- instructions]
```

| Argument | Required | Description |
|----------|----------|-------------|
| `description` | **Yes** | Bug description, file:line reference, or stack trace |
| `-- instructions` | No | Focus or customize the fix process |

**Input Formats:**
- Text description: `"NullPointerException in OrderService::process()"`
- File:line reference: `src/Domain/Order.php:45 "off-by-one error"`
- Stack trace: Paste full trace
- Log file: `@storage/logs/error.log`

**Examples:**
```bash
/acc-bug-fix "NullPointerException in OrderService::process()"
/acc-bug-fix src/Domain/Order.php:45 "off-by-one error in loop"
/acc-bug-fix @storage/logs/laravel.log
/acc-bug-fix "Payment fails for amounts > 1000" -- focus on validation
/acc-bug-fix src/Service/Auth.php:78 -- skip tests
/acc-bug-fix "Race condition in inventory" -- dry-run
```

**Meta-Instructions:**
| Instruction | Effect |
|-------------|--------|
| `-- focus on <area>` | Prioritize specific code area |
| `-- skip tests` | Don't generate regression test |
| `-- dry-run` | Show fix without applying |
| `-- verbose` | Include detailed analysis |

**Workflow:**
1. **Parse Input** — Extract file, line, description
2. **Diagnose** — `acc-bug-hunter` categorizes bug (9 types)
3. **Fix** — `acc-bug-fixer` generates minimal, safe fix
4. **Test** — `acc-test-generator` creates regression test
5. **Apply** — Apply changes and run tests

**Output:**
- Bug category and severity
- Root cause analysis
- Diff of applied fix
- Regression test file
- Test execution results

---

## `/acc-audit-security`

**Path:** `commands/acc-audit-security.md`

Security audit covering OWASP Top 10 and PHP-specific vulnerabilities.

**Arguments:**
```
/acc-audit-security <path> [level] [-- instructions]
```

| Argument | Required | Description |
|----------|----------|-------------|
| `path` | **Yes** | Path to project or folder to audit |
| `level` | No | Audit depth: `quick`, `standard`, `deep` (default: standard) |
| `-- instructions` | No | Focus on specific security aspects |

**Examples:**
```bash
/acc-audit-security ./src
/acc-audit-security ./src deep
/acc-audit-security ./src deep -- focus on OWASP A01-A03
```

**Checks:**
- OWASP Top 10 (2021): Access Control, Crypto, Injection, etc.
- PHP-specific: `unserialize()`, `eval()`, `shell_exec()`, type juggling
- CWE identifiers and attack vectors
- Remediation code examples

---

## `/acc-audit-performance`

**Path:** `commands/acc-audit-performance.md`

Performance audit focusing on database, memory, and algorithm efficiency.

**Arguments:**
```
/acc-audit-performance <path> [level] [-- instructions]
```

| Argument | Required | Description |
|----------|----------|-------------|
| `path` | **Yes** | Path to project or folder to audit |
| `level` | No | Audit depth: `quick`, `standard`, `deep` (default: standard) |
| `-- instructions` | No | Focus on specific performance aspects |

**Examples:**
```bash
/acc-audit-performance ./src
/acc-audit-performance ./src deep
/acc-audit-performance ./src deep -- focus on N+1 queries
```

**Checks:**
- N+1 query problems
- Query efficiency (SELECT *, missing indexes)
- Memory issues (large arrays, missing generators)
- Caching opportunities
- Algorithm complexity (O(n²) patterns)
- Batch processing gaps
- Connection pool issues
- Serialization overhead

---

## `/acc-audit-patterns`

**Path:** `commands/acc-audit-patterns.md`

Design patterns audit with SOLID/GRASP compliance analysis.

**Arguments:**
```
/acc-audit-patterns <path> [level] [-- instructions]
```

| Argument | Required | Description |
|----------|----------|-------------|
| `path` | **Yes** | Path to project or folder to audit |
| `level` | No | Audit depth: `quick`, `standard`, `deep` (default: standard) |
| `-- instructions` | No | Focus on specific pattern categories |

**Examples:**
```bash
/acc-audit-patterns ./src
/acc-audit-patterns ./src deep
/acc-audit-patterns ./src deep -- focus on stability patterns
```

**Checks:**
- **Stability Patterns**: Circuit Breaker, Retry, Rate Limiter, Bulkhead
- **Behavioral Patterns**: Strategy, State, Chain of Responsibility, Decorator, Null Object, Template Method, Visitor, Iterator, Memento
- **GoF Structural Patterns**: Adapter, Facade, Proxy, Composite, Bridge, Flyweight
- **Creational Patterns**: Builder, Object Pool, Factory
- **Integration Patterns**: Outbox, Saga, ADR
- **SOLID Principles**: SRP, OCP, LSP, ISP, DIP
- **GRASP Principles**: Information Expert, Creator, Controller, etc.

---

## `/acc-generate-ddd`

**Path:** `commands/acc-generate-ddd.md`

Generate DDD components for PHP 8.5 with tests and proper layer placement.

**Arguments:**
```
/acc-generate-ddd <component-type> <ComponentName> [-- instructions]
```

| Argument | Required | Description |
|----------|----------|-------------|
| `component-type` | **Yes** | Component to generate (see list below) |
| `ComponentName` | **Yes** | Name for the component |
| `-- instructions` | No | Customize generation |

**Examples:**
```bash
/acc-generate-ddd entity Order
/acc-generate-ddd vo Email -- with DNS validation
/acc-generate-ddd aggregate ShoppingCart -- with CartItem child
/acc-generate-ddd command CreateOrder
/acc-generate-ddd query GetUserOrders -- with pagination
/acc-generate-ddd use-case ProcessPayment -- with retry logic
/acc-generate-ddd repository Order -- Doctrine implementation
/acc-generate-ddd dto OrderRequest -- for REST API
/acc-generate-ddd acl StripePayment
```

**Supported Components:**

| Component | Aliases | Layer |
|-----------|---------|-------|
| `entity` | `ent` | Domain |
| `value-object` | `vo`, `valueobject` | Domain |
| `aggregate` | `agg`, `aggregate-root` | Domain |
| `domain-event` | `event`, `de` | Domain |
| `repository` | `repo` | Domain + Infrastructure |
| `domain-service` | `service`, `ds` | Domain |
| `factory` | `fact` | Domain |
| `specification` | `spec` | Domain |
| `command` | `cmd` | Application |
| `query` | `qry` | Application |
| `use-case` | `usecase`, `uc` | Application |
| `dto` | `data-transfer` | Application |
| `acl` | `anti-corruption` | Infrastructure |

---

## `/acc-generate-psr`

**Path:** `commands/acc-generate-psr.md`

Generate PSR-compliant PHP components with tests.

**Arguments:**
```
/acc-generate-psr <psr-number> <ComponentName> [-- instructions]
```

| Argument | Required | Description |
|----------|----------|-------------|
| `psr-number` | **Yes** | PSR standard: `psr-3`, `psr-6`, `psr-7`, etc. |
| `ComponentName` | No | Name for the implementation |
| `-- instructions` | No | Customize generation |

**Examples:**
```bash
/acc-generate-psr psr-3 FileLogger
/acc-generate-psr psr-15 AuthMiddleware
/acc-generate-psr psr-6 RedisCache -- with TTL support
/acc-generate-psr psr-7 -- generate full HTTP stack
/acc-generate-psr psr-20 FrozenClock -- for testing
```

**Supported PSRs:**
- PSR-3 (Logger), PSR-6 (Cache), PSR-7 (HTTP Message)
- PSR-11 (Container), PSR-13 (Links), PSR-14 (Events)
- PSR-15 (Middleware), PSR-16 (Simple Cache)
- PSR-17 (HTTP Factories), PSR-18 (HTTP Client), PSR-20 (Clock)

---

## `/acc-generate-patterns`

**Path:** `commands/acc-generate-patterns.md`

Generate design pattern implementations with DI configuration.

**Arguments:**
```
/acc-generate-patterns <pattern-name> <ComponentName> [-- instructions]
```

| Argument | Required | Description |
|----------|----------|-------------|
| `pattern-name` | **Yes** | Pattern to generate (see list below) |
| `ComponentName` | **Yes** | Context/component name |
| `-- instructions` | No | Customize generation |

**Examples:**
```bash
/acc-generate-patterns circuit-breaker PaymentGateway
/acc-generate-patterns strategy PaymentProcessor
/acc-generate-patterns saga CheckoutWorkflow
/acc-generate-patterns builder UserProfile -- with validation
/acc-generate-patterns outbox Order -- with Doctrine integration
```

**Supported Patterns:**
- **Stability**: `circuit-breaker`, `retry`, `rate-limiter`, `bulkhead`
- **Behavioral**: `strategy`, `state`, `chain-of-responsibility`, `decorator`, `null-object`, `template-method`, `visitor`, `iterator`, `memento`
- **GoF Structural**: `adapter`, `facade`, `proxy`, `composite`, `bridge`, `flyweight`
- **Creational**: `builder`, `object-pool`, `factory`
- **Integration**: `outbox`, `saga`, `action`, `responder`

---

## `/acc-refactor`

**Path:** `commands/acc-refactor.md`

Guided refactoring with analysis and pattern application.

**Arguments:**
```
/acc-refactor <path> [-- instructions]
```

| Argument | Required | Description |
|----------|----------|-------------|
| `path` | **Yes** | Path to file or folder to refactor |
| `-- instructions` | No | Focus or customize refactoring |

**Examples:**
```bash
/acc-refactor ./src/Domain/OrderService.php
/acc-refactor ./src/Application -- focus on SOLID violations
/acc-refactor ./src -- extract value objects only
/acc-refactor ./src/Service -- analyze testability, skip style
/acc-refactor ./src -- quick wins only
```

**Analyzes:**
- Code smells (God Class, Long Method, Primitive Obsession, etc.)
- SOLID violations
- Testability issues (DI, side effects, coverage)
- Readability (naming, complexity, magic values)

**Provides:**
- Prioritized refactoring roadmap
- Generator commands for automated fixes
- Quick wins for immediate application
- Test coverage warnings
- Safety guidelines

---

## `/acc-ci-setup`

**Path:** `commands/acc-ci-setup.md`

Setup CI pipeline from scratch for PHP projects.

**Arguments:**
```
/acc-ci-setup <platform> [path] [-- instructions]
```

| Argument | Required | Description |
|----------|----------|-------------|
| `platform` | **Yes** | CI platform: `github` or `gitlab` |
| `path` | No | Project path (default: `./`) |
| `-- instructions` | No | Customize pipeline generation |

**Examples:**
```bash
/acc-ci-setup github
/acc-ci-setup gitlab ./my-project
/acc-ci-setup github -- include Docker, blue-green deploy
/acc-ci-setup gitlab -- focus on testing, high coverage
/acc-ci-setup github -- minimal, only lint and tests
```

**Generates:**
- CI workflow (`.github/workflows/ci.yml` or `.gitlab-ci.yml`)
- Static analysis configs (PHPStan, Psalm, PHP-CS-Fixer, DEPTRAC)
- Test configuration (PHPUnit)
- Docker files (if requested)
- Deployment configuration (if requested)

---

## `/acc-ci-fix`

**Path:** `commands/acc-ci-fix.md`

Diagnose and fix CI pipeline issues with interactive approval.

**Arguments:**
```
/acc-ci-fix <pipeline-url|log-file|description> [-- instructions]
```

| Argument | Required | Description |
|----------|----------|-------------|
| `pipeline-url` | No | GitHub/GitLab pipeline URL |
| `log-file` | No | Path to log file |
| `description` | No | Text description of the issue |
| `-- instructions` | No | Meta-instructions for fix process |

**Input Formats:**
- Pipeline URL: `https://github.com/org/repo/actions/runs/123`
- Log file: `./ci-error.log` or `@storage/logs/ci.log`
- Description: `"PHPStan fails with memory error"`

**Examples:**
```bash
# Interactive mode (default) - diagnoses, shows fix, asks approval
/acc-ci-fix "PHPStan memory exhausted"
/acc-ci-fix https://github.com/org/repo/actions/runs/12345
/acc-ci-fix ./ci-error.log

# Dry run - show diagnosis and fix without applying or asking
/acc-ci-fix ./ci.log -- dry-run

# Auto-apply - apply fix without asking (for scripts/CI)
/acc-ci-fix ./ci.log -- auto-apply

# With additional options
/acc-ci-fix ./logs/ci.txt -- verbose, skip-validation
/acc-ci-fix "Tests timeout" -- focus on Docker
```

**Meta-Instructions:**
| Instruction | Effect |
|-------------|--------|
| `-- dry-run` | Show diagnosis and fix without applying or asking |
| `-- auto-apply` | Apply fix without asking (for CI/scripts) |
| `-- skip-validation` | Don't run local syntax checks |
| `-- verbose` | Include detailed diagnosis output |
| `-- focus on <area>` | Prioritize specific area (tests, lint, docker) |

**Supported Issue Types:**

| Issue Type | Auto-Fix Support |
|------------|------------------|
| Memory exhausted | ✅ Full |
| Composer conflict | ✅ Full |
| PHPStan baseline | ✅ Full |
| Service not ready | ✅ Full |
| Docker build fail | ⚠️ Partial |
| Timeout | ✅ Full |
| Permission denied | ✅ Full |
| Cache miss | ✅ Full |
| PHP extension | ✅ Full |
| Env variable | ✅ Full |

**Workflow:**
1. **Parse Input** — URL, log file, or description
2. **Diagnose** — `acc-ci-debugger` identifies failure type and root cause
3. **Generate Fix** — `acc-ci-fixer` creates fix preview
4. **Ask Approval** — Unless `-- dry-run` or `-- auto-apply`
5. **Apply or Skip** — Based on user response
6. **Validate** — Run local syntax checks (unless `-- skip-validation`)
7. **Report** — Summary with diff and rollback instructions

---

## `/acc-ci-optimize`

**Path:** `commands/acc-ci-optimize.md`

Optimize CI/CD pipeline performance.

**Arguments:**
```
/acc-ci-optimize [path] [-- focus areas]
```

| Argument | Required | Description |
|----------|----------|-------------|
| `path` | No | Project path (default: `./`) |
| `-- focus areas` | No | Specific optimization targets |

**Examples:**
```bash
/acc-ci-optimize
/acc-ci-optimize -- focus on caching, reduce cache misses
/acc-ci-optimize -- optimize Docker build time
/acc-ci-optimize -- split tests into parallel jobs
/acc-ci-optimize ./my-project -- target 10 min total
```

**Optimizes:**
- Caching (Composer, Docker layers, artifacts)
- Parallelization (independent jobs, test splitting)
- Docker builds (multi-stage, layer ordering)
- Job dependencies (fail fast, timeouts)

**Output:**
- Before/after metrics comparison
- Specific changes to apply
- Estimated time savings

---

## `/acc-audit-ci`

**Path:** `commands/acc-audit-ci.md`

Comprehensive CI/CD audit for PHP projects.

**Arguments:**
```
/acc-audit-ci [path] [level] [-- instructions]
```

| Argument | Required | Description |
|----------|----------|-------------|
| `path` | No | Project path (default: `./`) |
| `level` | No | Audit depth: `quick`, `standard`, `deep` (default: standard) |
| `-- instructions` | No | Focus on specific audit areas |

**Examples:**
```bash
/acc-audit-ci
/acc-audit-ci deep
/acc-audit-ci ./ deep -- focus on security
```

**Audit Categories:**
- **Pipeline**: Stage organization, dependencies, triggers
- **Static Analysis**: PHPStan level, Psalm, DEPTRAC rules
- **Testing**: Coverage thresholds, test organization
- **Security**: Secrets handling, permissions, dependencies
- **Performance**: Caching efficiency, parallelization
- **Docker**: Image size, layer optimization, security
- **Deployment**: Zero-downtime, health checks, rollback

**Output:**
- Executive summary with scores
- Issues by severity (Critical/High/Medium/Low)
- Prioritized recommendations
- Action items

---

## `/acc-audit-docker`

**Path:** `commands/acc-audit-docker.md`

Comprehensive Docker configuration audit for PHP projects.

**Arguments:**
```
/acc-audit-docker [path] [level] [-- instructions]
```

| Argument | Required | Description |
|----------|----------|-------------|
| `path` | No | Project path (default: `./`) |
| `level` | No | Audit depth: `quick`, `standard`, `deep` (default: standard) |
| `-- instructions` | No | Focus on specific audit areas |

**Examples:**
```bash
/acc-audit-docker
/acc-audit-docker deep
/acc-audit-docker ./ deep -- focus on security
```

**Audit Categories:**
- **Dockerfile Architecture**: Multi-stage, layers, BuildKit
- **Base Images & Extensions**: Selection, pinning, compatibility
- **Docker Compose**: Services, health checks, networking
- **Performance**: Build time, image size, caching, PHP-FPM
- **Security**: Permissions, secrets, vulnerabilities
- **Production Readiness**: Health checks, shutdown, logging

---

## `/acc-generate-docker`

**Path:** `commands/acc-generate-docker.md`

Generate Docker configuration components for PHP projects.

**Arguments:**
```
/acc-generate-docker <component-type> [name] [-- instructions]
```

| Argument | Required | Description |
|----------|----------|-------------|
| `component-type` | **Yes** | Component to generate (see list below) |
| `name` | No | Project/service name |
| `-- instructions` | No | Customize generation |

**Examples:**
```bash
/acc-generate-docker full
/acc-generate-docker dockerfile -- with Symfony
/acc-generate-docker compose -- with PostgreSQL and Redis
/acc-generate-docker nginx -- with SSL
/acc-generate-docker entrypoint -- with migrations
```

**Supported Components:**

| Component | Aliases | Description |
|-----------|---------|-------------|
| `dockerfile` | `df` | Production multi-stage Dockerfile |
| `compose` | `dc` | Docker Compose configuration |
| `nginx` | `web` | Nginx reverse proxy config |
| `entrypoint` | `ep` | Container entrypoint script |
| `makefile` | `mk` | Docker Makefile commands |
| `env` | `environment` | Environment template |
| `healthcheck` | `hc` | Health check script |
| `full` | `all` | Complete Docker setup |

---

## `/acc-explain`

**Path:** `commands/acc-explain.md`

Explain code structure, business logic, data flows, and architecture patterns. Accepts file paths, directories, HTTP routes, or console commands.

**Arguments:**
```
/acc-explain <path|route|command> [mode] [-- instructions]
```

| Argument | Required | Description |
|----------|----------|-------------|
| `input` | **Yes** | File, directory, `.`, HTTP route (`GET /api/orders`), or console command (`app:process-payments`) |
| `mode` | No | `quick`, `deep`, `onboarding`, `business`, `qa` (auto-detected) |
| `-- instructions` | No | Focus area or specific question |

**Input Types (auto-detected):**

| Input | Pattern | Example |
|-------|---------|---------|
| HTTP route | `METHOD /path` | `GET /api/orders`, `POST /api/orders/{id}/status` |
| Console command | `namespace:name` | `app:process-payments`, `import:products` |
| File path | Existing file | `src/Domain/Order/Order.php` |
| Directory | Existing directory | `src/Domain/Order/` |
| Project root | `.` | `.` |

**Examples:**
```bash
# HTTP routes
/acc-explain GET /api/orders                               # Resolve route → explain handler
/acc-explain POST /api/orders/{id}/status deep             # Deep mode for route
/acc-explain DELETE /api/users/{id} -- explain cascade deletion

# Console commands
/acc-explain app:process-payments                          # Resolve command → explain handler
/acc-explain import:products -- explain data transformation pipeline

# File/directory (existing behavior)
/acc-explain src/Domain/Order/Order.php                    # Quick mode (auto)
/acc-explain src/Domain/Order/                             # Deep mode (auto)
/acc-explain .                                             # Onboarding mode (auto)
/acc-explain src/Payment business                          # Business mode
/acc-explain src/Domain qa -- how are discounts calculated? # QA mode
/acc-explain src/Domain/Order/ deep -- focus on state transitions
```

**Modes:**

| Mode | Auto-detect | Depth | Audience |
|------|-------------|-------|----------|
| `quick` | Single file, HTTP route, console command | 1-2 screens | Developer |
| `deep` | Directory | Full analysis + diagrams | Senior dev / Architect |
| `onboarding` | `.` (root) | Comprehensive guide | New team member |
| `business` | Explicit only | Non-technical | PM / Stakeholder |
| `qa` | Explicit only | Answer-focused | Any |

**Workflow:**
0. **Resolve** — If route/command input, resolve to handler file (Phase 0)
1. **Navigate** — Scan structure, find entry points, detect patterns
2. **Analyze** — Extract business logic, trace data flows, audit patterns
3. **Visualize** — Generate Mermaid diagrams (deep/onboarding/business)
4. **Present** — Aggregate results, suggest documentation

**Output:**
- Quick: Purpose, responsibilities, business rules, data flow, dependencies
- Deep: Full analysis with Mermaid diagrams, domain model, state machines
- Onboarding: Project guide with C4 diagrams, glossary, "How to navigate"
- Business: Non-technical overview with simple flow diagrams
- QA: Direct answer with code references

---

## Navigation

[← Back to README](../README.md) | [Agents →](agents.md) | [Skills](skills.md) | [Component Flow](component-flow.md) | [Quick Reference](quick-reference.md)
