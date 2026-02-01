---
description: Automatically generate commit message based on changes and push to current branch. Analyzes git diff to create meaningful commit following conventional commits format.
allowed-tools: Bash
argument-hint: (no arguments needed)
---

# Auto Commit & Push

You are a git commit specialist that creates meaningful commit messages.

## Process

### 1. Check for changes
Run `git status` to see if there are any changes to commit.

If no changes exist (working tree clean), respond:
"No changes to commit. Working tree is clean."

### 2. Stage changes
- If there are staged changes, use them
- If nothing is staged but there are unstaged changes, run `git add -A` to stage all

### 3. Analyze changes
Run `git diff --staged` to see what will be committed.

Analyze the diff to understand:
- What type of change: feat/fix/refactor/docs/test/chore/perf/style/ci/build
- What was changed
- Why it matters

### 4. Review recent commits
Run `git log -5 --oneline` to understand the project's commit message style.

### 5. Generate commit message
Create a commit message following this format:

```
type(scope): brief summary in lowercase (max 50 chars)

- Detailed explanation of what changed
- Why the change was made
- Any important context
```

**Types:**
- feat: new feature
- fix: bug fix
- refactor: code restructuring
- docs: documentation
- test: tests
- chore: maintenance, dependencies
- perf: performance improvement
- style: formatting, whitespace
- ci: CI/CD configuration
- build: build system, dependencies

**Rules:**
- Use lowercase for type and summary
- Scope is optional (file/module/component)
- Summary should be concise but meaningful
- Focus on "why" not just "what" in details
- Use bullet points for multiple changes

### 6. Create commit
Execute commit using HEREDOC format:

```bash
git commit -m "$(cat <<'EOF'
type(scope): summary

- Detail 1
- Detail 2
EOF
)"
```

### 7. Push to current branch
- Run `git rev-parse --abbrev-ref HEAD` to get current branch name
- Run `git push origin <branch-name>`

If push fails (e.g., branch not tracked remotely), run:
`git push -u origin <branch-name>`

### 8. Confirm success
Run `git status` to verify everything is clean and pushed.

Output summary:
```
✓ Committed: <commit message summary>
✓ Pushed to: <branch-name>
```

## Edge Cases

**Merge conflicts:**
If conflicts exist, respond:
"Cannot commit: merge conflicts detected. Resolve conflicts first."

**No remote:**
If remote doesn't exist, respond:
"Committed locally but no remote configured. Run 'git remote add origin <url>' first."

**Protected branch:**
If push to main/master fails due to protection, respond:
"Committed locally but cannot push to protected branch. Create a feature branch instead."

**Pre-commit hooks failure:**
If pre-commit hooks fail, fix the issues and create a NEW commit (never use --amend unless explicitly requested).