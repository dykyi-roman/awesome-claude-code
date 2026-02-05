# Hooks

Hooks execute shell commands in response to Claude Code events. Copy the hooks you need to your `.claude/settings.json`.

## Available Hooks

### PSR & Code Style

| Hook                                          | Type  | Event       | Description                          |
|-----------------------------------------------|-------|-------------|--------------------------------------|
| [Auto-format PHP](#auto-format-php)           | info  | Edit\|Write | Runs `php-cs-fixer` on PHP files     |
| [Require strict_types](#require-strict_types) | block | Write       | Requires `declare(strict_types=1)`   |
| [PHP Syntax Check](#php-syntax-check)         | info  | Edit\|Write | Validates PHP syntax                 |
| [PHPDoc Required](#phpdoc-required)           | warn  | Edit\|Write | Warns if public methods lack PHPDoc  |

### DDD & Architecture

| Hook                                                    | Type  | Event       | Description                              |
|---------------------------------------------------------|-------|-------------|------------------------------------------|
| [Final Domain Classes](#final-domain-classes)           | warn  | Edit\|Write | Warns if Domain class not final          |
| [Readonly Classes Check](#readonly-classes-check)       | warn  | Edit\|Write | Warns if Domain class not readonly       |
| [Value Object Immutability](#value-object-immutability) | warn  | Edit\|Write | Ensures Value Objects are immutable      |
| [Aggregate Protection](#aggregate-protection)           | warn  | Edit\|Write | Protects Aggregate internal state        |
| [No Direct SQL](#no-direct-sql)                         | warn  | Edit\|Write | Detects raw SQL outside Repository       |

### Code Quality

| Hook                                                        | Type  | Event       | Description                              |
|-------------------------------------------------------------|-------|-------------|------------------------------------------|
| [File Size Check](#file-size-check)                         | warn  | Edit\|Write | Detects God Class antipattern            |
| [Constructor Injection Only](#constructor-injection-only)   | warn  | Edit\|Write | Warns about setter/property injection    |
| [No Public Properties](#no-public-properties)               | warn  | Edit\|Write | Warns about mutable public properties    |
| [No Sleep/Exit](#no-sleepexit)                              | warn  | Edit\|Write | Detects sleep/exit/die in code           |

### Security & Safety

| Hook                                            | Type  | Event       | Description                              |
|-------------------------------------------------|-------|-------------|------------------------------------------|
| [Protect vendor/](#protect-vendor)              | block | Edit\|Write | Prevents modification of vendor/         |
| [No var_dump/print_r](#no-var_dumpprint_r)      | block | Edit\|Write | Blocks debug output in code              |
| [No Hardcoded Paths](#no-hardcoded-paths)       | warn  | Edit\|Write | Detects hardcoded file system paths      |
| [No Global State](#no-global-state)             | warn  | Edit\|Write | Detects global variables usage           |

### Git & Workflow

| Hook                                          | Type  | Event       | Description                              |
|-----------------------------------------------|-------|-------------|------------------------------------------|
| [Auto-run Tests](#auto-run-tests)             | info  | Edit\|Write | Runs tests for modified class            |
| [No Direct Commits](#no-direct-commits)       | block | PreToolUse  | Forbids commits to main/master           |
| [Protect Migrations](#protect-migrations)     | block | PreToolUse  | Prevents editing existing migrations     |
| [Test Without Source](#test-without-source)   | warn  | PreToolUse  | Warns when changing only tests           |

## Hook Types

- **block** — Stops operation on failure (`exit 1`)
- **warn** — Shows warning but continues
- **info** — Shows information, never fails

## Hooks Reference

### Auto-format PHP

Automatically formats PHP files with PSR-12 after editing.

**Requirements:** `composer global require friendsofphp/php-cs-fixer`

```json
{
  "matcher": "Edit|Write",
  "hooks": [
    {
      "type": "command",
      "command": "if [[ \"$CLAUDE_FILE_PATHS\" == *.php ]]; then php-cs-fixer fix \"$CLAUDE_FILE_PATHS\" --quiet 2>/dev/null || true; fi"
    }
  ]
}
```

---

### Require strict_types

Blocks creation of PHP files without `declare(strict_types=1)`.

```json
{
  "matcher": "Write",
  "hooks": [
    {
      "type": "command",
      "command": "if [[ \"$CLAUDE_FILE_PATHS\" == *.php ]] && ! head -3 \"$CLAUDE_FILE_PATHS\" | grep -q 'strict_types=1'; then echo '❌ Missing declare(strict_types=1)'; exit 1; fi"
    }
  ]
}
```

---

### Protect vendor/

Prevents any modification to vendor/ directory.

```json
{
  "matcher": "Edit|Write",
  "hooks": [
    {
      "type": "command",
      "command": "if [[ \"$CLAUDE_FILE_PATHS\" == *vendor/* ]]; then echo '❌ Cannot modify vendor/'; exit 1; fi"
    }
  ]
}
```

---

### PHP Syntax Check

Validates PHP syntax after editing.

```json
{
  "matcher": "Edit|Write",
  "hooks": [
    {
      "type": "command",
      "command": "if [[ \"$CLAUDE_FILE_PATHS\" == *.php ]]; then php -l \"$CLAUDE_FILE_PATHS\" 2>&1 | grep -v 'No syntax errors' || true; fi"
    }
  ]
}
```

---

### Auto-run Tests

Automatically runs PHPUnit tests for the modified class.

**Requirements:** PHPUnit configured in project

```json
{
  "matcher": "Edit|Write",
  "hooks": [
    {
      "type": "command",
      "command": "if [[ \"$CLAUDE_FILE_PATHS\" == src/*.php ]]; then class=$(basename \"${CLAUDE_FILE_PATHS%.php}\"); phpunit --filter \"$class\" 2>/dev/null || true; fi"
    }
  ]
}
```

---

### Final Domain Classes

Warns when Domain layer classes are not declared as `final`.

```json
{
  "matcher": "Edit|Write",
  "hooks": [
    {
      "type": "command",
      "command": "if [[ \"$CLAUDE_FILE_PATHS\" == */Domain/*.php ]] && grep -q '^class ' \"$CLAUDE_FILE_PATHS\" && ! grep -q '^final class\\|^readonly class\\|^final readonly class' \"$CLAUDE_FILE_PATHS\"; then echo '⚠️ Domain classes should be final'; fi"
    }
  ]
}
```

---

### File Size Check

Warns when PHP file exceeds 300 lines (potential God Class).

```json
{
  "matcher": "Edit|Write",
  "hooks": [
    {
      "type": "command",
      "command": "if [[ \"$CLAUDE_FILE_PATHS\" == *.php ]]; then lines=$(wc -l < \"$CLAUDE_FILE_PATHS\"); if [[ $lines -gt 300 ]]; then echo \"⚠️ File has $lines lines (>300). Consider splitting.\"; fi; fi"
    }
  ]
}
```

---

### PHPDoc Required

Warns when public methods in Domain layer lack PHPDoc documentation.

```json
{
  "matcher": "Edit|Write",
  "hooks": [
    {
      "type": "command",
      "command": "if [[ \"$CLAUDE_FILE_PATHS\" == */Domain/*.php ]] && grep -B1 'public function' \"$CLAUDE_FILE_PATHS\" | grep -qv '@'; then echo '⚠️ Public methods should have PHPDoc'; fi"
    }
  ]
}
```

## DDD & Architecture Hooks

---

### Readonly Classes Check

Warns when Domain layer classes are not declared as `readonly`.

```json
{
  "matcher": "Edit|Write",
  "hooks": [
    {
      "type": "command",
      "command": "if [[ \"$CLAUDE_FILE_PATHS\" == */Domain/*.php ]] && grep -q '^class\\|^final class' \"$CLAUDE_FILE_PATHS\" && ! grep -q 'readonly class' \"$CLAUDE_FILE_PATHS\"; then echo '⚠️ Domain classes should be readonly'; fi"
    }
  ]
}
```

---

### Value Object Immutability

Ensures Value Objects remain immutable by detecting setters or property mutations.

```json
{
  "matcher": "Edit|Write",
  "hooks": [
    {
      "type": "command",
      "command": "if [[ \"$CLAUDE_FILE_PATHS\" == */ValueObject/*.php ]] && grep -qE 'public function set|->.*=' \"$CLAUDE_FILE_PATHS\"; then echo '⚠️ Value Objects must be immutable'; fi"
    }
  ]
}
```

---

### Aggregate Protection

Warns when Aggregate classes expose internal state via public properties.

```json
{
  "matcher": "Edit|Write",
  "hooks": [
    {
      "type": "command",
      "command": "if [[ \"$CLAUDE_FILE_PATHS\" == */Aggregate/*.php ]] && grep -q 'public \\$' \"$CLAUDE_FILE_PATHS\"; then echo '⚠️ Aggregate internals should not be public'; fi"
    }
  ]
}
```

---

### No Direct SQL

Detects raw SQL queries outside Repository classes. SQL should be encapsulated in repositories.

```json
{
  "matcher": "Edit|Write",
  "hooks": [
    {
      "type": "command",
      "command": "if [[ \"$CLAUDE_FILE_PATHS\" == *.php ]] && grep -qiE 'SELECT\\s+\\*|INSERT INTO|UPDATE .+ SET|DELETE FROM' \"$CLAUDE_FILE_PATHS\" && [[ \"$CLAUDE_FILE_PATHS\" != *Repository* ]]; then echo '⚠️ Raw SQL found outside Repository'; fi"
    }
  ]
}
```

## Code Quality Hooks

---

### Constructor Injection Only

Warns about setter injection or property injection via annotations. Use constructor injection instead.

```json
{
  "matcher": "Edit|Write",
  "hooks": [
    {
      "type": "command",
      "command": "if [[ \"$CLAUDE_FILE_PATHS\" == *.php ]] && grep -qE '@(Inject|Required|Autowired)' \"$CLAUDE_FILE_PATHS\"; then echo '⚠️ Use constructor injection instead of annotations'; fi"
    }
  ]
}
```

---

### No Public Properties

Warns about mutable public properties. Use getters or readonly properties instead.

```json
{
  "matcher": "Edit|Write",
  "hooks": [
    {
      "type": "command",
      "command": "if [[ \"$CLAUDE_FILE_PATHS\" == *.php ]] && grep -qE 'public \\$|public string \\$|public int \\$|public array \\$' \"$CLAUDE_FILE_PATHS\" && ! grep -qE 'public readonly' \"$CLAUDE_FILE_PATHS\"; then echo '⚠️ Avoid public properties, use getters or readonly'; fi"
    }
  ]
}
```

---

### No Sleep/Exit

Warns about usage of `sleep()`, `exit()`, or `die()` in production code.

```json
{
  "matcher": "Edit|Write",
  "hooks": [
    {
      "type": "command",
      "command": "if [[ \"$CLAUDE_FILE_PATHS\" == *.php ]] && grep -qE '\\bsleep\\b|\\bexit\\b|\\bdie\\b' \"$CLAUDE_FILE_PATHS\"; then echo '⚠️ Avoid sleep/exit/die in production code'; fi"
    }
  ]
}
```

## Security & Safety Hooks

---

### No var_dump/print_r

Blocks code containing debug output functions.

```json
{
  "matcher": "Edit|Write",
  "hooks": [
    {
      "type": "command",
      "command": "if [[ \"$CLAUDE_FILE_PATHS\" == *.php ]] && grep -qE '\\bvar_dump\\b|\\bprint_r\\b|\\bdd\\b|\\bdump\\b' \"$CLAUDE_FILE_PATHS\"; then echo '❌ Debug output detected'; exit 1; fi"
    }
  ]
}
```

---

### No Hardcoded Paths

Warns about hardcoded file system paths. Use configuration or environment variables instead.

```json
{
  "matcher": "Edit|Write",
  "hooks": [
    {
      "type": "command",
      "command": "if [[ \"$CLAUDE_FILE_PATHS\" == *.php ]] && grep -qE \"'/var/|'/tmp/|'/home/|C:\\\\\\\\\" \"$CLAUDE_FILE_PATHS\"; then echo '⚠️ Hardcoded paths detected, use config'; fi"
    }
  ]
}
```

---

### No Global State

Detects usage of global variables, `$GLOBALS`, `$_SESSION`, or `$_REQUEST`.

```json
{
  "matcher": "Edit|Write",
  "hooks": [
    {
      "type": "command",
      "command": "if [[ \"$CLAUDE_FILE_PATHS\" == *.php ]] && grep -qE '\\bglobal \\$|\\$GLOBALS|\\$_SESSION|\\$_REQUEST' \"$CLAUDE_FILE_PATHS\"; then echo '⚠️ Avoid global state'; fi"
    }
  ]
}
```

## PreToolUse Hooks

PreToolUse hooks execute **before** the tool runs — ideal for validation and blocking.

---

### No Direct Commits

Forbids direct commits to main/master branches.

```json
{
  "matcher": "Bash(git commit*)",
  "hooks": [
    {
      "type": "command",
      "command": "branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null); if [[ \"$branch\" == 'main' || \"$branch\" == 'master' ]]; then echo '❌ Direct commits to '$branch' forbidden. Create a feature branch.'; exit 1; fi"
    }
  ]
}
```

---

### Protect Migrations

Prevents editing existing database migrations. Create new migrations instead.

```json
{
  "matcher": "Edit",
  "hooks": [
    {
      "type": "command",
      "command": "if [[ \"$CLAUDE_FILE_PATHS\" == *migrations/* ]]; then echo '❌ Cannot edit existing migrations. Create a new migration instead.'; exit 1; fi"
    }
  ]
}
```

---

### Test Without Source

Warns when modifying test files without corresponding source code changes.

```json
{
  "matcher": "Edit|Write",
  "hooks": [
    {
      "type": "command",
      "command": "if [[ \"$CLAUDE_FILE_PATHS\" == *Test.php ]] && ! git diff --name-only 2>/dev/null | grep -qv 'Test.php'; then echo '⚠️ Changing tests without changing source code'; fi"
    }
  ]
}
```

## Installation

Add hooks to your `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash(git commit*)",
        "hooks": [
          // paste PreToolUse hooks here
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          // paste PostToolUse hooks here
        ]
      }
    ]
  }
}
```

## Environment Variables

Available in hook commands:

| Variable | Description |
|----------|-------------|
| `CLAUDE_FILE_PATHS` | Path to the modified file |
| `CLAUDE_TOOL_NAME` | Name of the tool that triggered the hook |

## Tips

- Use `|| true` at the end to prevent blocking on errors
- Use `2>/dev/null` to suppress stderr
- Use `exit 1` to block the operation
- Test hooks manually before adding to settings

---

## Navigation

[← Back to README](../README.md) | [Commands](commands.md) | [Agents](agents.md) | [Skills](skills.md) | [MCP](mcp.md)