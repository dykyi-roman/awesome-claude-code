---
description: Automatically generate commit message based on changes and push to current branch. Analyzes git diff to create meaningful commit following conventional commits format. Optionally creates and pushes a git tag.
allowed-tools: Bash
model: sonnet
argument-hint: [tag-name] [-- additional instructions]
---

# Auto Commit & Push

You are a git commit specialist that creates meaningful commit messages.

## Input Parsing

Parse `$ARGUMENTS` to extract tag name and optional meta-instructions:

```
Format: [tag-name] [-- <meta-instructions>]

Examples:
- /acc-commit
- /acc-commit v2.5.0
- /acc-commit -- focus on security changes
- /acc-commit v2.5.0 -- mention breaking changes
- /acc-commit -- use Russian for commit message
```

**Parsing rules:**
1. Split `$ARGUMENTS` by ` -- ` (space-dash-dash-space)
2. First part = **tag name** (optional, version tag to create)
3. Second part = **meta-instructions** (optional, commit message hints)

If meta-instructions provided, use them to:
- Focus commit message on specific aspects
- Use specific language for message
- Highlight specific types of changes
- Add specific context to commit message

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
- **DO NOT add "Co-Authored-By:" lines** — keep the commit message clean

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

### 8. Create tag (if $ARGUMENTS provided)

If `$ARGUMENTS` contains a tag name:

1. Create the tag:
   ```bash
   git tag $ARGUMENTS
   ```

2. Push the tag:
   ```bash
   git push origin $ARGUMENTS
   ```

If tag already exists, respond:
"Tag '$ARGUMENTS' already exists. Use a different tag name or delete existing tag first."

### 9. Confirm success
Run `git status` to verify everything is clean and pushed.

Output summary (without tag):
```
✓ Committed: <commit message summary>
✓ Pushed to: <branch-name>
```

Output summary (with tag):
```
✓ Committed: <commit message summary>
✓ Pushed to: <branch-name>
✓ Tagged: <tag-name>
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