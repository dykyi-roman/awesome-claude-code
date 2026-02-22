# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---
## [3.2.0] - 2026-02-22

### Added
- 6 new knowledge skills for system design: `consistency-patterns-knowledge`, `observability-knowledge`, `access-control-knowledge`, `scalability-knowledge`, `replication-sharding-knowledge`, `cloud-native-knowledge`
- 7 new analyzer skills: `check-idempotency`, `check-observability-coverage`, `check-access-control-model`, `check-scalability-readiness`, `check-distributed-locks`, `check-database-scaling`, `check-12-factor-compliance`
- 6 new generator skills: `create-idempotency-handler`, `create-structured-logger`, `create-access-control`, `create-distributed-lock`, `create-read-write-proxy`, `create-metrics-collector`
- `observability-auditor` agent — analyzes structured logging, correlation IDs, metrics endpoints, tracing, health checks (called by `architecture-auditor`)

### Changed
- Enhanced `caching-strategies-knowledge`: added cache stampede prevention (locking, XFetch, stale-while-revalidate), distributed cache coherence, write-back vs write-through comparison
- Enhanced `stability-patterns-knowledge`: added backpressure mechanisms, graceful degradation, adaptive retry with jitter, chaos engineering, health-based routing
- Enhanced `testing-knowledge`: added contract testing (Pact), chaos testing, load testing patterns, E2E distributed testing
- Enhanced `api-design-knowledge`: added cursor-based pagination, API rate limiting algorithms, gRPC for PHP, GraphQL N+1 prevention
- Enhanced `microservices-knowledge`: added Strangler Fig pattern, API Gateway aggregation, database-per-service trade-offs
- Enhanced `integration-auditor`: added `consistency-patterns-knowledge`, `check-idempotency`, `check-distributed-locks` skills; idempotency and distributed lock checks
- Enhanced `auth-reviewer`: added `access-control-knowledge`, `check-access-control-model` skills; access control model checks
- Enhanced `performance-reviewer`: added `scalability-knowledge`, `check-scalability-readiness`, `replication-sharding-knowledge`, `check-database-scaling` skills; scalability and database scaling categories
- Enhanced `architecture-auditor`: added 4th sub-auditor `acc:observability-auditor`, expanded cross-pattern analysis and report format
- Enhanced `structural-auditor`: added `cloud-native-knowledge`, `check-12-factor-compliance` skills; 12-Factor compliance checks
- Updated component counts: 26 commands, 68 agents, 283 skills
- Split `performance-reviewer` (19 skills) → `performance-reviewer` (9) + `resource-reviewer` (5) + `scalability-reviewer` (5) — eliminates God-Agent antipattern
- Split `structural-auditor` (16 skills) → `structural-auditor` (9) + `principles-auditor` (7) — separates architecture patterns from SOLID/GRASP principles
- Trimmed `integration-auditor` (16→11 skills) — removed 5 stability skills already covered by `stability-auditor`
- Changed `integration-auditor`, `gof-structural-auditor`, `stability-auditor`, `observability-auditor` model from `sonnet` to `opus` (sub-auditors require higher analysis quality)
- Updated `architecture-auditor` delegation: 4→5 sub-auditors (added `principles-auditor`)
- Updated `code-review-coordinator` HIGH level: added `resource-reviewer`, `scalability-reviewer`
- Updated `audit-performance` command: delegates to 3 parallel reviewers (performance + resource + scalability)

---
## [3.1.0] - 2026-02-21

### Added
- `framework-expert` agent — PHP framework knowledge expert for Symfony, Laravel, Yii, CodeIgniter, and no-framework projects
- 5 framework knowledge skills: `symfony-knowledge` (12 references), `laravel-knowledge` (11 references), `yii-knowledge` (11 references), `codeigniter-knowledge` (11 references), `no-framework-knowledge` (11 references)
- `messaging-generator` agent — Outbox, Saga, Correlation Context, Message Broker, Idempotent Consumer, Dead Letter Queue (9 skills)
- `api-infrastructure-generator` agent — ADR, API Versioning, Health Check, Unit of Work (7 skills)

### Changed
- Decomposed `integration-generator` (16 skills) → `messaging-generator` (9) + `api-infrastructure-generator` (7)
- `symfony-knowledge`: added security, messenger-advanced, workflow, event-system, infrastructure-components references; expanded antipatterns (+2) and ddd-integration
- `laravel-knowledge`: added security, queues-advanced, event-system, infrastructure-components references; expanded antipatterns (+2) and ddd-integration
- `yii-knowledge`: added security, event-system, queue, infrastructure-components references; expanded antipatterns (+2) and ddd-integration
- `codeigniter-knowledge`: added security, event-system, queue, infrastructure-components references; expanded antipatterns (+2) and ddd-integration
- `no-framework-knowledge`: added security, event-system, queue, infrastructure-components references; expanded antipatterns (+2) and ddd-integration
- `framework-expert` agent: added security/workflow/queue/facade detection patterns and report sections
- `structural-auditor`, `architecture-generator`: added framework delegation to `acc:framework-expert`
- `ddd-auditor`: added Phase 0 framework detection via `acc:framework-expert` delegation
- `architecture-generator`, `pattern-generator`: added "Progress Tracking" sections with TaskCreate/TaskUpdate phases
- Updated component counts: 26 commands, 64 agents, 264 skills

### Fixed
- Created 22 missing reference files across 7 skills: `ci-pipeline-knowledge` (3), `ci-tools-knowledge` (3), `deployment-knowledge` (3), `diagram-knowledge` (3), `documentation-knowledge` (5), `documentation-qa-knowledge` (3), `stability-patterns-knowledge` (2)
- `README.md`: added current version (v3.1.0)
- `docs/agents.md`: added `acc:ddd-auditor` to `framework-expert` Invoked By
- `docs/component-flow.md`: added `framework-expert` to dependency graph (ddd-auditor, structural-auditor)
- `docs/skills.md`, `docs/quick-reference.md`: unified skill category counts (100 analyzer, 93 generator, 7 optimizer, 10 template, 7 other)
- `docs/commands.md`: fixed navigation arrows (`<-`/`->` → `←`/`→`)
- `docs/quick-reference.md`: added version, fixed file tree explain-output-template double-count

### Removed
- `integration-generator` agent (replaced by `messaging-generator` + `api-infrastructure-generator`)

---
## [3.0.0] - 2026-02-16

### Breaking Changes
- **Distribution**: Migrated from Composer plugin to Claude Code marketplace plugin
- **Command syntax**: `/acc-*` → `/acc:*` (dash replaced with colon)
- **Installation**: `composer require` replaced with `/plugin marketplace add` + `/plugin install`
- **Removed**: Composer infrastructure (`src/`, `bin/`, `tests/`, `composer.json`, `.gitattributes`)

### Added
- `.claude-plugin/marketplace.json` — marketplace catalog
- `.claude-plugin/plugin.json` — plugin manifest
- `hooks/hooks.json` — PHP syntax check hook (was in `.claude/settings.json`)

### Changed
- Components moved to root: `commands/`, `agents/`, `skills/` (was `.claude/commands/`, `.claude/agents/`, `.claude/skills/`)
- `acc-` prefix removed from filenames (e.g., `acc-audit-ddd.md` → `audit-ddd.md`)
- Agent `name:` frontmatter uses bare names (e.g., `name: architecture-auditor`)
- Agent `skills:` frontmatter uses bare names (e.g., `skills: ddd-knowledge, solid-knowledge`)
- `subagent_type` references use `acc:` namespace (e.g., `subagent_type="acc:ddd-auditor"`)
- Slash commands use colon syntax: `/acc:audit-ddd`, `/acc:code-review`, etc.
- Makefile updated: removed `test`, `test-clear`, `upgrade` targets; paths point to root `commands/`, `agents/`, `skills/`
- All documentation updated for new paths and command syntax
- Component counts unchanged: 26 commands, 62 agents, 259 skills

### Fixed
- `.claude/settings.json` PostToolUse hook: matcher `Write` → `Write|Edit` to match `hooks/hooks.json`
- `.claude/settings.json` PostToolUse hook: env var `$ACC_TOOL_FILE_PATH` → `$CLAUDE_FILE_PATHS` (correct Claude Code variable)

### Removed
- `src/ComposerPlugin.php` — Composer plugin class
- `bin/acc` — CLI upgrade tool
- `tests/` — Docker-based test environment
- `composer.json` — Composer package manifest
- `.gitattributes` — Git export attributes

## [2.13.0] - 2026-02-15

### Added
- Added support for PHP 8.4
- `acc-cqrs-generator` agent — CQRS/ES component generator (8 skills)
- `acc-create-unit-of-work` — Unit of Work with identity map, savepoints, event collector
- `acc-create-message-broker-adapter` — unified interface for RabbitMQ, Kafka, SQS, InMemory
- `acc-create-idempotent-consumer` — message deduplication with Database/Redis stores
- `acc-create-dead-letter-queue` — DLQ handler with retry strategy and failure classifier
- `acc-create-timeout` — timeout executors (Signal/Stream/Null) with PSR-15 middleware
- `acc-microservices-knowledge` — decomposition, communication, API gateway, antipatterns
- `acc-api-design-knowledge` — REST, Richardson Model, RFC 7807, pagination, error handling
- `acc-message-queue-knowledge` — RabbitMQ/Kafka/SQS/Redis Streams comparison, delivery guarantees
- `acc-caching-strategies-knowledge` — Cache-Aside/Read-Through/Write-Behind, invalidation, stampede prevention

### Changed
- Decomposed `acc-ddd-generator` → `acc-ddd-generator` (11 skills) + `acc-cqrs-generator` (8 skills)
- Changed `acc-ddd-generator` model from `opus` to `sonnet`
- Updated 5 agents routing: `acc-generate-ddd`, `acc-architecture-generator`, `acc-architecture-auditor`, `acc-ddd-auditor`, `acc-refactor-coordinator`
- Updated `acc-integration-generator`: +4 skills (Unit of Work, Message Broker, Idempotent Consumer, Dead Letter Queue)
- Updated `acc-stability-generator`: +1 skill (Timeout)
- Updated `acc-pattern-generator` coordinator and `acc-generate-patterns` command for 5 new patterns
- Updated component counts: 26 commands, 62 agents, 259 skills

## [2.12.0] - 2026-02-14

### Added
- `acc-create-event-store` skill — generates Event Store infrastructure: StoredEvent, EventStream, EventStoreInterface, DoctrineEventStore with optimistic locking and ConcurrencyException
- `acc-create-snapshot` skill — generates Snapshot infrastructure for event sourcing performance: Snapshot VO, SnapshotStoreInterface, SnapshotStrategy, AggregateSnapshotter, DoctrineSnapshotStore
- `acc-create-api-versioning` skill — generates API Versioning: ApiVersion VO, version resolvers (URI prefix, Accept header, query param, composite), VersionMiddleware, DeprecationHeaderMiddleware
- `acc-create-health-check` skill — generates Health Check endpoints: HealthCheckInterface, HealthStatus enum, HealthCheckResult, checkers (Database, Redis, RabbitMQ), HealthCheckRunner, HealthCheckAction
- `acc-create-cache-aside` skill — generates Cache-Aside pattern: CacheAsideExecutor with PSR-16, stampede protection via distributed locking, CacheInvalidator with tag-based invalidation
- Enhanced `acc-create-read-model` with event sourcing projections reference: ProjectionRunner, ProjectionVersion, ProjectionCheckpoint, async ProjectionWorker

### Changed
- Updated component counts: 26 commands, 61 agents, 250 skills
- Slimmed `acc-generate-ddd` command (418→119 lines) — extracted verbose examples to `acc-ddd-knowledge/references/generation-examples.md`
- Slimmed `acc-ci-fix` command (391→287 lines) — extracted workflow diagram and verbose examples to `acc-generate-ci-fix/references/workflow.md`
- Reduced `acc-psr-generator` skills (14→11) — removed knowledge skills (kept in `acc-psr-auditor`)
- Slimmed 5 oversized agents to <200 lines: `acc-integration-auditor` (383→151), `acc-behavioral-auditor` (358→153), `acc-performance-reviewer` (333→87), `acc-stability-auditor` (326→182), `acc-creational-auditor` (321→173)
- Extracted references for 5 near-limit skills: `acc-create-github-actions` (500→143), `acc-create-entity` (478→144), `acc-check-connection-pool` (472→99), `acc-detect-ci-antipatterns` (464→110), `acc-check-encapsulation` (459→130)

## [2.11.0] - 2026-02-11

### Added
- `acc-create-correlation-context` skill — generates Correlation ID propagation infrastructure: CorrelationId value object, CorrelationContext holder, PSR-15 middleware, Monolog processor, message bus stamp, with unit tests and framework integration examples
- `acc-discover-project-logs` skill — auto-discovers log files across PHP frameworks (Laravel, Symfony, CodeIgniter, Yii2/Yii3), infrastructure (PHP-FPM, Docker, Nginx), and CI/CD build artifacts with scoring and prioritization
- `acc-analyze-php-logs` skill — parses PHP logs in PSR-3/Monolog (JSON + line), Laravel, Symfony, plain error_log, and PHP-FPM slow log formats; extracts exceptions, stack traces, request context, error frequency, and correlates related errors
- Log discovery integrated into 7 agents: `acc-bug-hunter` (+2 skills), `acc-docker-debugger-agent` (+2 skills), `acc-ci-debugger` (+1 skill), `acc-bug-fixer` (+1 skill), `acc-performance-reviewer` (+1 skill), `acc-data-flow-analyst` (+1 skill), `acc-docker-coordinator` (updated delegation prompt)
- `acc-bug-fix` command: new `-- scan-logs` / `-- no-logs` meta-instructions and auto-discover input type with AskUserQuestion fallback
- `acc-ci-fix` command: new `-- scan-logs` meta-instruction and auto-discover CI logs input type with AskUserQuestion fallback
- 4 security specialist agents: `acc-injection-reviewer` (A03/A10/A08), `acc-auth-reviewer` (A01/A07), `acc-data-security-reviewer` (A02/A09/A05), `acc-design-security-reviewer` (A04/A06)
- 3 deny rules in `settings.json`: `git branch -D`, `git checkout .`, `git rebase`

### Changed
- `acc-security-reviewer` transformed from specialist (21 skills, sonnet) to coordinator (model: opus, delegates to 4 specialist agents via Task tool)
- Unified `level` parameter across all 11 audit commands: `level` is now an explicit optional positional parameter (`quick|standard|deep`, default: `standard`) instead of hidden inside meta-instructions (`-- level:deep`). Backward-compatible: `level:*` in meta-instructions still works.
- Updated component counts: 26 commands, 61 agents, 245 skills

## [2.10.0] - 2026-02-09

### Added
- `.claude/rules/` directory with 3 conditional rules: `component-creation.md`, `versioning.md`, `troubleshooting.md` — loaded only when matching files are involved, saving context
- `acc-cqrs-auditor` agent — dedicated CQRS/ES/EDA patterns auditor (split from `acc-behavioral-auditor`)
- Creational auditor skills (+3): `acc-check-singleton-antipattern` (Singleton anti-pattern detection), `acc-check-abstract-factory` (Abstract Factory audit), `acc-create-prototype` (Prototype pattern generator)
- Stability auditor skills (+3): `acc-check-timeout-strategy` (timeout configuration audit), `acc-check-cascading-failures` (cascading failure detection), `acc-check-fallback-strategy` (fallback/graceful degradation audit)
- DDD auditor skills (+3): `acc-check-aggregate-consistency` (aggregate rules audit), `acc-check-cqrs-alignment` (CQRS/ES alignment), `acc-check-context-communication` (Context Map patterns)
- Documentation auditor skills (+3): `acc-check-doc-links` (link validation), `acc-check-doc-examples` (code example verification), `acc-check-version-consistency` (version sync audit)
- Security reviewer skills (+6): `acc-check-insecure-design` (A04:2021), `acc-check-logging-failures` (A09:2021), `acc-check-secure-headers` (CSP/HSTS/X-Frame), `acc-check-cors-security` (CORS misconfiguration), `acc-check-mass-assignment` (mass assignment), `acc-check-type-juggling` (PHP type juggling)
- Performance reviewer skills (+3): `acc-check-index-usage` (missing DB indexes), `acc-check-async-patterns` (sync ops that should be async), `acc-check-file-io` (file I/O patterns)

### Changed

#### Audit System
- All 11 audit commands upgraded to `model: opus` (was sonnet for psr, test, security, performance)
- Unified severity system 🔴🟠🟡🟢 across all 11 audit commands (was 5 different icon sets)
- All 11 audit commands now support `level:quick`, `level:standard`, `level:deep` via meta-instructions
- All 11 audit commands now have Meta-Instructions Guide tables (was 2/11)
- All 11 audit commands now have Pre-flight checks (was 8/11)
- `acc-audit-psr` rewritten: 89 → 220 lines with Pre-flight Check, Audit Levels, Severity, Meta-Instructions Guide, full Expected Output template
- `acc-audit-test` rewritten: 137 → 230 lines with Pre-flight Check, Audit Levels, Severity, Meta-Instructions Guide, full Expected Output template
- `acc-audit-psr` and `acc-audit-test` commands expanded `allowed-tools` from `Task` to `Read, Grep, Glob, Bash, Task`

#### Agents
- `acc-behavioral-auditor` split: CQRS/ES/EDA → new `acc-cqrs-auditor` (8 skills), GoF behavioral remains (11 skills, was 17+458 lines)
- `acc-docker-production-agent` slimmed: 410 → ~200 lines, extracted inline templates to skill references
- `acc-find-sql-injection` merged into `acc-check-sql-injection` (>70% content overlap), `acc-bug-hunter` updated
- `acc-pattern-auditor` and `acc-architecture-auditor` coordinators updated delegation tables for CQRS split
- `acc-creational-auditor` expanded: 3 → 6 skills, added Abstract Factory, Singleton anti-pattern, Prototype phases
- `acc-stability-auditor` expanded: 5 → 8 skills, added Timeout, Cascading Failures, Fallback phases
- `acc-ddd-auditor` expanded: 5 → 8 skills, added Aggregate Consistency, CQRS Alignment, Context Communication phases
- `acc-documentation-auditor` expanded: 3 → 6 skills, added link validation, example verification, version consistency
- `acc-security-reviewer` expanded: 14 → 20 skills, added OWASP A04 Insecure Design, A09 Logging Failures, Secure Headers, CORS, Mass Assignment, Type Juggling
- `acc-performance-reviewer` expanded: 10 → 13 skills, added Index Usage, Async Patterns, File I/O
- `acc-pattern-auditor` coordinator updated delegation table (stability 5→8, creational 3→6)

#### Progress Tracking
- 5 specialist agents (`acc-security-reviewer`, `acc-performance-reviewer`, `acc-psr-auditor`, `acc-test-auditor`, `acc-documentation-auditor`) upgraded with TaskCreate/TaskUpdate progress tracking (3 phases: Scan → Analyze → Report)
- 6 sub-auditors (`acc-behavioral-auditor`, `acc-cqrs-auditor`, `acc-creational-auditor`, `acc-gof-structural-auditor`, `acc-structural-auditor`, `acc-integration-auditor`, `acc-stability-auditor`) upgraded with TaskCreate/TaskUpdate progress tracking

#### Skills & CLAUDE.md
- 10 analyzer skills expanded with "When This Is Acceptable" false-positive guidance: `acc-check-method-length`, `acc-check-class-length`, `acc-detect-n-plus-one`, `acc-analyze-solid-violations`, `acc-detect-code-smells`, `acc-check-input-validation`, `acc-check-sql-injection`, `acc-detect-memory-issues`, `acc-check-caching-strategy`, `acc-check-output-encoding`
- `CLAUDE.md` slimmed from 147 to ~80 lines — extracted component creation, versioning, and troubleshooting sections into conditional rules
- Updated component counts: 26 commands, 57 agents, 242 skills
---

## [2.9.0] - 2026-02-08

### Added
- `/acc-explain` command — code explanation with 5 modes (quick, deep, onboarding, business, qa), accepts files, directories, HTTP routes, console commands
- Explain agents (4): explain-coordinator, codebase-navigator, business-logic-analyst, data-flow-analyst
- Explain skills (12): codebase scanning, entry-point resolution, architecture detection, business rules/processes/domain extraction, state machines, request lifecycle tracing, data transformation, async flows, output templates
- GoF Structural patterns (6): Adapter, Facade, Proxy, Composite, Bridge, Flyweight — auditor + generator agents, 6 skills with templates/examples
- GoF Behavioral patterns (4): Template Method, Visitor, Iterator, Memento — 4 skills with templates/examples

### Changed
- `acc-behavioral-generator/auditor` expanded with 4 new GoF behavioral patterns
- `acc-pattern-generator/auditor` coordinators now delegate to 5 sub-agents (added `acc-gof-structural-*`)
- `/acc-generate-patterns` supports 26 patterns (was 16), `/acc-audit-patterns` audits GoF structural category
- `docs/mcp.md` expanded with 6 MCP server configurations: Redis, RabbitMQ, Elasticsearch, Kafka, GitHub, Docker Hub
- Updated component counts: 26 commands, 56 agents, 222 skills

---

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

[Unreleased]: https://github.com/dykyi-roman/awesome-claude-code/compare/v3.2.0...HEAD
[3.2.0]: https://github.com/dykyi-roman/awesome-claude-code/compare/v3.1.0...v3.2.0
[3.1.0]: https://github.com/dykyi-roman/awesome-claude-code/compare/v3.0.0...v3.1.0
[3.0.0]: https://github.com/dykyi-roman/awesome-claude-code/compare/v2.13.0...v3.0.0
[2.13.0]: https://github.com/dykyi-roman/awesome-claude-code/compare/v2.12.0...v2.13.0
[2.12.0]: https://github.com/dykyi-roman/awesome-claude-code/compare/v2.11.0...v2.12.0
[2.11.0]: https://github.com/dykyi-roman/awesome-claude-code/compare/v2.10.0...v2.11.0
[2.10.0]: https://github.com/dykyi-roman/awesome-claude-code/compare/v2.9.0...v2.10.0
[2.9.0]: https://github.com/dykyi-roman/awesome-claude-code/compare/v2.8.0...v2.9.0
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
