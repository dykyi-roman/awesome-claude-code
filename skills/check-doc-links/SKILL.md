---
name: acc-check-doc-links
description: Validates documentation links. Detects broken relative links, missing anchor targets, malformed URLs, and orphaned documentation files.
---

# Documentation Link Validation

Analyze documentation files for broken links, missing targets, and navigation issues.

## Detection Patterns

### 1. Broken Relative Links

```markdown
<!-- BROKEN: Target file doesn't exist -->
See [installation guide](docs/install.md)
<!-- File docs/install.md not found -->

<!-- BROKEN: Wrong path depth -->
See [API docs](../docs/api.md)
<!-- Should be ./docs/api.md -->

<!-- BROKEN: Case mismatch -->
See [README](readme.md)
<!-- Actual file is README.md -->
```

### 2. Broken Anchor Links

```markdown
<!-- BROKEN: Anchor target doesn't exist in file -->
See [Configuration](#configuration)
<!-- No ## Configuration heading found -->

<!-- BROKEN: Anchor in another file -->
See [API Authentication](docs/api.md#auth)
<!-- docs/api.md exists but has no ## Auth heading -->

<!-- BROKEN: Wrong anchor format -->
See [Setup](#set-up)
<!-- Heading is "## Set Up" → anchor should be #set-up -->
```

### 3. Malformed URLs

```markdown
<!-- MALFORMED: Missing protocol -->
See [docs](www.example.com/docs)

<!-- MALFORMED: Space in URL -->
See [guide](docs/getting started.md)

<!-- MALFORMED: Unencoded special characters -->
See [API](docs/api?version=2&format=json)
```

### 4. Orphaned Documentation

```markdown
<!-- File exists but no other doc links to it -->
docs/deprecated-api.md    <!-- Not linked from any other .md file -->
docs/internal-notes.md    <!-- Not in any navigation/TOC -->
```

## Grep Patterns

```bash
# All markdown links (relative)
Grep: "\]\([^http][^:][^/][^)]+\)" --glob "**/*.md"

# All markdown links (absolute)
Grep: "\]\(https?://[^)]+\)" --glob "**/*.md"

# Anchor links
Grep: "\]\(#[^)]+\)" --glob "**/*.md"

# Cross-file anchor links
Grep: "\]\([^)]+\.md#[^)]+\)" --glob "**/*.md"

# Image references
Grep: "!\[[^\]]*\]\([^)]+\)" --glob "**/*.md"

# HTML links in markdown
Grep: "href=\"[^\"]+\"" --glob "**/*.md"
```

## Validation Process

### Step 1: Extract All Links

```bash
# Find all relative links
Grep: "\]\(([^http][^)]+)\)" --glob "**/*.md"

# Find all anchor links
Grep: "\]\((#[^)]+)\)" --glob "**/*.md"
```

### Step 2: Verify Targets Exist

For each relative link `[text](path)`:
1. Resolve path relative to the source file's directory
2. Check if target file exists using `Glob`
3. If link has `#anchor`, verify heading exists in target

### Step 3: Check Anchor Targets

For each anchor link `[text](#heading)`:
1. Convert heading to anchor: lowercase, replace spaces with `-`, remove special chars
2. Search for matching heading in the file
3. Report if no match found

### Step 4: Find Orphaned Docs

```bash
# List all .md files
Glob: **/*.md

# For each file, check if it's referenced by any other .md
Grep: "filename.md" --glob "**/*.md"
# If referenced by 0 files and not README/CHANGELOG → orphaned
```

## Severity Classification

| Pattern | Severity |
|---------|----------|
| Broken link to critical doc (README, install) | 🔴 Critical |
| Broken relative link | 🟠 Major |
| Broken anchor link | 🟡 Minor |
| Malformed URL | 🟡 Minor |
| Orphaned documentation | 🟡 Minor |

## Output Format

```markdown
### Link Validation: [Description]

**Severity:** 🔴/🟠/🟡
**Source:** `file.md:line`
**Link:** `[text](target)`
**Type:** Relative/Anchor/External/Image

**Issue:**
[Description — target not found, anchor missing, etc.]

**Fix:**
- Correct path: `[text](correct/path.md)`
- Or remove dead link
```

## Summary Report Format

```markdown
## Link Validation Summary

| Metric | Count |
|--------|-------|
| Total links checked | X |
| Valid links | X |
| Broken relative links | X |
| Broken anchors | X |
| Malformed URLs | X |
| Orphaned files | X |

### Broken Links

| Source | Link | Issue |
|--------|------|-------|
| `README.md:45` | `[guide](docs/guide.md)` | File not found |
| `docs/api.md:12` | `[auth](#authentication)` | Anchor not found |
```
