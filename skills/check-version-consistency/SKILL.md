---
name: acc-check-version-consistency
description: Audits version consistency across project files. Checks composer.json, README, CHANGELOG, docs, and configuration files for version number synchronization.
---

# Version Consistency Audit

Analyze project files for version number synchronization across all locations where version is referenced.

## Detection Patterns

### 1. composer.json vs README Version Mismatch

```json
// composer.json says:
{ "version": "2.10.0" }
```

```markdown
<!-- README.md says: -->
Current version: **2.9.0**   <!-- OUTDATED! -->
```

### 2. CHANGELOG Missing Latest Version

```markdown
<!-- CHANGELOG.md -->
## [2.9.0] - 2025-01-15
- Added feature X

<!-- Missing entry for 2.10.0! -->
```

### 3. Documentation References Old Version

```markdown
<!-- docs/getting-started.md -->
composer require vendor/package:^2.8
<!-- Should be ^2.10 -->
```

### 4. Component Count Mismatch

```markdown
<!-- README.md says: -->
| Skills | 200 |

<!-- docs/quick-reference.md says: -->
| Skills | 222 |

<!-- Out of sync! -->
```

## Verification Process

### Step 1: Find All Version References

```bash
# Version in composer.json
Grep: "\"version\"" --glob "composer.json"

# Version in README
Grep: "version|v[0-9]+\.[0-9]+\.[0-9]+" -i --glob "README.md"

# Version in CHANGELOG
Grep: "## \[" --glob "CHANGELOG.md"

# Version in docs
Grep: "version|v[0-9]+\.[0-9]+" -i --glob "docs/**/*.md"

# Version in configuration
Grep: "version" --glob "**/*.json" --glob "**/*.yaml" --glob "**/*.yml"
```

### Step 2: Extract Canonical Version

```bash
# Primary source of truth: composer.json or latest CHANGELOG entry
Read: composer.json
# Extract version field

# Or from git tags
# git describe --tags --abbrev=0
```

### Step 3: Cross-Check All Locations

For each location where version appears:
1. Extract the version number
2. Compare against canonical version
3. Report mismatches

### Step 4: Verify Component Counts

```bash
# Count actual components
Glob: .claude/commands/acc-*.md      # Commands count
Glob: .claude/agents/acc-*.md        # Agents count
Glob: .claude/skills/acc-*/SKILL.md  # Skills count

# Check documented counts in all files
Grep: "commands.*[0-9]+|agents.*[0-9]+|skills.*[0-9]+" -i --glob "README.md"
Grep: "commands.*[0-9]+|agents.*[0-9]+|skills.*[0-9]+" -i --glob "docs/quick-reference.md"
Grep: "commands.*[0-9]+|agents.*[0-9]+|skills.*[0-9]+" -i --glob "composer.json"
```

### Step 5: Verify CHANGELOG Completeness

```bash
# Check CHANGELOG has entry for current version
Grep: "## \[" --glob "CHANGELOG.md"

# Check comparison links at bottom
Grep: "\[.*\]: https://.*compare" --glob "CHANGELOG.md"
```

## Files to Check

| File | What to Verify |
|------|---------------|
| `composer.json` | `version` field, `description` with counts |
| `README.md` | Version badges, component counts, install examples |
| `CHANGELOG.md` | Latest version section, comparison links |
| `docs/quick-reference.md` | Statistics table, version references |
| `llms.txt` | Quick Facts section, component counts |
| `CLAUDE.md` | Architecture section counts |
| `docs/*.md` | Version references in examples |

## Severity Classification

| Pattern | Severity |
|---------|----------|
| composer.json version wrong | 🔴 Critical |
| CHANGELOG missing latest version | 🔴 Critical |
| README version mismatch | 🟠 Major |
| Component count mismatch | 🟠 Major |
| Docs referencing old version | 🟡 Minor |
| Badge showing wrong version | 🟡 Minor |

## Output Format

```markdown
### Version Consistency: [Description]

**Severity:** 🔴/🟠/🟡
**Canonical Version:** X.Y.Z

**Mismatches Found:**

| File | Expected | Found | Line |
|------|----------|-------|------|
| `README.md` | 2.10.0 | 2.9.0 | 15 |
| `docs/guide.md` | ^2.10 | ^2.8 | 23 |

**Component Count Sync:**

| File | Commands | Agents | Skills | Status |
|------|----------|--------|--------|--------|
| Actual | 26 | 56 | 222 | Source |
| README.md | 26 | 56 | 222 | OK |
| composer.json | 26 | 56 | 200 | MISMATCH |

**Fix:**
Update all listed files to version X.Y.Z.
```
