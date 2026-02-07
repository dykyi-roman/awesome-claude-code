# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.8.0] - 2026-02-07

### Added
- Docker Expert System for PHP (2 commands + 1 coordinator + 7 agents + 42 skills)
- Enhanced `acc-claude-code-knowledge` from ~45% to ~95% coverage with 6 reference files:
  - `hooks-reference.md` — all 12 hook events, 3 types, matchers, I/O, exit codes
  - `skills-advanced.md` — context:fork, agent, hooks, model, invocation control
  - `subagents-advanced.md` — memory, hooks, disallowedTools, background, resume
  - `memory-and-rules.md` — CLAUDE.md hierarchy, rules/, @imports, paths frontmatter
  - `plugins-reference.md` — plugin structure, manifest, marketplace, migration
  - `settings-and-permissions.md` — full settings schema, sandbox, permissions, env vars
- New SKILL.md sections: Memory, Plugins, Permissions, MCP, Settings, Decision Framework, Context Costs
- New agent fields documented: `disallowedTools`, `hooks`, `memory`, `permissionMode` (6 modes)
- New skill fields documented: `context`, `agent`, `hooks`, `model`, `!`command`` injection
- Plugin and rules creation in `/acc-generate-claude-component`
- Memory/rules, plugin, and hooks comprehensive audit in `/acc-audit-claude-components`

### Changed
- `acc-claude-code-expert` agent updated with Memory, Plugins, Permissions, Rules knowledge
- `/acc-generate-claude-component` expanded from 4 to 6 component types (+ rule, plugin)
- `/acc-audit-claude-components` enhanced with memory/rules, plugin, hooks, permissions quality criteria
- `/acc-audit-docker` command - Docker configuration audit (Dockerfile, Compose, security, performance)
- `/acc-generate-docker` command - Docker component generation (dockerfile, compose, nginx, entrypoint, makefile, env, healthcheck, full)
- `acc-docker-coordinator` agent - orchestrates Docker audit and generation operations
- Docker specialist agents (7): architect, image-builder, compose, performance, security, debugger, production
- Docker knowledge skills (12): core, multistage, base-images, php-extensions, compose, networking, security, buildkit, production, troubleshooting, orchestration, scanning
- Docker analyzer skills (12): build-errors, runtime-errors, image-size, security, secrets, user-permissions, compose-config, production-readiness, antipatterns, layer-efficiency, php-config, healthcheck
- Docker creator skills (12): dockerfile-production, dockerfile-dev, dockerignore, compose-dev, compose-production, php-config, healthcheck, entrypoint, nginx-config, makefile, env-template, supervisor-config
- Docker optimizer skills (6): build-time, image-size, php-fpm, compose-resources, opcache, startup
- Updated component counts: 25 commands, 50 agents, 200 skills

### Changed
- Renamed `/acc-write-test` → `/acc-generate-test` for consistent `generate-` verb across all generation commands
- Renamed `/acc-write-documentation` → `/acc-generate-documentation`
- Renamed `/acc-write-claude-component` → `/acc-generate-claude-component`

---

## [2.7.0] - 2026-02-06

### Added
- `/acc-generate-ddd` command - direct DDD component generation (13 components)
- `/acc-generate-psr` command - direct PSR component generation (11 PSR implementations)
- `/acc-generate-patterns` command - direct design pattern generation (16 patterns)
- `/acc-audit-security` command - standalone security audit (OWASP Top 10)
- `/acc-audit-performance` command - standalone performance audit
- `/acc-audit-patterns` command - design patterns audit
- `/acc-refactor` command - guided refactoring workflow
- CI/CD commands (4): `/acc-ci-setup`, `/acc-ci-fix`, `/acc-ci-optimize`, `/acc-audit-ci`
- CI/CD agents (10): ci-coordinator, pipeline-architect, ci-debugger, ci-fixer, pipeline-optimizer, ci-security-agent, docker-agent, deployment-agent, static-analysis-agent, test-pipeline-agent
- CI/CD skills (18): knowledge (3), config generators (6), docker (2), deployment (2), analyzers (4), fix generator (1)
- `acc-task-progress-knowledge` skill - TaskCreate pattern guidelines for coordinator progress tracking
- Progress tracking (TaskCreate/TaskUpdate) in 7 coordinator agents for user visibility
- TaskCreate guidelines in project CLAUDE.md and global ~/.claude/CLAUDE.md
- Coordinator progress tracking check in `/acc-audit-claude-components`
- Coordinator creation guidelines in `/acc-generate-claude-component`
- Updated component counts: 23 commands, 42 agents, 158 skills

---

## [2.6.0] - 2026-02-05

### Added
- `bin/acc` CLI tool for managing Claude components (`acc upgrade`)
- `/acc-bug-fix` command - automated bug diagnosis, fix generation, and testing
- `acc-bug-fix-coordinator` agent - orchestrates bug diagnosis → fix → test workflow
- `acc-bug-fixer` agent - generates safe, minimal bug fixes (11 skills)
- Bug fix skills (5): knowledge, root-cause-finder, impact-analyzer, fix-generator, regression-preventer
- Security skills (5): SSRF, command injection, deserialization, XXE, path traversal (OWASP 10/10)
- Performance skills (2): connection-pool, serialization

### Changed
- `acc-security-reviewer`: 9 → 14 skills (full OWASP Top 10)
- `acc-performance-reviewer`: 8 → 10 skills

## [2.5.0] - 2026-02-04

### Added
- `/acc-code-review` command - multi-level code review with git diff analysis
- Review agents (6): code-review-coordinator, bug-hunter, security-reviewer, performance-reviewer, readability-reviewer, testability-reviewer
- Bug detection skills (9): logic-errors, null-pointer, boundary, race-conditions, resource-leaks, exception, type, sql-injection, infinite-loops
- Security review skills (9): input-validation, output-encoding, authentication, authorization, sensitive-data, csrf, crypto, dependencies, sql-injection
- Performance skills (8): n-plus-one, query-efficiency, memory, caching, loops, lazy-loading, batch-processing, complexity
- Readability skills (9): naming, code-style, method-length, class-length, nesting, comments, magic-values, consistency, simplification
- Testability skills (5): dependency-injection, pure-functions, side-effects, test-quality, testability-improvements

## [2.4.0] - 2026-02-03

### Added
- `/acc-generate-test` - generate tests for PHP file/folder
- `/acc-audit-test` - audit test quality
- `/acc-generate-documentation` - generate documentation
- `/acc-audit-documentation` - audit documentation quality
- Auditor agents (6): structural, behavioral, integration, stability, creational, psr
- Generator agents (4): stability, behavioral, creational, integration
- Test agents (2): test-auditor, test-generator
- Documentation agents (3): documentation-writer, documentation-auditor, diagram-designer
- Knowledge skills (4): testing, documentation, diagram, documentation-qa
- Analyzer skills (8): test-coverage, test-smells, code-smells, bounded-contexts, immutability, leaky-abstractions, encapsulation, coupling-cohesion
- Generator skills (5): unit-test, integration-test, test-builder, mock-repository, test-double
- Template skills (9): readme, architecture-doc, adr, api-doc, getting-started, troubleshooting, code-examples, mermaid, changelog
- Hooks (10): auto-format, strict-types, protect-vendor, syntax-check, auto-tests, final-domain, file-size, no-direct-commits, protect-migrations, test-without-source
- Meta-instructions support via `--` separator for all commands

### Changed
- Decomposed `acc-architecture-auditor` to coordinator pattern (delegates to 3 auditors)
- Refactored `acc-pattern-auditor` and `acc-pattern-generator` to coordinator patterns
- Renamed `/acc-claude-code` to `/acc-generate-claude-component`

## [2.3.0] - 2026-02-02

### Added
- `/acc-audit-psr` command - PSR compliance audit
- `acc-psr-generator` agent (11 skills)
- Knowledge skills (6): SOLID, GRASP, PSR coding style, PSR autoloading, PSR overview, ADR
- Analyzer skill: SOLID violations
- PSR generator skills (13): PSR-3, 6, 7, 11, 13, 14, 15, 16, 17, 18, 20, action, responder
- Utility skills (2): DI container, mediator

## [2.2.0] - 2026-01-31

### Added
- `/acc-audit-claude-code` command
- Agents (3): architecture-generator, pattern-auditor, pattern-generator
- Knowledge skills (3): outbox-pattern, saga-pattern, stability-patterns
- Generator skills (20): dto, specification, factory, domain-service, outbox, saga, circuit-breaker, retry, rate-limiter, bulkhead, strategy, state, decorator, chain-of-responsibility, builder, null-object, object-pool, anti-corruption-layer, read-model, policy

### Changed
- Refactored 22 skills to use `references/` folder structure

## [2.1.0] - 2026-01-30

### Added
- `/acc-audit-architecture` command - multi-pattern architecture audit
- `/acc-audit-ddd` command - DDD compliance analysis
- Agents (3): architecture-auditor, ddd-auditor, ddd-generator
- Knowledge skills (7): DDD, CQRS, Clean Architecture, Hexagonal, Layered, Event Sourcing, EDA
- Generator skills (8): value-object, entity, aggregate, domain-event, repository, command, query, use-case

## [2.0.0] - 2026-01-29

### Added
- Composer plugin for auto-copying Claude Code components
- `/acc-generate-claude-component` command - interactive wizard
- `/acc-commit` command - auto-generate commit message
- `acc-claude-code-expert` agent
- `acc-claude-code-knowledge` skill

## [1.0.0] - 2026-01-28

### Added
- Initial release
- Project structure and Composer package setup

[Unreleased]: https://github.com/dykyi-roman/awesome-claude-code/compare/v2.8.0...HEAD
[2.8.0]: https://github.com/dykyi-roman/awesome-claude-code/compare/v2.7.0...v2.8.0
[2.7.0]: https://github.com/dykyi-roman/awesome-claude-code/compare/v2.6.0...v2.7.0
[2.6.0]: https://github.com/dykyi-roman/awesome-claude-code/compare/v2.5.0...v2.6.0
[2.5.0]: https://github.com/dykyi-roman/awesome-claude-code/compare/v2.4.0...v2.5.0
[2.4.0]: https://github.com/dykyi-roman/awesome-claude-code/compare/v2.3.0...v2.4.0
[2.3.0]: https://github.com/dykyi-roman/awesome-claude-code/compare/v2.2.0...v2.3.0
[2.2.0]: https://github.com/dykyi-roman/awesome-claude-code/compare/v2.1.0...v2.2.0
[2.1.0]: https://github.com/dykyi-roman/awesome-claude-code/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/dykyi-roman/awesome-claude-code/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/dykyi-roman/awesome-claude-code/releases/tag/v1.0.0
