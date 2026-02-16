# Documentation Audit Procedures

## Pre-Audit Setup

### 1. Gather Information

```bash
# Find all documentation files
Glob: **/*.md

# Find all source files
Glob: src/**/*.php

# Get project structure
tree -L 3 --dirsfirst

# Check git history for doc changes
git log --oneline --since="3 months ago" -- "*.md"
```

### 2. Identify Documentation Scope

| Category | Files | Priority |
|----------|-------|----------|
| Entry Point | README.md | Critical |
| Installation | docs/installation.md | Critical |
| API | docs/api/*.md | High |
| Architecture | docs/architecture/*.md | High |
| Guides | docs/guides/*.md | Medium |
| Reference | docs/reference/*.md | Medium |
| Other | *.md | Low |

## Audit Process

### Phase 1: Completeness Check

**README.md Audit**

```markdown
[ ] Project description present
[ ] Installation instructions
[ ] Basic usage example
[ ] Requirements listed
[ ] License specified
[ ] Links to documentation
```

**API Documentation Audit**

```bash
# Count public classes
Grep: "^(final )?class " --glob "src/**/*.php" | wc -l

# Count documented classes
Grep: "## class " --glob "docs/api/**/*.md" | wc -l

# Calculate coverage
echo "Coverage: documented/total * 100"
```

**Method Coverage**

```bash
# Count public methods
Grep: "public function " --glob "src/**/*.php" | wc -l

# Count documented methods
Grep: "### " --glob "docs/api/**/*.md" | wc -l
```

### Phase 2: Accuracy Check

**Version Consistency**

```bash
# Check versions match
Grep: "version" --glob "README.md" --glob "composer.json"

# Check PHP version requirements
Grep: "php.*[0-9]" --glob "README.md"
Grep: '"php":' --glob "composer.json"
```

**Code Example Testing**

1. Extract code blocks from docs
2. Create test file
3. Run with PHP
4. Verify output matches

```bash
# Find all PHP code blocks
Grep: "```php" -A 20 --glob "docs/**/*.md"
```

**Link Validation**

```bash
# Find all internal links
Grep: "\]\([^http]" --glob "**/*.md"

# For each link, verify file exists
```

### Phase 3: Clarity Check

**Terminology Audit**

```bash
# Find acronyms
Grep: "\b[A-Z]{2,5}\b" --glob "**/*.md"

# Check each is defined on first use
```

**Readability Metrics**

| Metric | Target | Check |
|--------|--------|-------|
| Avg paragraph length | < 5 lines | Manual |
| Code:text ratio | 1:3 to 1:1 | Count blocks |
| Headers per 500 words | 2-4 | Count headers |

### Phase 4: Navigation Check

**TOC Validation**

```bash
# Find docs > 100 lines
wc -l docs/**/*.md | awk '$1 > 100'

# Each should have TOC
Grep: "## Table of Contents|## Contents" --glob "docs/**/*.md"
```

**Cross-Reference Check**

```bash
# Find all links between docs
Grep: "\]\(.*\.md\)" --glob "**/*.md"

# Verify each target exists
# Verify bidirectional links where appropriate
```

### Phase 5: Diagram Check

**Diagram Inventory**

```bash
# Find all Mermaid diagrams
Grep: "```mermaid" --glob "**/*.md"

# Count elements per diagram (manual review)
```

**Diagram Quality**

| Check | Pass | Fail |
|-------|------|------|
| Elements ≤ 9 | ✅ | ❌ |
| All labeled | ✅ | ❌ |
| Renders correctly | ✅ | ❌ |
| Matches current architecture | ✅ | ❌ |

## Scoring

### Calculate Dimension Scores

```markdown
Completeness Score = (items_documented / total_items) × 100

Accuracy Score = 100 - (errors × 10)  // Max penalty 100

Clarity Score = Based on manual review (0-100)

Consistency Score = Based on terminology/style review (0-100)

Navigation Score = (working_links / total_links) × 100
```

### Calculate Overall Score

```markdown
Overall = (Completeness × 0.25) + (Accuracy × 0.25) + (Clarity × 0.20)
        + (Consistency × 0.15) + (Navigation × 0.10) + (Freshness × 0.05)
```

## Report Generation

### Issue Classification

```markdown
## Critical Issues (Score < 60)
Issues that block user success:
- Missing installation
- Broken examples
- Incorrect information

## Warnings (Score 60-79)
Issues that hinder user experience:
- Missing API docs
- Incomplete examples
- Outdated information

## Recommendations (Score 80-89)
Improvements for excellence:
- Additional examples
- Better organization
- More diagrams

## Good (Score 90-100)
Document what's working well.
```

### Priority Matrix

```markdown
             | High Impact | Low Impact
-------------|-------------|------------
Quick Fix    | Do First    | Do Later
Hard Fix     | Plan        | Consider
```

## Post-Audit Actions

1. **Create issues** for Critical problems
2. **Schedule work** for Warnings
3. **Add to backlog** Recommendations
4. **Document** baseline scores
5. **Schedule** follow-up audit (quarterly)
