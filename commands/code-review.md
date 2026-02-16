---
description: Code review for branch changes. Analyzes git diff between branches with multi-level depth (low/medium/high). Matches changes against task description. Returns structured report with severity levels and verdict.
allowed-tools: Read, Grep, Glob, Bash, Task
model: opus
argument-hint: [branch/path] [level] [-- task-description]
---

# Code Review Command

Perform comprehensive code review on branch changes with configurable depth levels.

## Input Parsing

Parse `$ARGUMENTS` to extract branch, path, level, and optional task description:

```
Format: [branchpath] [level] [-- task-description]

Arguments:
- branch: Branch to review (auto-detected vs path)
- path: File or folder to filter (auto-detected vs branch)
- level: Review depth - high|medium|low (optional, default: high)
- -- task-description: Task description for matching analysis (optional)
- Target: Always main/master (auto-detected)

Examples:
- /acc-code-review                                   # current branch, whole project, high
- /acc-code-review feature/payment                   # branch, whole project
- /acc-code-review src/Domain                        # current branch, only src/Domain
- /acc-code-review feature/payment src/Domain        # branch + path
- /acc-code-review src/Domain medium                 # current branch, path, medium
- /acc-code-review feature/auth src/Auth -- JWT      # full format
- /acc-code-review medium                            # current branch, medium
- /acc-code-review feature/payment low -- task       # branch, low + task matching
```

**Parsing rules:**
1. Split `$ARGUMENTS` by ` -- ` (space-dash-dash-space)
2. First part = arguments, Second part = task description
3. In arguments, search for `high|medium|low` → this is level (default: high)
4. For each remaining argument:
   - If exists as file/folder (test -e) → this is path
   - Otherwise → this is branch
5. Default branch: current via `git branch --show-current`
6. Default path: . (whole project)
7. Target → auto-detect main/master via `git symbolic-ref refs/remotes/origin/HEAD`

## Pre-flight Checks

1. **Verify git repository:**
   ```bash
   git rev-parse --git-dir
   ```
   If not a git repo, report error and stop.

2. **Determine review mode:**

   Check each non-level argument:
   ```bash
   # If argument is a file or folder
   test -e "[argument]" && echo "PATH" || echo "BRANCH"
   ```

   **Two review modes:**
   - **PATH MODE** — Review files/folders (staged + unstaged changes, or all files in path)
   - **BRANCH MODE** — Review branch diff against main/master

3. **PATH MODE flow:**

   If path exists:
   ```bash
   # Get changed files in path (staged + unstaged)
   git diff --name-only HEAD -- [path]

   # If no changes, review ALL PHP files in path
   find [path] -name "*.php" -type f
   ```

   Source: current working directory
   Target: N/A (no branch comparison)

4. **BRANCH MODE flow:**

   a. **Detect target branch (main/master):**
   ```bash
   git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@'
   ```
   Fallback: check if `main` or `master` exists.

   b. **Verify source branch exists:**
   ```bash
   git rev-parse --verify [branch] 2>/dev/null
   ```
   If branch doesn't exist, report error and stop.

   c. **Get changed files:**
   ```bash
   git diff --name-only [target]...[source] -- [path]
   ```
   If no changes, report "No changes to review" and stop.

5. **Validate files found:**
   If no PHP files to review, report "No PHP files to review" and stop.

## Instructions

Execute code review using the `acc-code-review-coordinator` agent.

Use the Task tool to invoke the coordinator:

### PATH MODE (reviewing folder/file)

```
Task: acc-code-review-coordinator
prompt: |
  Perform code review with the following parameters:

  Review mode: PATH
  Path: [detected path]
  Review level: [detected level]
  Task description: [if provided]

  Files to review:
  [list of PHP files in path]

  Execute review according to the level:
  - LOW: PSR + Tests + Encapsulation + Code Smells
  - MEDIUM: LOW + Bugs + Readability + SOLID
  - HIGH: MEDIUM + Security + Performance + Testability + DDD + Architecture

  Return structured report with findings by severity and verdict.
```

### BRANCH MODE (reviewing branch changes)

```
Task: acc-code-review-coordinator
prompt: |
  Perform code review with the following parameters:

  Review mode: BRANCH
  Source branch: [detected or provided branch]
  Target branch: [detected main/master]
  Path filter: [detected path or "." for whole project]
  Review level: [detected level]
  Task description: [if provided]

  Changed files:
  [list of changed files from git diff -- path]

  Execute review according to the level:
  - LOW: PSR + Tests + Encapsulation + Code Smells
  - MEDIUM: LOW + Bugs + Readability + SOLID
  - HIGH: MEDIUM + Security + Performance + Testability + DDD + Architecture

  Return structured report with findings by severity and verdict.
```

## Review Levels

| Level | Scope | Auditors/Reviewers |
|-------|-------|-------------------|
| **LOW** | Quick sanity check | acc-psr-auditor, acc-test-auditor + basic skills |
| **MEDIUM** | Standard review | LOW + acc-bug-hunter, acc-readability-reviewer |
| **HIGH** | Full review | MEDIUM + security, performance, testability, ddd, architecture |

## Expected Output

The coordinator will return a structured markdown report:

### Code Review Report

**Branch:** `source` → `target`
**Commits:** N (hash..hash)
**Changed Files:** N (+added/-removed lines)
**Review Level:** HIGH/MEDIUM/LOW

### Change Summary
- What was done (bullet points)
- Files changed table

### Review Findings
Grouped by severity:
- 🔴 Critical
- 🟠 Major
- 🟡 Minor
- 🟢 Suggestions

### Category Summary
Table with counts per category (Bug, Security, Performance, etc.)

### Task Match Analysis (if task description provided)
- Match score percentage
- Expected vs Found comparison
- Deviation notes

### Verdict
One of:
- ✅ **APPROVE** — No critical/major issues
- ⚠️ **APPROVE WITH COMMENTS** — Minor issues only
- ❌ **REQUEST CHANGES** — Critical or major issues found

## Usage Examples

```bash
# Review current branch (full review)
/acc-code-review

# Review specific branch
/acc-code-review feature/payment

# Quick review
/acc-code-review low

# Standard review of specific branch
/acc-code-review feature/auth medium

# Full review with task matching
/acc-code-review feature/auth -- implement JWT authentication

# Quick review with task matching
/acc-code-review feature/payment low -- add Stripe payment processing

# Review only specific folder (current branch)
/acc-code-review src/Domain

# Review specific branch and folder
/acc-code-review feature/payment src/Domain

# Quick review of specific file
/acc-code-review src/Payment/PaymentService.php low

# Full review with path and task
/acc-code-review feature/auth src/Auth high -- implement JWT
```
