# DEPTRAC — Operations

Architecture-agnostic recipes: advanced collectors, baseline management, CI integration, output formats.

---

## Advanced Collectors

DEPTRAC supports more than directory matching. Use these to capture cross-cutting patterns that don't follow folder structure.

### Class-name pattern

```yaml
layers:
  - name: Controllers
    collectors:
      - type: classNameRegex
        value: /.*Controller$/

  - name: Repositories
    collectors:
      - type: classNameRegex
        value: /.*Repository$/

  - name: Services
    collectors:
      - type: classNameRegex
        value: /.*Service$/
```

Useful when class naming is consistent but folder placement varies.

### Interface implementation

```yaml
layers:
  - name: EventHandlers
    collectors:
      - type: implements
        value: App\Domain\EventHandler

  - name: CommandHandlers
    collectors:
      - type: implements
        value: App\Application\CommandHandler
```

Captures everything implementing a given interface, regardless of where the class lives.

### Attribute-based

```yaml
layers:
  - name: Aggregates
    collectors:
      - type: attribute
        value: App\Attribute\Aggregate
```

Captures classes marked with a specific PHP attribute. Useful for picking out entities marked with `#[AggregateRoot]` or `#[ReadModel]` without relying on folder placement.

### Combined collectors

```yaml
layers:
  - name: DomainServices
    collectors:
      - type: bool
        must:
          - type: directory
            value: src/Domain/.*
          - type: classNameRegex
            value: /.*Service$/
        must_not:
          - type: classNameRegex
            value: /.*Test$/
```

`bool` lets you combine collectors with `must:`, `must_not:`, and `must_one_of:`. Use this for layers that need to match more than one criterion.

---

## Baseline Management

For legacy projects with existing violations, generate a baseline so new violations fail CI while existing ones are tracked separately.

```yaml
# deptrac.yaml
deptrac:
  paths:
    - ./src

  baseline: deptrac-baseline.yaml

  # ... layers and ruleset
```

### Generate the baseline

```bash
vendor/bin/deptrac analyse --baseline=deptrac-baseline.yaml
```

This snapshots the current violations into `deptrac-baseline.yaml`. Subsequent runs ignore those exact violations.

### Run with baseline

```bash
vendor/bin/deptrac analyse
```

New violations fail; baselined ones pass quietly. As you fix baselined violations, regenerate the baseline periodically to shrink it.

### Strategy

1. On first install with violations: generate the baseline immediately so CI starts green.
2. Address baselined violations gradually — sort by severity (cross-layer skips, framework-in-domain) and tackle the worst first.
3. Re-baseline whenever a batch is fixed, so the file accurately reflects what's left.

---

## CI Configuration

### GitHub Actions

```yaml
name: Static analysis
on: [push, pull_request]

jobs:
  deptrac:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: shivammathur/setup-php@v2
        with:
          php-version: '8.4'
      - run: composer install --no-progress
      - run: vendor/bin/deptrac analyse --fail-on-uncovered
```

`--fail-on-uncovered` makes CI fail when a class doesn't belong to any layer — useful to catch new top-level folders that you forgot to add to the config.

### GitLab CI

```yaml
deptrac:
  stage: test
  script:
    - composer install --no-progress
    - vendor/bin/deptrac analyse --formatter=junit --output=deptrac-report.xml
  artifacts:
    reports:
      junit: deptrac-report.xml
```

The JUnit formatter integrates with GitLab's test report UI.

---

## Output Formats

```bash
# Console (default) — human-readable
vendor/bin/deptrac analyse

# JUnit XML — for CI report integration
vendor/bin/deptrac analyse --formatter=junit --output=deptrac.xml

# GraphViz — visualize the dependency graph
vendor/bin/deptrac analyse --formatter=graphviz --output=deptrac.dot
dot -Tpng deptrac.dot -o deptrac.png

# JSON — for custom tooling
vendor/bin/deptrac analyse --formatter=json --output=deptrac.json

# GitHub Actions annotations — surface findings inline on PR diffs
vendor/bin/deptrac analyse --formatter=github-actions
```

### Picking a formatter

- **Console** — local development.
- **JUnit** — GitLab CI (built-in report integration) or CI systems that parse JUnit XML.
- **GitHub Actions** — surfaces findings directly on PR file annotations.
- **GraphViz** — for documentation diagrams or one-off architecture reviews.
- **JSON** — for custom dashboards or aggregating across multiple projects.
