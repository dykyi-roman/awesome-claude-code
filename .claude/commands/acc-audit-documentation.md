---
description: Audit documentation quality. Checks completeness, accuracy, clarity, navigation, and diagrams. Use for documentation review and improvement planning.
allowed-tools: Read, Glob, Grep, Bash, Task
model: opus
argument-hint: <path> [level] [-- meta-instructions]
---

# Documentation Audit

Perform a comprehensive documentation quality audit with actionable improvement recommendations.

## Input Parsing

Parse `$ARGUMENTS` to extract path, level, and optional meta-instructions:

```
Format: <path> [level] [-- <meta-instructions>]

Arguments:
- path: Target directory or file (required, default: current directory)
- level: Audit depth - quick|standard|deep (optional, default: standard)
- -- meta-instructions: Additional focus areas or filters (optional)

Examples:
- /acc-audit-documentation docs/
- /acc-audit-documentation docs/ deep
- /acc-audit-documentation docs/ quick
- /acc-audit-documentation docs/ -- focus on API documentation
- /acc-audit-documentation docs/ deep -- check examples actually work
- /acc-audit-documentation docs/ -- level:deep (backward compatible)
```

**Parsing rules:**
1. Split `$ARGUMENTS` by ` -- ` (space-dash-dash-space)
2. First part = positional arguments, Second part = meta-instructions
3. In positional arguments, check if last word is a valid level (`quick|standard|deep`)
4. If level found → extract it; remaining = path
5. Also accept `level:quick|standard|deep` in meta-instructions (backward compatibility)
6. Priority: positional > meta-instruction > default (`standard`)
7. Default path: current directory (if empty)

## Target

- **Path**: First part of `$ARGUMENTS` (before `--`)
- **Meta-instructions**: Second part (after `--`) — use to customize audit focus

If meta-instructions provided, adjust audit to:
- Focus on specific documentation types
- Skip certain checks if requested
- Prioritize specific quality dimensions

## Pre-flight Check

1. **Verify the path exists:**
   - If `$ARGUMENTS` is empty, audit current directory
   - If path doesn't exist, report error and stop

2. **Find documentation files:**
   - Look for `*.md` files
   - Check for `docs/` directory
   - Identify README.md, CHANGELOG.md, etc.

## Audit Flow

```
/acc-documentation-audit <path>
    │
    ├─ Pre-flight: Validate path exists
    │
    ├─ Phase 1: Scan documentation files
    │   ├─ Glob: **/*.md
    │   ├─ Categorize by type (README, API, Architecture)
    │   └─ Prioritize by importance
    │
    ├─ Phase 2: Task → acc-documentation-auditor
    │   ├─ Completeness check
    │   ├─ Accuracy check
    │   ├─ Clarity check
    │   ├─ Consistency check
    │   └─ Navigation check
    │
    └─ Output: Quality report with recommendations
```

## Instructions

Use the `acc-documentation-auditor` agent to perform quality assessment:

### Quality Dimensions

| Dimension | Weight | Checks |
|-----------|--------|--------|
| **Completeness** | 25% | All APIs documented, required sections |
| **Accuracy** | 25% | Code matches docs, versions correct |
| **Clarity** | 20% | No jargon, working examples |
| **Consistency** | 15% | Uniform style, terminology |
| **Navigation** | 10% | Working links, logical structure |
| **Freshness** | 5% | Up-to-date with latest version |

### Audit Checklist

**README.md:**
- [ ] Project description
- [ ] Installation instructions
- [ ] Basic usage example
- [ ] Examples actually run
- [ ] License information
- [ ] Links to documentation

**API Documentation:**
- [ ] All public classes documented
- [ ] All public methods documented
- [ ] Parameters with types
- [ ] Return types documented
- [ ] Usage examples
- [ ] Error handling documented

**Architecture Documentation:**
- [ ] System overview
- [ ] Component descriptions
- [ ] Diagrams render correctly
- [ ] Matches actual code structure
- [ ] Technology decisions explained

## Expected Output

### Audit Report Structure

```markdown
# Documentation Audit Report

**Project:** {name}
**Date:** {date}
**Path:** {audited path}

## Executive Summary

| Metric | Score | Status |
|--------|-------|--------|
| **Overall** | X/100 | ✅/🟡/🔴 |
| Completeness | X/100 | ✅/🟡/🔴 |
| Accuracy | X/100 | ✅/🟡/🔴 |
| Clarity | X/100 | ✅/🟡/🔴 |
| Consistency | X/100 | ✅/🟡/🔴 |
| Navigation | X/100 | ✅/🟡/🔴 |

**Rating:** {Excellent (90+) | Good (75-89) | Adequate (60-74) | Poor (40-59) | Critical (<40)}

## Critical Issues

Issues blocking user success:

### 1. {Issue Title}
- **Location:** {file:line}
- **Problem:** {description}
- **Impact:** {who is affected}
- **Fix:** {specific action}

## Warnings

Issues hindering user experience:

### 1. {Issue Title}
- **Location:** {file}
- **Problem:** {description}
- **Recommendation:** {improvement}

## Improvement Recommendations

### High Priority
| Issue | File | Action | Tool |
|-------|------|--------|------|
| Missing README | / | Create README | `/acc-generate-documentation` |
| No examples | docs/api.md | Add code examples | `/acc-generate-documentation` |

### Medium Priority
| Issue | File | Action |
|-------|------|--------|
| Outdated diagram | docs/arch.md | Update Mermaid |
| Missing TOC | docs/guide.md | Add table of contents |

### Low Priority
| Issue | File | Action |
|-------|------|--------|
| No badges | README.md | Add CI/coverage badges |
| Missing FAQ | docs/ | Create FAQ section |

## Detailed Findings

### README.md Analysis
| Check | Status | Notes |
|-------|--------|-------|
| Project description | ✅/❌ | {notes} |
| Installation | ✅/❌ | {notes} |
| Quick start example | ✅/❌ | {notes} |
| Examples run correctly | ✅/❌ | {notes} |
| License | ✅/❌ | {notes} |

### API Documentation Coverage
| Metric | Value |
|--------|-------|
| Public classes | X |
| Documented classes | Y |
| Coverage | Z% |

### Link Validation
| Link | Source | Status |
|------|--------|--------|
| [link text](target) | file.md:line | ✅/❌ |

## Action Plan

### Quick Wins (< 1 hour)
1. [ ] Fix broken links
2. [ ] Add missing badges
3. [ ] Update version numbers

### Short-term (1 day)
1. [ ] Add missing code examples
2. [ ] Create FAQ section
3. [ ] Update outdated diagrams

### Long-term (1 week+)
1. [ ] Generate API documentation
2. [ ] Create architecture documentation
3. [ ] Set up documentation CI/CD
```

## Scoring Guide

| Score | Rating | Interpretation |
|-------|--------|----------------|
| 90-100 | ✅ Excellent | Production-ready documentation |
| 75-89 | 🟢 Good | Minor improvements needed |
| 60-74 | 🟡 Adequate | Significant gaps to address |
| 40-59 | 🟠 Poor | Major issues blocking users |
| 0-39 | 🔴 Critical | Documentation emergency |

## Audit Levels

Level is an optional positional parameter. Default: `standard`.

| Level | Scope | What's Checked |
|-------|-------|----------------|
| `quick` | Completeness only | Required files present, basic section checks |
| `standard` | 6-dimension scoring | Completeness, accuracy, clarity, consistency, navigation, freshness |
| `deep` | Standard + verification | Standard + code example verification, link validation, diagram rendering |

## Severity Levels

| Level | Symbol | Criteria |
|-------|--------|----------|
| Critical | 🔴 | Missing README, no installation docs, broken critical links |
| High | 🟠 | Missing API docs, outdated examples, no architecture description |
| Medium | 🟡 | Incomplete sections, minor inconsistencies, missing TOC |
| Low | 🟢 | Style suggestions, missing badges, formatting improvements |

## Meta-Instructions Guide

| Instruction | Effect |
|-------------|--------|
| `focus on API` | Deep API documentation analysis |
| `focus on examples` | Verify code examples work |
| `check links` | Full link validation |
| `skip architecture` | Exclude architecture docs |
| `level:quick` | Quick audit (same as positional `quick`) |
| `level:standard` | Standard audit (same as positional `standard`) |
| `level:deep` | Deep audit (same as positional `deep`) |
| `detailed report` | Maximum detail in report |
| `на русском` | Report in Russian |

## Usage Examples

```bash
# Standard audit (default)
/acc-audit-documentation docs/

# Quick check
/acc-audit-documentation docs/ quick

# Deep analysis
/acc-audit-documentation docs/ deep

# Deep + focus
/acc-audit-documentation docs/ deep -- check examples actually work

# Backward compatible
/acc-audit-documentation docs/ -- level:deep
```

## Follow-up Actions

Based on audit results, suggest:

1. **For Critical Issues:**
   - Run `/acc-generate-documentation` to create missing docs

2. **For Diagram Issues:**
   - Invoke `acc-diagram-designer` to create/update diagrams

3. **For Regular Maintenance:**
   - Schedule periodic audits
   - Add documentation to PR checklist
