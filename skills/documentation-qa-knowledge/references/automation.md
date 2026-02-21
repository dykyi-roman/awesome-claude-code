# Automation

## Documentation CI/CD Integration

### Overview

Automate documentation quality checks to catch issues before they reach production.
Integrate validation tools into CI pipelines alongside tests and static analysis.

## markdownlint

### GitHub Actions Integration

```yaml
# .github/workflows/docs.yml
name: Documentation Quality

on:
  pull_request:
    paths:
      - '**/*.md'
      - '.markdownlint.json'

jobs:
  markdown-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Lint Markdown
        uses: DavidAnson/markdownlint-cli2-action@v19
        with:
          globs: |
            **/*.md
            !vendor/**
            !node_modules/**
```

### GitLab CI Integration

```yaml
# .gitlab-ci.yml
markdown-lint:
  stage: test
  image: davidanson/markdownlint-cli2:latest
  script:
    - markdownlint-cli2 "**/*.md" "!vendor/**"
  rules:
    - changes:
        - "**/*.md"
```

### Configuration

```json
// .markdownlint.json
{
  "default": true,
  "MD013": { "line_length": 120 },
  "MD033": { "allowed_elements": ["details", "summary", "br"] },
  "MD041": false,
  "MD024": { "siblings_only": true }
}
```

## markdown-link-check

### GitHub Actions Integration

```yaml
# .github/workflows/docs.yml (add to existing)
  link-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Check Markdown Links
        uses: gaurav-nelson/github-action-markdown-link-check@v1
        with:
          use-quiet-mode: 'yes'
          config-file: '.markdown-link-check.json'
          folder-path: 'docs/'
          file-path: './README.md,./CHANGELOG.md,./CONTRIBUTING.md'
```

### Configuration

```json
// .markdown-link-check.json
{
  "ignorePatterns": [
    { "pattern": "^https://localhost" },
    { "pattern": "^https://api\\.example\\.com" }
  ],
  "replacementPatterns": [
    {
      "pattern": "^/docs/",
      "replacement": "{{BASEURL}}/docs/"
    }
  ],
  "httpHeaders": [
    {
      "urls": ["https://github.com"],
      "headers": {
        "Accept-Encoding": "zstd, br, gzip, deflate"
      }
    }
  ],
  "timeout": "10s",
  "retryOn429": true,
  "retryCount": 3,
  "aliveStatusCodes": [200, 206]
}
```

## Mermaid Diagram Validation

### GitHub Actions Integration

```yaml
  mermaid-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: 22

      - name: Install Mermaid CLI
        run: npm install -g @mermaid-js/mermaid-cli

      - name: Validate Mermaid Diagrams
        run: |
          # Extract and validate all mermaid blocks from markdown files
          find docs/ -name "*.md" -exec grep -l '```mermaid' {} \; | while read file; do
            echo "Validating diagrams in: $file"
            # Extract mermaid blocks and validate each
            awk '/```mermaid/,/```/' "$file" | sed '/```/d' > /tmp/diagram.mmd
            if [ -s /tmp/diagram.mmd ]; then
              mmdc -i /tmp/diagram.mmd -o /tmp/diagram.svg 2>&1 || echo "FAILED: $file"
            fi
          done
```

## PHPDoc Coverage Checking

### GitHub Actions Integration

```yaml
  phpdoc-coverage:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup PHP
        uses: shivammathur/setup-php@v2
        with:
          php-version: '8.4'

      - name: Install Dependencies
        run: composer install --no-progress

      - name: Check PHPDoc Coverage
        run: |
          # Count public methods
          TOTAL=$(grep -rn "public function " src/ | wc -l | tr -d ' ')
          # Count documented methods (PHPDoc before method)
          DOCUMENTED=$(grep -rn -B1 "public function " src/ | grep -c "/\*\*" | tr -d ' ')
          COVERAGE=$((DOCUMENTED * 100 / TOTAL))
          echo "PHPDoc coverage: ${COVERAGE}% (${DOCUMENTED}/${TOTAL})"
          if [ "$COVERAGE" -lt 80 ]; then
            echo "::error::PHPDoc coverage ${COVERAGE}% is below 80% threshold"
            exit 1
          fi
```

### Using phpDocumentor

```yaml
      - name: Generate API Docs
        run: |
          wget https://phpdoc.org/phpDocumentor.phar
          php phpDocumentor.phar --directory=src/ --target=docs/api/generated/
          # Check for undocumented elements
          grep -c "No summary" docs/api/generated/**/*.html && exit 1 || true
```

## Auto-Generating Changelog

### conventional-changelog

```yaml
  changelog:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: 22

      - name: Generate Changelog
        run: |
          npm install -g conventional-changelog-cli
          conventional-changelog -p conventionalcommits -i CHANGELOG.md -s
```

### Git-Based Changelog

```bash
#!/bin/bash
# scripts/generate-changelog.sh

VERSION=$1
PREVIOUS_TAG=$(git describe --tags --abbrev=0 HEAD^)

echo "## [$VERSION] - $(date +%Y-%m-%d)"
echo ""

# Features
FEATURES=$(git log ${PREVIOUS_TAG}..HEAD --pretty=format:"%s" | grep "^feat" | sed 's/^feat[:(]//' | sed 's/):/: /')
if [ -n "$FEATURES" ]; then
    echo "### Added"
    echo "$FEATURES" | while read line; do echo "- $line"; done
    echo ""
fi

# Fixes
FIXES=$(git log ${PREVIOUS_TAG}..HEAD --pretty=format:"%s" | grep "^fix" | sed 's/^fix[:(]//' | sed 's/):/: /')
if [ -n "$FIXES" ]; then
    echo "### Fixed"
    echo "$FIXES" | while read line; do echo "- $line"; done
    echo ""
fi
```

## doctoc (Table of Contents)

### GitHub Actions Integration

```yaml
  toc-update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Generate TOC
        run: |
          npm install -g doctoc
          doctoc docs/ --github --title "## Table of Contents"
          # Check if TOC changed (outdated in PR)
          git diff --exit-code docs/ || {
            echo "::error::Table of Contents is outdated. Run 'doctoc docs/' locally."
            exit 1
          }
```

### Local Usage

```bash
# Generate TOC for specific file
npx doctoc docs/architecture/README.md --github

# Generate TOC for all docs
npx doctoc docs/ --github --title "## Table of Contents"

# Add markers in your markdown for TOC placement
# <!-- START doctoc -->
# <!-- END doctoc -->
```

## Complete CI Pipeline

### GitHub Actions (Full Documentation Workflow)

```yaml
# .github/workflows/docs.yml
name: Documentation Quality

on:
  pull_request:
    paths:
      - '**/*.md'
      - 'src/**/*.php'
      - '.markdownlint.json'
      - '.markdown-link-check.json'

jobs:
  markdown-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: DavidAnson/markdownlint-cli2-action@v19
        with:
          globs: '**/*.md !vendor/**'

  link-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: gaurav-nelson/github-action-markdown-link-check@v1
        with:
          config-file: '.markdown-link-check.json'

  phpdoc-coverage:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: shivammathur/setup-php@v2
        with:
          php-version: '8.4'
      - run: composer install --no-progress
      - name: Check PHPDoc Coverage
        run: |
          TOTAL=$(grep -rn "public function " src/ | wc -l | tr -d ' ')
          DOCUMENTED=$(grep -rn -B1 "public function " src/ | grep -c "/\*\*" | tr -d ' ')
          COVERAGE=$((DOCUMENTED * 100 / TOTAL))
          echo "PHPDoc coverage: ${COVERAGE}%"
          [ "$COVERAGE" -ge 80 ] || exit 1

  toc-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npx doctoc docs/ --github
      - run: git diff --exit-code docs/
```

## Detection Patterns

```bash
# Check if CI validates docs
Grep: "markdownlint|markdown-link-check|doctoc" --glob ".github/workflows/*.yml"
Grep: "markdownlint|markdown-link-check" --glob ".gitlab-ci.yml"

# Check for markdownlint config
Glob: .markdownlint.json
Glob: .markdownlint.yaml

# Check for link checker config
Glob: .markdown-link-check.json

# Check for auto-generated sections
Grep: "<!-- START doctoc -->|<!-- AUTO-GENERATED -->" --glob "**/*.md"

# Check for PHPDoc validation in CI
Grep: "phpdoc|phpDocumentor" --glob ".github/workflows/*.yml"
```

## Summary

| Tool | Purpose | CI Integration |
|------|---------|----------------|
| **markdownlint** | Markdown style and formatting | GitHub Action, GitLab job, pre-commit hook |
| **markdown-link-check** | Detect broken internal/external links | GitHub Action, scheduled job |
| **mermaid-cli** | Validate Mermaid diagram syntax | npm script in CI pipeline |
| **PHPDoc coverage** | Ensure public API is documented | Custom script in CI |
| **conventional-changelog** | Generate CHANGELOG from commits | Post-merge hook, release job |
| **doctoc** | Auto-generate Table of Contents | Pre-commit hook, CI check |
| **phpDocumentor** | Generate HTML API reference | CI build step, deploy to pages |
