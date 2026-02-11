---
description: Comprehensive audit of .claude folder. Checks structure, quality, cross-references, antipatterns, resource usage, behavior verification, context alignment, semantic fit, God-Agent detection, skill responsibility analysis, domain boundaries, memory/rules, plugins, hooks, and refactoring recommendations.
allowed-tools: Read, Glob, Grep, Bash
model: opus
argument-hint: [level] [-- meta-instructions]
---

# Claude Code Configuration Audit

Perform a comprehensive audit of the `.claude/` folder in the current project.

## Input Parsing

Parse `$ARGUMENTS` to extract level and optional meta-instructions:

```
Format: [level] [-- <meta-instructions>]

Arguments:
- level: Audit depth - quick|standard|deep (optional, default: standard)
- -- meta-instructions: Additional focus areas or filters (optional)

Examples:
- /acc-audit-claude-components
- /acc-audit-claude-components deep
- /acc-audit-claude-components quick
- /acc-audit-claude-components -- focus on God-Agent detection
- /acc-audit-claude-components deep -- check only commands
- /acc-audit-claude-components -- level:deep (backward compatible)
```

**Parsing rules:**
1. Split `$ARGUMENTS` by ` -- ` (space-dash-dash-space)
2. First part = positional arguments, Second part = meta-instructions
3. If first positional argument is `quick|standard|deep` → this is level
4. Also accept `level:quick|standard|deep` in meta-instructions (backward compatibility)
5. Priority: positional > meta-instruction > default (`standard`)

If meta-instructions provided, adjust audit to:
- Focus on specific component types (commands/agents/skills)
- Prioritize specific checks (God-Agent, cross-references, etc.)
- Skip certain analysis phases

## Pre-flight Check

1. Check if `.claude/` folder exists in the current working directory
2. If missing, skip to **Missing Configuration** section

## Audit Process

### Step 1: Scan Structure

Discover all components:

```
.claude/
├── commands/           # Slash commands (*.md)
├── agents/             # Custom agents (*.md)
├── skills/             # Skills (name/SKILL.md)
├── plans/              # Plan files
├── settings.json       # Project settings
├── settings.local.json # Local settings (gitignored)
├── CLAUDE.md           # Project instructions
└── README.md           # Documentation
```

Use Glob to find:
- `.claude/commands/*.md`
- `.claude/agents/*.md`
- `.claude/skills/*/SKILL.md`
- `.claude/settings.json`
- `.claude/settings.local.json`
- `.claude/CLAUDE.md`
- `.claude/rules/*.md`
- `.claude-plugin/plugin.json`
- `CLAUDE.md` (project root)
- `CLAUDE.local.md` (project root)

### Step 2: Analyze Each Component

For each file found, evaluate against quality criteria:

#### Commands Quality Criteria

| Criterion | ✅ Good | ⚠️ Improve | ❌ Problem |
|-----------|---------|------------|------------|
| YAML frontmatter | Valid, all fields | Missing optional fields | Invalid/missing |
| Description | Clear, specific | Too generic | Missing |
| Instructions | Step-by-step, clear | Vague steps | No instructions |
| $ARGUMENTS handling | Documented, validated | Used but not documented | Ignored |
| Tool restrictions | Appropriate for task | Too permissive | Missing when needed |

#### Agents Quality Criteria

| Criterion | ✅ Good | ⚠️ Improve | ❌ Problem |
|-----------|---------|------------|------------|
| YAML frontmatter | name, description, tools | Missing optional | Invalid/missing |
| Name | Lowercase, hyphenated | Inconsistent casing | Invalid characters |
| Description | Specific purpose | Too generic | Missing |
| Tool restrictions | Minimal needed set | Missing restrictions | Overly broad |
| Skills reference | Links to skills | No skill usage | Broken references |
| disallowedTools | Used when most tools needed except few | Not used, tools list too long | Conflicts with tools list |
| hooks field | Valid scoped hooks with matchers | Hooks without matchers | Invalid hook events |
| memory field | Appropriate scope (user/project/local) | Missing when isolation needed | Invalid value |
| permissionMode | Appropriate for task type | Missing for sensitive ops | Overly permissive |

#### Skills Quality Criteria

| Criterion | ✅ Good | ⚠️ Improve | ❌ Problem |
|-----------|---------|------------|------------|
| Location | name/SKILL.md structure | Flat file | Wrong location |
| YAML frontmatter | name, description | Missing fields | Invalid |
| Size | Under 500 lines | 500-1000 lines | Over 1000 lines |
| References | Large content in references/ | Everything in SKILL.md | Missing needed refs |
| Trigger conditions | Clear "when to use" | Vague triggers | No triggers |
| context field | `fork` when isolated execution needed | Missing when should be set | Invalid value |
| model field | Appropriate model override | Missing when speed matters | Invalid model name |
| hooks field | Valid lifecycle hooks | Hooks without matchers | Invalid hook events |

#### Settings Quality Criteria

| Criterion | ✅ Good | ⚠️ Improve | ❌ Problem |
|-----------|---------|------------|------------|
| JSON validity | Valid JSON | - | Parse errors |
| Hooks | Defined and documented | Undocumented | Invalid format |
| Hook events | Valid event names (12) | Uncommon events | Invalid event names |
| Hook types | Correct type (command/prompt/agent) | Missing type field | Invalid type |
| Permissions | Explicit allow/deny/ask | Implicit defaults | Overly permissive |
| Permission syntax | Tool(specifier) format | Missing specifiers | Invalid syntax |
| Permission eval order | deny → ask → allow | Only allow rules | No deny rules |
| Sandbox | Configured when auto-allowing Bash | Not configured | Disabled with bypassPermissions |
| Local settings | Gitignored properly | Not gitignored | Secrets exposed |
| MCP servers | Explicitly allowed/denied | All enabled without review | Secrets in config |

#### Memory/Rules Quality Criteria

| Criterion | ✅ Good | ⚠️ Improve | ❌ Problem |
|-----------|---------|------------|------------|
| Root CLAUDE.md | Exists with project instructions | Exists but empty | Missing |
| CLAUDE.md size | Under 500 lines | 500-800 lines | Over 800 lines |
| Rules modularity | `.claude/rules/*.md` for topics | Everything in CLAUDE.md | No rules |
| Path scoping | `paths` frontmatter on relevant rules | Generic rules for specific areas | Invalid glob patterns |
| Local settings | `CLAUDE.local.md` gitignored | Not in .gitignore | Committed with secrets |
| @imports | Resolve correctly (max 5 hops) | Missing referenced files | Circular imports |
| Rules/CLAUDE.md alignment | Rules match project architecture | Outdated rules | Contradictory rules |

#### Plugin Quality Criteria (if `.claude-plugin/` exists)

| Criterion | ✅ Good | ⚠️ Improve | ❌ Problem |
|-----------|---------|------------|------------|
| Manifest | Valid plugin.json with required fields | Missing optional fields | Invalid/missing manifest |
| Name | Lowercase, hyphens | Inconsistent | Missing |
| Components | Proper directory structure | Mixed locations | Missing directories |
| Namespacing | No prefix collisions | Inconsistent prefixes | Name conflicts |
| Hooks | In hooks/hooks.json | Scattered locations | Invalid format |

### Step 3: Check Cross-References

Verify integrity:
- Commands referencing agents → agents exist
- Agents referencing skills → skills exist
- Skills referencing other files → files exist

### Step 4: Detect Antipatterns

#### 4.1 Structural Antipatterns

Common issues to flag:

1. **Duplicate functionality** — Multiple commands doing similar things
2. **Missing descriptions** — Components without clear purpose
3. **Hardcoded paths** — Paths that won't work in other projects
4. **Overly long files** — Skills over 500 lines, commands over 200 lines
5. **No tool restrictions** — Commands/agents with unlimited tool access
6. **Inconsistent naming** — Mixed naming conventions
7. **Missing error handling** — Commands without pre-flight checks
8. **Secrets in settings** — API keys or sensitive data in versioned files
9. **Missing CLAUDE.md** — Project lacks root CLAUDE.md for instructions
10. **Rules without paths** — Rules in `.claude/rules/` that should be path-scoped but aren't
11. **Oversized context** — CLAUDE.md > 500 lines (always loaded, impacts context budget)
12. **Invalid hook events** — Hook using non-existent event name (12 valid events)
13. **Missing permission rules** — Settings with hooks but no permission deny rules

#### 4.2 Architectural Antipatterns

Advanced architectural issues:

1. **God-Agent** — Agent with >15 skills, violates SRP
2. **Feature Envy** — Skill placed in wrong domain (e.g., testing skill in DDD agent)
3. **Semantic Mismatch** — Command uses agent from different domain
4. **Skill Duplication** — Multiple skills with >70% similar functionality
5. **Missing Orchestration** — Complex workflow without coordinator agent
6. **Domain Leakage** — Skills mixing multiple bounded contexts
7. **Circular Dependencies** — Agents/skills referencing each other in loops
8. **Orphaned Domain** — Domain knowledge skill without corresponding generator/auditor

### Step 5: Resource Usage Analysis

Build dependency graph and find unused components:

#### 5.1 Build Usage Graph

Extract references from all components:

1. **Commands → Agents**: Parse command bodies for agent references
   - Look for Task tool calls with agent names
   - Pattern: `acc-*-agent`, `acc-*-auditor`, `acc-*-generator`, `acc-*-expert`, `acc-*-writer`, `acc-*-designer`

2. **Agents → Skills**: Parse agent frontmatter `skills:` field
   - Extract skill names from YAML list
   - Also check agent body for skill mentions

3. **Skills → Skills**: Parse skill bodies for cross-references
   - Look for skill name patterns in instructions

#### 5.2 Find Orphans

Compare discovered components against usage graph:

- **Orphaned skills** — Skills not referenced by any agent
- **Orphaned agents** — Agents not referenced by any command
- **Undocumented commands** — Commands not mentioned in README.md

#### 5.3 Resource Report Format

```
📊 Resource Usage Analysis
├── Active components: X/Y (Z%)
├── Orphaned skills: [list or "none"]
├── Orphaned agents: [list or "none"]
├── Undocumented commands: [list or "none"]
└── Circular references: [list or "none"]
```

### Step 6: Behavior Verification

Verify that component descriptions match actual behavior:

#### 6.1 Extract Declared Behavior

For each component, parse:
- `description` field — what it claims to do
- `argument-hint` — expected input format
- Key action verbs: generates, creates, audits, analyzes, validates, executes

#### 6.2 Extract Actual Behavior

Analyze component body:
- Tool usage patterns (Write = generates, Read/Grep = audits, Bash = executes)
- `$ARGUMENTS` handling — is it used if argument-hint is present?
- Output patterns — what the component actually produces

#### 6.3 Behavior Mapping Rules

| Description verb | Expected tools | Validation |
|------------------|----------------|------------|
| "generates", "creates", "writes" | Write, Edit | Must modify files |
| "audits", "analyzes", "checks" | Read, Grep, Glob | Must read files |
| "executes", "runs" | Bash | Must run commands |
| "validates" | Read, Grep | Must check criteria |

#### 6.4 Behavior Report Format

```
📋 Behavior Verification
├── ✅ acc-commit.md — description matches behavior
├── ⚠️ acc-foo.md — claims "generates" but no Write tool
├── ❌ acc-bar.md — argument-hint defined but $ARGUMENTS unused
└── Summary: X/Y components verified (Z%)
```

### Step 7: Context Awareness

Check alignment with project architecture and goals:

#### 7.1 Detect Project Context

Read project configuration files:
- `CLAUDE.md` (root) — global instructions
- `.claude/CLAUDE.md` — project-specific rules
- `README.md` — project purpose and tech stack
- `composer.json` — PHP dependencies (if exists)

#### 7.2 Identify Project Patterns

Look for mentions of:
- Architecture patterns: DDD, CQRS, Clean Architecture, Hexagonal, Event Sourcing
- Standards: PSR-1, PSR-4, PSR-12, etc.
- Frameworks: Symfony, Laravel, etc.
- Tech stack: PHP version, databases, queues

#### 7.3 Verify CLAUDE.md/Rules Alignment

Check that CLAUDE.md and `.claude/rules/` are consistent with components:
- Rules mention patterns → corresponding skills/agents exist
- CLAUDE.md architecture decisions → matching audit commands available
- Rules size is reasonable (< 500 lines total in CLAUDE.md, modular rules in `.claude/rules/`)
- No contradictory rules between CLAUDE.md and `.claude/rules/`

#### 7.4 Verify Pattern Alignment

Check if Claude configuration supports detected patterns:

| Project mentions | Required support |
|------------------|------------------|
| DDD | DDD audit command, DDD skills |
| CQRS | CQRS skills |
| PSR-* | PSR audit command, PSR skills |
| Event Sourcing | Event skills |
| PHP X.Y | Skills compatible with version |

#### 7.4 Context Report Format

```
🎯 Context Alignment
├── Project type: [detected patterns]
├── Tech stack: [detected technologies]
├── Pattern coverage:
│   ├── ✅ DDD — full support (audit + 13 skills)
│   ├── ✅ CQRS — full support (4 skills)
│   ├── ⚠️ Event Sourcing — partial (mentioned but no skills)
│   └── ❌ Laravel — not supported (no framework-specific skills)
└── Suggestions:
    └── 💡 Add Event Sourcing skills (mentioned in CLAUDE.md)
```

### Step 8: Command-Agent Semantic Fit

Verify that commands use agents appropriate for their domain:

#### 8.1 Extract Domain from Component Name

Parse naming patterns to identify domain:
- `acc-audit-ddd` → Domain: DDD
- `acc-generate-test` → Domain: Testing
- `acc-create-entity` → Domain: DDD
- `acc-psr-*` → Domain: PSR Standards

#### 8.2 Build Domain Map

Group components by domain:
```
DDD Domain:
├── Commands: acc-audit-ddd
├── Agents: acc-ddd-auditor, acc-ddd-generator
└── Skills: acc-ddd-knowledge, acc-create-entity, acc-create-value-object, ...

Testing Domain:
├── Commands: acc-generate-test, acc-audit-test
├── Agents: acc-test-generator, acc-test-auditor
└── Skills: acc-testing-knowledge, acc-create-unit-test, ...
```

#### 8.3 Verify Semantic Fit

Check command → agent domain alignment:

| Pattern | Status | Issue |
|---------|--------|-------|
| `acc-audit-ddd` → `acc-ddd-auditor` | ✅ Good | Same domain |
| `acc-audit-ddd` → `acc-test-auditor` | ❌ Mismatch | Cross-domain |
| `acc-generate-test` → `acc-ddd-generator` | ❌ Mismatch | Wrong domain |

#### 8.5 Semantic Fit Report Format

```
🔗 Command-Agent Semantic Fit
├── Commands analyzed: X
├── Perfect fit: Y (Z%)
├── Cross-domain usage: [list]
│   └── ⚠️ acc-foo.md uses acc-bar-agent (expected: acc-foo-agent)
└── Recommendation: Create domain-specific agents for mismatched commands
```

### Step 9: Agent Complexity Analysis (God-Agent Detection)

Detect agents that violate Single Responsibility Principle:

#### 9.1 Complexity Metrics

For each agent, calculate:
- **Skill count** — number of skills in frontmatter
- **Tool count** — number of tools in frontmatter
- **Responsibility count** — distinct action verbs in description
- **Line count** — total lines in agent file

#### 9.2 God-Agent Thresholds

| Metric | ✅ Good | ⚠️ Warning | ❌ God-Agent |
|--------|---------|------------|--------------|
| Skills | 1-10 | 11-15 | >15 |
| Tools | 1-5 | 6-8 | >8 |
| Responsibilities | 1-3 | 4-5 | >5 |
| Lines | <200 | 200-400 | >400 |

#### 9.3 Coordinator Progress Tracking Check

For agents with "coordinator" in name or description containing "orchestrates/coordinates":

| Check | ✅ Good | ⚠️ Missing |
|-------|---------|------------|
| TaskCreate in tools | Listed in frontmatter | Not listed |
| TaskUpdate in tools | Listed in frontmatter | Not listed |
| Progress section | Has "Progress Tracking" section | Missing section |
| Phase count | 3-5 phases defined | <3 or >5 phases |
| acc-task-progress-knowledge | In skills list | Missing |

**Detection:**
```bash
# Check if coordinator has TaskCreate
Grep: "TaskCreate" --glob ".claude/agents/*coordinator*.md"
Grep: "Progress Tracking" --glob ".claude/agents/*coordinator*.md"
Grep: "acc-task-progress-knowledge" --glob ".claude/agents/*coordinator*.md"
```

**Coordinator Progress Report:**
```
📊 Coordinator Progress Tracking
├── Coordinators found: X
├── With progress tracking: Y (Z%)
├── Missing TaskCreate:
│   └── ❌ acc-foo-coordinator — no Progress Tracking section
└── Recommendation: Add TaskCreate/TaskUpdate to coordinators
```

#### 9.3 Responsibility Extraction

Parse description for action verbs:
- "audits, validates, and generates" → 3 responsibilities
- "creates DDD components" → 1 responsibility
- "analyzes, detects, reports, and fixes" → 4 responsibilities

#### 9.4 God-Agent Report Format

```
🏛️ Agent Complexity Analysis
├── Agents analyzed: X
├── Healthy agents: Y (Z%)
├── Warning level: [list]
│   └── ⚠️ acc-architecture-auditor (12 skills, 4 responsibilities)
├── God-Agents detected:
│   └── ❌ acc-mega-agent (23 skills, 8 responsibilities)
│       ├── Recommended split:
│       │   ├── acc-mega-auditor (audit responsibilities)
│       │   └── acc-mega-generator (generation responsibilities)
│       └── Skills to redistribute: [grouped list]
└── Summary: X agents need refactoring
```

### Step 10: Skill Responsibility Analysis

Analyze skill design quality:

#### 10.1 Single Responsibility Check

For each skill, verify:
- **One primary action** — creates, audits, analyzes, generates (not multiple)
- **One domain focus** — DDD, Testing, PSR (not mixed)
- **Clear trigger** — when to use is specific

#### 10.2 Feature Envy Detection

Check if skill belongs in correct agent:

```
Skill: acc-create-unit-test
├── Current agent: acc-ddd-generator
├── Expected domain: Testing
├── Status: ❌ Feature Envy
└── Recommendation: Move to acc-test-generator
```

#### 10.3 Skill Similarity Analysis

Compare skills for potential duplication:

1. **Name similarity** — Levenshtein distance < 5
2. **Description similarity** — >70% word overlap
3. **Instruction similarity** — >60% content overlap

```
Potential duplicates:
├── acc-create-unit-test vs acc-create-test (85% similar)
│   └── Recommendation: Merge into acc-create-unit-test
├── acc-ddd-knowledge vs acc-domain-knowledge (75% similar)
│   └── Recommendation: Keep acc-ddd-knowledge, deprecate other
```

#### 10.4 Skill Responsibility Report Format

```
📋 Skill Responsibility Analysis
├── Skills analyzed: X
├── SRP compliant: Y (Z%)
├── SRP violations:
│   └── ⚠️ acc-mega-skill.md — multiple actions (creates, audits, validates)
├── Feature Envy:
│   └── ⚠️ acc-create-test in acc-ddd-generator (should be in acc-test-generator)
├── Similar skills (potential merge):
│   └── acc-foo-skill ↔ acc-bar-skill (82% similar)
└── Summary: X skills need attention
```

### Step 11: Domain Boundary Analysis

Analyze bounded context separation:

#### 11.1 Identify Domains

Extract domains from component naming and content:
- **DDD** — entity, value-object, aggregate, repository, domain-service
- **CQRS** — command, query, read-model
- **Testing** — test, mock, stub, builder
- **PSR** — psr-*, coding-style, autoloading
- **Documentation** — doc, readme, changelog, architecture
- **Patterns** — circuit-breaker, retry, saga, outbox
- **Architecture** — clean, hexagonal, layered, eda

#### 11.2 Build Domain Graph

Map components to domains and find overlaps:

```
Domain: DDD
├── Commands: 1
├── Agents: 2
├── Skills: 15
└── Boundary violations: 2
    ├── acc-ddd-generator uses acc-testing-knowledge (Testing domain)
    └── acc-ddd-auditor references PSR patterns (PSR domain)
```

#### 11.3 Cross-Domain Dependencies

Identify when domains depend on each other:

| From Domain | To Domain | Type | Status |
|-------------|-----------|------|--------|
| DDD | Testing | Expected | ✅ OK (test generation uses DDD) |
| PSR | DDD | Unexpected | ⚠️ Review |
| Documentation | All | Expected | ✅ OK (docs for everything) |

#### 11.4 Domain Boundary Report Format

```
🌐 Domain Boundary Analysis
├── Domains identified: X
├── Domain map:
│   ├── DDD: 1 cmd, 2 agents, 15 skills
│   ├── Testing: 2 cmd, 2 agents, 7 skills
│   ├── PSR: 1 cmd, 1 agent, 14 skills
│   └── ...
├── Boundary violations:
│   └── ⚠️ acc-foo-skill in DDD domain references Testing domain
├── Missing domains:
│   └── 💡 No dedicated Caching domain (mentioned in CLAUDE.md)
└── Recommendations:
    └── Consider creating acc-caching-* components
```

### Step 12: Refactoring Recommendations

Generate actionable refactoring proposals:

#### 12.1 Split Recommendations

For God-Agents and SRP violations:

```markdown
### Split Recommendation: acc-mega-agent

**Current state:**
- 23 skills across 4 domains
- Responsibilities: audits, generates, validates, documents

**Proposed split:**

| New Agent | Domain | Skills | Responsibilities |
|-----------|--------|--------|------------------|
| acc-mega-auditor | Audit | 8 | audits, validates |
| acc-mega-generator | Generation | 10 | generates, creates |
| acc-mega-documenter | Documentation | 5 | documents |

**Before:**
```yaml
name: acc-mega-agent
description: Audits, generates, validates, and documents everything
skills:
  - 23 skills listed
```

**After (acc-mega-auditor):**
```yaml
name: acc-mega-auditor
description: Audits and validates mega components
skills:
  - acc-mega-audit-skill-1
  - acc-mega-audit-skill-2
  # ... 8 skills
```
```

#### 12.2 Merge Recommendations

For duplicate/similar skills:

```markdown
### Merge Recommendation: acc-create-test + acc-create-unit-test

**Similarity:** 85%
**Reason:** Both create unit tests with minor variations

**Proposed merge:**
- Keep: acc-create-unit-test (more specific name)
- Deprecate: acc-create-test
- Migrate: Update acc-test-generator to use acc-create-unit-test

**Before:**
- acc-create-test: Generic test creation
- acc-create-unit-test: Unit test creation

**After:**
- acc-create-unit-test: Unified test creation with type parameter
```

#### 12.3 Move Recommendations

For Feature Envy:

```markdown
### Move Recommendation: acc-create-mock-repository

**Current location:** acc-ddd-generator (DDD domain)
**Recommended location:** acc-test-generator (Testing domain)
**Reason:** Mock repositories are testing artifacts, not DDD building blocks

**Action:**
1. Remove from acc-ddd-generator skills list
2. Add to acc-test-generator skills list
3. Update documentation
```

#### 12.4 Rename Recommendations

For naming inconsistencies:

```markdown
### Rename Recommendation: acc-domain-knowledge

**Current:** acc-domain-knowledge
**Proposed:** acc-ddd-knowledge
**Reason:** Consistency with acc-ddd-* naming convention

**Affected files:**
- .claude/skills/acc-domain-knowledge/SKILL.md → acc-ddd-knowledge/SKILL.md
- .claude/agents/acc-ddd-auditor.md (skills reference)
```

#### 12.5 Refactoring Report Format

```
🔧 Refactoring Recommendations
├── Split recommendations: X
│   └── acc-mega-agent → acc-mega-auditor + acc-mega-generator
├── Merge recommendations: X
│   └── acc-create-test + acc-create-unit-test → acc-create-unit-test
├── Move recommendations: X
│   └── acc-create-mock → from acc-ddd-generator to acc-test-generator
├── Rename recommendations: X
│   └── acc-domain-knowledge → acc-ddd-knowledge
├── Priority order:
│   1. ❌ Critical: Split acc-mega-agent (God-Agent)
│   2. ⚠️ High: Move Feature Envy skills
│   3. 💡 Low: Merge similar skills
└── Estimated impact: X files affected
```

## Output Format

Generate a structured markdown report:

### 1. Overview

```
📁 .claude/ Audit Report
========================

📊 Summary
├── Commands:  X found (Y issues)
├── Agents:    X found (Y issues)
├── Skills:    X found (Y issues)
├── Settings:  X files (Y issues)
├── Resource usage: X% active
├── Behavior match: X%
├── Context alignment: X%
├── Semantic fit: X%
├── SRP compliance: X%
├── Domain coverage: X domains
└── Total issues: X critical, Y warnings, Z suggestions
```

### 2. File Tree

Show discovered structure with status indicators:
```
.claude/
├── commands/
│   ├── ✅ acc-commit.md
│   ├── ⚠️ my-command.md (missing description)
│   └── ❌ broken.md (invalid YAML)
├── agents/
│   └── ✅ my-agent.md
├── skills/
│   └── ⚠️ my-skill/SKILL.md (too long: 800 lines)
└── ✅ settings.json
```

### 3. Detailed Analysis

For each file with issues:

```markdown
#### ⚠️ commands/my-command.md

**Issues:**
- Missing `description` in frontmatter
- No $ARGUMENTS validation
- Uses Bash without restriction

**Current:**
```yaml
---
allowed-tools: Bash
---
```

**Recommended:**
```yaml
---
description: Brief description of what this command does
allowed-tools: Bash, Read
argument-hint: <required-argument>
---

## Pre-flight Check
Validate $ARGUMENTS before proceeding...
```
```

### 4. Recommendations

Prioritized action items:

| Priority | File | Issue | Fix |
|----------|------|-------|-----|
| ❌ Critical | broken.md | Invalid YAML | Fix frontmatter syntax |
| ⚠️ High | my-command.md | No description | Add description field |
| 💡 Suggestion | settings.json | No hooks | Consider adding pre-commit hook |

### 5. Resource Usage

```
📊 Resource Usage Analysis
├── Active components: 81/84 (96%)
├── Orphaned skills:
│   └── acc-example-skill (not used by any agent)
├── Orphaned agents: none
├── Undocumented commands: none
└── Circular references: none
```

**Recommendation:**
- Remove orphaned skills or add them to relevant agents
- Document the purpose of undocumented commands

### 6. Behavior Verification

```
📋 Behavior Verification
├── Commands: 8/8 verified
│   ├── ✅ acc-commit.md — "generates commit" + Bash ✓
│   ├── ✅ acc-audit-ddd.md — "audits" + Read/Grep ✓
│   └── ...
├── Agents: 11/11 verified
└── Skills: 73/73 verified
```

**Mismatches found:**
| Component | Declared | Actual | Issue |
|-----------|----------|--------|-------|
| acc-foo.md | "generates files" | No Write tool | Missing tool capability |
| acc-bar.md | argument-hint: <path> | $ARGUMENTS unused | Argument not processed |

### 7. Context Alignment

```
🎯 Context Alignment
├── Project context detected:
│   ├── Architecture: DDD, CQRS, Clean Architecture
│   ├── Standards: PSR-1, PSR-4, PSR-12
│   ├── Tech: PHP 8.5, Redis, RabbitMQ
│   └── Principles: SOLID, GRASP
├── Pattern coverage:
│   ├── ✅ DDD — full (audit + 13 skills)
│   ├── ✅ CQRS — full (4 skills)
│   ├── ✅ PSR — full (audit + 11 skills)
│   ├── ✅ SOLID — full (knowledge + analyzer)
│   └── ✅ GRASP — full (knowledge skill)
└── Suggestions: none
```

**Gaps identified:**
| Context | Required | Available | Status |
|---------|----------|-----------|--------|
| Event Sourcing | skills/audit | knowledge only | ⚠️ Partial |
| Redis | cache skills | none | 💡 Consider |

### 8. Command-Agent Semantic Fit

```
🔗 Command-Agent Semantic Fit
├── Commands analyzed: 8
├── Perfect fit: 7 (87.5%)
│   ├── ✅ acc-audit-ddd → acc-ddd-auditor (DDD → DDD)
│   ├── ✅ acc-generate-test → acc-test-generator (Testing → Testing)
│   └── ...
├── Cross-domain usage:
│   └── ⚠️ acc-foo.md uses acc-bar-agent
│       ├── Command domain: Foo
│       ├── Agent domain: Bar
│       └── Recommendation: Create acc-foo-agent or use existing Foo agent
└── Summary: 1 command needs agent alignment
```

### 9. Architectural Analysis

```
🏛️ Agent Complexity Analysis
├── Agents analyzed: 11
├── Healthy: 9 (82%)
├── Warning level:
│   └── ⚠️ acc-architecture-auditor (14 skills, 4 responsibilities)
├── God-Agents: 0
└── Summary: Consider splitting acc-architecture-auditor

📋 Skill Responsibility Analysis
├── Skills analyzed: 73
├── SRP compliant: 71 (97%)
├── SRP violations:
│   └── ⚠️ acc-mega-skill — audits AND generates
├── Feature Envy: 1
│   └── acc-create-mock-repository in acc-ddd-generator (Testing domain)
├── Similar skills: 2 pairs
│   └── acc-foo ↔ acc-bar (78% similar)
└── Summary: 2 skills need attention

🌐 Domain Boundary Analysis
├── Domains: 7 (DDD, Testing, PSR, Documentation, Patterns, Architecture, Claude Code)
├── Domain distribution:
│   ├── DDD: 1 cmd, 2 agents, 15 skills
│   ├── Testing: 2 cmd, 2 agents, 7 skills
│   └── ...
├── Boundary violations: 1
│   └── acc-create-mock-repository crosses DDD → Testing
└── Missing domains: none
```

### 10. Refactoring Proposals

```
🔧 Refactoring Recommendations

## Split Proposals
None needed.

## Merge Proposals
| Skills | Similarity | Action |
|--------|------------|--------|
| acc-foo + acc-bar | 78% | Merge into acc-foo |

## Move Proposals
| Skill | From | To | Reason |
|-------|------|-----|--------|
| acc-create-mock-repository | acc-ddd-generator | acc-test-generator | Feature Envy |

## Rename Proposals
None needed.

## Priority Order
1. ⚠️ High: Move acc-create-mock-repository (Feature Envy)
2. 💡 Low: Merge similar skills

## Estimated Impact
- Files affected: 3
- Agents updated: 2
- Commands unchanged: 8
```

### 11. Quick Fixes

Ready-to-apply fixes for common issues:

```markdown
**Fix: Add missing description to my-command.md**
Add this to the YAML frontmatter:
description: [Describe what this command does and when to use it]
```

## Missing Configuration

If `.claude/` folder is missing or empty, provide starter template:

```markdown
## Recommended Structure

Your project is missing Claude Code configuration. Here's a starter setup:

### 1. Create basic structure

```bash
mkdir -p .claude/commands .claude/agents .claude/skills
```

### 2. Create CLAUDE.md

```markdown
# CLAUDE.md

## Project Overview
[Describe your project]

## Architecture
[Key patterns and structures]

## Commands
- `make test` — run tests
- `make lint` — check code style
```

### 3. Create settings.json

```json
{
  "hooks": {
    "PreToolUse": []
  },
  "permissions": {
    "allow": [],
    "deny": []
  }
}
```

### 4. Add to .gitignore

```
.claude/settings.local.json
```
```

## Audit Levels

Level is an optional positional parameter. Default: `standard`.

| Level | Scope | What's Checked |
|-------|-------|----------------|
| `quick` | Structure + cross-refs | Frontmatter validation, cross-reference integrity |
| `standard` | Quick + quality + antipatterns | Standard quality criteria, structural antipatterns, behavior verification |
| `deep` | Standard + architecture | Standard + God-Agent detection, domain boundaries, skill responsibility, refactoring recommendations |

## Severity Levels

| Level | Symbol | Criteria |
|-------|--------|----------|
| Critical | 🔴 | Invalid YAML, broken cross-references, missing required files |
| High | 🟠 | God-Agent detected, orphaned components, behavior mismatch |
| Medium | 🟡 | Quality criteria warnings, naming inconsistencies |
| Low | 🟢 | Style suggestions, optional improvements |

## Meta-Instructions Guide

| Instruction | Effect |
|-------------|--------|
| `focus on God-Agent` | Deep God-Agent detection analysis |
| `check only commands` | Only audit command files |
| `check only agents` | Only audit agent files |
| `skip skills` | Exclude skills from audit |
| `level:quick` | Quick audit (same as positional `quick`) |
| `level:standard` | Standard audit (same as positional `standard`) |
| `level:deep` | Deep audit (same as positional `deep`) |
| `detailed report` | Maximum detail in report |
| `на русском` | Report in Russian |

## Usage

```bash
/acc-audit-claude-components
/acc-audit-claude-components quick
/acc-audit-claude-components deep
/acc-audit-claude-components deep -- focus on God-Agent detection
/acc-audit-claude-components -- level:deep
```
