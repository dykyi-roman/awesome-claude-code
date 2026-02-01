# Detection Patterns for PSR-1/PSR-12

## Overview

This document provides comprehensive patterns for detecting PSR coding style violations using grep, glob, and static analysis tools.

## PSR-1 Detection

### Side Effects in Declaration Files

```bash
# Echo/print statements in class files
grep -rn "^\s*echo\s" --include="*.php" src/
grep -rn "^\s*print\s" --include="*.php" src/
grep -rn "^\s*print_r\s*(" --include="*.php" src/
grep -rn "^\s*var_dump\s*(" --include="*.php" src/

# Header modifications
grep -rn "^\s*header\s*(" --include="*.php" src/
grep -rn "^\s*setcookie\s*(" --include="*.php" src/

# Session operations
grep -rn "^\s*session_start" --include="*.php" src/
grep -rn "^\s*session_destroy" --include="*.php" src/
grep -rn "^\s*session_regenerate_id" --include="*.php" src/

# Configuration changes
grep -rn "^\s*ini_set\s*(" --include="*.php" src/
grep -rn "^\s*error_reporting\s*(" --include="*.php" src/
grep -rn "^\s*date_default_timezone_set" --include="*.php" src/

# File operations at top level
grep -rn "^require\s" --include="*.php" src/
grep -rn "^require_once\s" --include="*.php" src/
grep -rn "^include\s" --include="*.php" src/
grep -rn "^include_once\s" --include="*.php" src/

# Output buffering
grep -rn "^\s*ob_start\s*(" --include="*.php" src/
grep -rn "^\s*ob_flush\s*(" --include="*.php" src/
grep -rn "^\s*flush\s*(" --include="*.php" src/

# Die/exit calls
grep -rn "^\s*die\s*(" --include="*.php" src/
grep -rn "^\s*exit\s*(" --include="*.php" src/
```

### Invalid Naming Conventions

```bash
# Class names - should be StudlyCaps
# Lowercase first character
grep -rn "^class\s\+[a-z]" --include="*.php" src/

# Contains underscore
grep -rn "^class\s\+[A-Za-z]*_" --include="*.php" src/

# All uppercase
grep -rn "^class\s\+[A-Z][A-Z][A-Z]" --include="*.php" src/

# Method names - should be camelCase
# Uppercase first character
grep -rn "function\s\+[A-Z][a-zA-Z]*\s*(" --include="*.php" src/

# Contains underscore (excluding magic methods)
grep -rn "function\s\+[a-z][a-z]*_[a-z]" --include="*.php" src/

# Constants - should be UPPER_CASE
# Lowercase constants
grep -rn "const\s\+[a-z]" --include="*.php" src/
```

### Invalid PHP Tags

```bash
# Short open tags
grep -rn "<?[^p=]" --include="*.php" src/

# ASP-style tags
grep -rn "<%" --include="*.php" src/

# Missing closing tag (optional, actually recommended to omit)
```

## PSR-12 Detection

### Indentation Issues

```bash
# Tab characters
grep -rn $'\t' --include="*.php" src/

# More than 4 spaces at start of line (potential issue)
grep -rn "^        [^ ]" --include="*.php" src/
```

### Whitespace Issues

```bash
# Trailing whitespace
grep -rn "\s$" --include="*.php" src/

# Multiple blank lines
grep -rn -A1 "^$" --include="*.php" src/ | grep -B1 "^$"

# No space after control keywords
grep -rn "\(if\|for\|foreach\|while\|switch\|catch\)(" --include="*.php" src/

# Space before opening parenthesis in function call
grep -rn "[a-zA-Z_]\s\+(" --include="*.php" src/ | grep -v "if\|for\|foreach\|while\|switch\|catch\|function"
```

### Brace Placement

```bash
# Opening brace on same line as class/interface/trait
grep -rn "^\s*\(class\|interface\|trait\|enum\).*{$" --include="*.php" src/

# Opening brace not on same line as function
grep -rn "function.*$" --include="*.php" src/ | grep -v "{"
```

### Keyword Case

```bash
# Uppercase keywords
grep -rn "\sTRUE\s\|\sFALSE\s\|\sNULL\s" --include="*.php" src/
grep -rn "=\s*TRUE\|=\s*FALSE\|=\s*NULL" --include="*.php" src/

# Long type names
grep -rn "boolean\s" --include="*.php" src/
grep -rn "integer\s" --include="*.php" src/
grep -rn ": boolean" --include="*.php" src/
grep -rn ": integer" --include="*.php" src/
```

### Import Statement Issues

```bash
# Multiple classes per use statement (not grouped)
grep -rn "^use.*,.*;" --include="*.php" src/ | grep -v "{"

# Unsorted imports (check manually)
grep -rn "^use\s" --include="*.php" src/
```

### Control Structure Issues

```bash
# else/elseif on new line
grep -rn "^}\s*$" -A1 --include="*.php" src/ | grep -E "else|elseif"

# Missing space in ternary
grep -rn "\?[^ ]" --include="*.php" src/
grep -rn "[^ ]:" --include="*.php" src/
```

## PHP_CodeSniffer Configuration

```xml
<?xml version="1.0"?>
<ruleset name="PSR-12 Strict">
    <description>PSR-12 with additional strict rules</description>

    <file>src</file>
    <file>tests</file>

    <exclude-pattern>vendor/*</exclude-pattern>
    <exclude-pattern>*.blade.php</exclude-pattern>

    <!-- PSR-12 base -->
    <rule ref="PSR12"/>

    <!-- Additional strict rules -->
    <rule ref="Generic.Files.LineLength">
        <properties>
            <property name="lineLimit" value="120"/>
            <property name="absoluteLineLimit" value="150"/>
        </properties>
    </rule>

    <rule ref="Generic.Metrics.CyclomaticComplexity">
        <properties>
            <property name="complexity" value="10"/>
        </properties>
    </rule>

    <rule ref="Generic.Metrics.NestingLevel">
        <properties>
            <property name="nestingLevel" value="4"/>
        </properties>
    </rule>

    <!-- Detect side effects -->
    <rule ref="PSR1.Files.SideEffects"/>

    <!-- Arguments -->
    <arg name="colors"/>
    <arg value="sp"/>
    <arg name="extensions" value="php"/>
</ruleset>
```

## Automated Detection Script

```bash
#!/bin/bash
# psr-check.sh - Quick PSR-1/PSR-12 violation detector

SRC_DIR="${1:-src}"
ERRORS=0

echo "=== PSR-1 Checks ==="

echo -n "Checking for side effects in class files... "
COUNT=$(grep -rln "^\s*\(echo\|print\|header\|session_start\|ini_set\)\s" --include="*.php" "$SRC_DIR" 2>/dev/null | wc -l)
if [ "$COUNT" -gt 0 ]; then
    echo "FOUND: $COUNT files"
    ERRORS=$((ERRORS + COUNT))
else
    echo "OK"
fi

echo -n "Checking class naming conventions... "
COUNT=$(grep -rln "^class\s\+[a-z]" --include="*.php" "$SRC_DIR" 2>/dev/null | wc -l)
if [ "$COUNT" -gt 0 ]; then
    echo "FOUND: $COUNT files"
    ERRORS=$((ERRORS + COUNT))
else
    echo "OK"
fi

echo ""
echo "=== PSR-12 Checks ==="

echo -n "Checking for tab characters... "
COUNT=$(grep -rln $'\t' --include="*.php" "$SRC_DIR" 2>/dev/null | wc -l)
if [ "$COUNT" -gt 0 ]; then
    echo "FOUND: $COUNT files"
    ERRORS=$((ERRORS + COUNT))
else
    echo "OK"
fi

echo -n "Checking for trailing whitespace... "
COUNT=$(grep -rln "\s$" --include="*.php" "$SRC_DIR" 2>/dev/null | wc -l)
if [ "$COUNT" -gt 0 ]; then
    echo "FOUND: $COUNT files"
    ERRORS=$((ERRORS + COUNT))
else
    echo "OK"
fi

echo -n "Checking for uppercase keywords... "
COUNT=$(grep -rln "\sTRUE\s\|\sFALSE\s\|\sNULL\s" --include="*.php" "$SRC_DIR" 2>/dev/null | wc -l)
if [ "$COUNT" -gt 0 ]; then
    echo "FOUND: $COUNT files"
    ERRORS=$((ERRORS + COUNT))
else
    echo "OK"
fi

echo -n "Checking for missing space after control keywords... "
COUNT=$(grep -rln "\(if\|for\|foreach\|while\|switch\|catch\)(" --include="*.php" "$SRC_DIR" 2>/dev/null | wc -l)
if [ "$COUNT" -gt 0 ]; then
    echo "FOUND: $COUNT files"
    ERRORS=$((ERRORS + COUNT))
else
    echo "OK"
fi

echo ""
echo "=== Summary ==="
if [ "$ERRORS" -gt 0 ]; then
    echo "Total issues found: $ERRORS"
    exit 1
else
    echo "All checks passed!"
    exit 0
fi
```

## CI Integration

### GitHub Actions

```yaml
name: PSR Coding Style

on: [push, pull_request]

jobs:
  phpcs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup PHP
        uses: shivammathur/setup-php@v2
        with:
          php-version: '8.5'
          tools: phpcs, php-cs-fixer

      - name: Run PHP_CodeSniffer
        run: phpcs --standard=PSR12 src/ tests/

      - name: Run PHP-CS-Fixer (dry-run)
        run: php-cs-fixer fix --dry-run --diff --config=.php-cs-fixer.php
```

### GitLab CI

```yaml
phpcs:
  image: php:8.5-cli
  before_script:
    - composer global require squizlabs/php_codesniffer
  script:
    - ~/.composer/vendor/bin/phpcs --standard=PSR12 src/ tests/
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```
