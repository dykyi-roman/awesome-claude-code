---
description: Generate or rewrite documentation for a file/folder. Creates README, architecture docs, Mermaid diagrams. Use when you need to create or improve technical documentation.
allowed-tools: Read, Write, Edit, Glob, Grep, Task
model: opus
argument-hint: <path> [-- additional instructions]
---

# Generate Documentation

Generate high-quality technical documentation for a file, folder, or project.

## Input Parsing

Parse `$ARGUMENTS` to extract path and optional meta-instructions:

```
Format: <path> [-- <meta-instructions>]

Examples:
- /acc-generate-documentation ./
- /acc-generate-documentation src/ -- focus on API documentation
- /acc-generate-documentation ./ -- create architecture doc with C4 diagrams
- /acc-generate-documentation src/Domain/Order -- document only public interfaces
- /acc-generate-documentation ./ -- на русском языке
```

**Parsing rules:**
1. Split `$ARGUMENTS` by ` -- ` (space-dash-dash-space)
2. First part = **path** (required, default: current directory)
3. Second part = **meta-instructions** (optional, customization)

## Target

- **Path**: First part of `$ARGUMENTS` (before `--`)
- **Meta-instructions**: Second part (after `--`) — use to customize output

If meta-instructions provided, adjust documentation to:
- Focus on specific documentation types
- Include/exclude certain sections
- Use specific diagram types
- Target specific audience
- Use specific language

## Pre-flight Check

1. **Verify the path exists:**
   - If `$ARGUMENTS` is empty, ask user what they want to document
   - If path doesn't exist, report error and stop

2. **Determine documentation type:**
   - File → API documentation, code examples
   - Directory → README, architecture docs
   - Project root → Full documentation suite

## Documentation Flow

```
/acc-generate-documentation <path>
    │
    ├─ Pre-flight: Validate path exists
    │
    ├─ Phase 1: Analyze project scope
    │   ├─ Read composer.json (if exists)
    │   ├─ Identify project type (library/app/API)
    │   └─ Determine audience
    │
    ├─ Phase 2: Task → acc-documentation-writer
    │   └─ Generate appropriate documentation
    │
    ├─ Phase 3: Task → acc-diagram-designer (if architecture docs)
    │   └─ Create Mermaid diagrams
    │
    └─ Output: Generated documentation files
```

## Instructions

Use the `acc-documentation-writer` agent to create documentation:

### For Project Root (default)

Generate complete documentation suite:

1. **README.md** — Project overview, installation, quick start
2. **docs/getting-started.md** — Detailed tutorial
3. **docs/architecture.md** — System architecture (if complex)

### For Directory

Generate contextual documentation:

| Directory Type | Output |
|----------------|--------|
| `src/` | Architecture overview + API index |
| `src/Domain/` | Domain model documentation |
| `src/Api/` | API endpoint documentation |
| `docs/` | Improve existing docs |

### For File

Generate specific documentation:

| File Type | Output |
|-----------|--------|
| Class file | Class documentation with examples |
| Interface | API documentation |
| Config file | Configuration reference |

## Diagram Generation

For architecture documentation, invoke the diagram designer:

```
Task tool with subagent_type="acc-diagram-designer"
prompt: "Create diagrams for {target}. Include:
- System context (if project)
- Layer diagram (if DDD/Clean Architecture)
- Component interactions (if multiple services)"
```

## Expected Output

### For README.md

```markdown
# {Project Name}

{badges}

{one-line description}

## Features
{bullet list with benefits}

## Installation
{composer/setup commands}

## Quick Start
{minimal working example}

## Documentation
{links to docs}

## Contributing
{contributing link}

## License
{license}
```

### For Architecture Documentation

```markdown
# Architecture

## Overview
{high-level description}

## System Context
{C4 context diagram - Mermaid}

## Layers
{layer diagram - Mermaid}

## Components
{component descriptions}

## Technology Stack
{technology table}
```

### For API Documentation

```markdown
# API Reference

## {ClassName}

### Overview
{class purpose}

### Methods

#### method(params): ReturnType
{description}

**Parameters:**
| Name | Type | Description |
|------|------|-------------|

**Returns:** {description}

**Example:**
```php
// usage example
```
```

## Documentation Quality Checklist

Generated documentation must have:

- [ ] Clear project description
- [ ] Installation instructions (if applicable)
- [ ] Working code examples
- [ ] Appropriate diagrams (for architecture)
- [ ] Links to related documentation
- [ ] Consistent formatting

## Usage Examples

```bash
# Document entire project
/acc-generate-documentation

# Document specific directory
/acc-generate-documentation src/Domain/Order

# Document specific file
/acc-generate-documentation src/Service/PaymentService.php

# Document API
/acc-generate-documentation src/Api/
```

## Follow-up

After generating documentation, suggest:

1. **Review generated files** for accuracy
2. **Run `/acc-audit-documentation`** for quality check
3. **Add/update diagrams** if needed
