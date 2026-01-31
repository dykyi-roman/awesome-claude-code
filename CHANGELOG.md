# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.0.0] - 2025-01-31

### Added

#### Commands
- `/acc-architecture-audit` - comprehensive multi-pattern architecture audit
- `/acc-ddd-audit` - DDD compliance analysis for PHP projects

#### Agents
- `acc-architecture-auditor` - multi-pattern architecture auditor (DDD, CQRS, Clean, Hexagonal, Layered, EDA, Event Sourcing)
- `acc-ddd-auditor` - specialized DDD compliance auditor
- `acc-ddd-generator` - creates DDD and architecture components

#### Knowledge Skills (for audits)
- `acc-ddd-knowledge` - DDD patterns, antipatterns, PHP guidelines
- `acc-cqrs-knowledge` - CQRS patterns, command/query separation
- `acc-clean-arch-knowledge` - Clean Architecture, dependency rules
- `acc-hexagonal-knowledge` - Hexagonal/Ports & Adapters patterns
- `acc-layer-arch-knowledge` - Layered Architecture, DTO patterns
- `acc-event-sourcing-knowledge` - Event Sourcing, projections, snapshots
- `acc-eda-knowledge` - Event-Driven Architecture, messaging, sagas

#### Generator Skills (for code generation)
- `acc-create-value-object` - generates DDD Value Objects with tests
- `acc-create-entity` - generates DDD Entities with tests
- `acc-create-aggregate` - generates DDD Aggregates with tests
- `acc-create-domain-event` - generates Domain Events with tests
- `acc-create-repository` - generates Repository interfaces and stubs
- `acc-create-command` - generates CQRS Commands and Handlers
- `acc-create-query` - generates CQRS Queries and Handlers
- `acc-create-use-case` - generates Application Use Cases

### Changed
- Renamed `/commit` to `/acc-commit` for consistency
- Renamed `/claude-code` to `/acc-claude-code` for consistency
- Renamed `claude-code-expert` to `acc-claude-code-expert` for consistency
- Renamed `claude-code-knowledge` to `acc-claude-code-knowledge` for consistency
- Removed Co-Authored-By from commit messages in `/acc-commit`

## [1.0.0] - 2025-01-31

### Added

- Initial release
- Composer plugin for auto-copying Claude Code components
- Command `/acc-claude-code` - interactive wizard for creating commands, agents, skills, hooks
- Command `/acc-commit` - auto-generate commit message and push
- Agent `acc-claude-code-expert` - expert in Claude Code architecture
- Skill `acc-claude-code-knowledge` - knowledge base for formats and patterns
- Comprehensive documentation in `.claude/README.md`

[Unreleased]: https://github.com/dykyi-roman/awesome-claude-code/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/dykyi-roman/awesome-claude-code/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/dykyi-roman/awesome-claude-code/releases/tag/v1.0.0
