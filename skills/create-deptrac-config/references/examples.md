# DEPTRAC Configuration Examples

## Bounded Context Separation

```yaml
# deptrac.yaml - Multi-bounded context
deptrac:
  paths:
    - ./src

  layers:
    #############################################
    # Bounded Context: Order
    #############################################
    - name: Order
      collectors:
        - type: directory
          value: src/Order/.*

    - name: Order.Domain
      collectors:
        - type: directory
          value: src/Order/Domain/.*

    - name: Order.Application
      collectors:
        - type: directory
          value: src/Order/Application/.*

    - name: Order.Infrastructure
      collectors:
        - type: directory
          value: src/Order/Infrastructure/.*

    #############################################
    # Bounded Context: Payment
    #############################################
    - name: Payment
      collectors:
        - type: directory
          value: src/Payment/.*

    - name: Payment.Domain
      collectors:
        - type: directory
          value: src/Payment/Domain/.*

    - name: Payment.Application
      collectors:
        - type: directory
          value: src/Payment/Application/.*

    #############################################
    # Bounded Context: Shipping
    #############################################
    - name: Shipping
      collectors:
        - type: directory
          value: src/Shipping/.*

    #############################################
    # Shared Kernel
    #############################################
    - name: SharedKernel
      collectors:
        - type: directory
          value: src/SharedKernel/.*

  ruleset:
    # Shared Kernel is available to all
    SharedKernel: []

    # Each context depends only on SharedKernel
    Order.Domain:
      - SharedKernel
    Order.Application:
      - Order.Domain
      - SharedKernel
    Order.Infrastructure:
      - Order.Domain
      - Order.Application
      - SharedKernel

    Payment.Domain:
      - SharedKernel
    Payment.Application:
      - Payment.Domain
      - SharedKernel

    Shipping:
      - SharedKernel

    # Cross-context communication via events/ACL
    # NOT direct dependencies!
```

## Hexagonal Architecture

```yaml
# deptrac.yaml - Ports & Adapters
deptrac:
  paths:
    - ./src

  layers:
    # Core Domain
    - name: Core
      collectors:
        - type: directory
          value: src/Core/.*

    # Ports (interfaces)
    - name: Port.Inbound
      collectors:
        - type: directory
          value: src/Port/Inbound/.*

    - name: Port.Outbound
      collectors:
        - type: directory
          value: src/Port/Outbound/.*

    # Adapters (implementations)
    - name: Adapter.Primary
      collectors:
        - type: directory
          value: src/Adapter/Primary/.*

    - name: Adapter.Secondary
      collectors:
        - type: directory
          value: src/Adapter/Secondary/.*

  ruleset:
    # Core has no dependencies
    Core: []

    # Ports depend on Core
    Port.Inbound:
      - Core
    Port.Outbound:
      - Core

    # Adapters depend on Ports
    Adapter.Primary:
      - Port.Inbound
      - Core
    Adapter.Secondary:
      - Port.Outbound
      - Core
```

## Advanced Collectors

### Class Name Pattern

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

### Interface Implementation

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

### Attribute-based

```yaml
layers:
  - name: Aggregates
    collectors:
      - type: attribute
        value: App\Attribute\Aggregate
```

### Combined Collectors

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

## Baseline Management

```yaml
# deptrac.yaml
deptrac:
  paths:
    - ./src

  baseline: deptrac-baseline.yaml

  # ... layers and ruleset
```

### Generate Baseline

```bash
# Generate baseline for current violations
vendor/bin/deptrac analyse --baseline=deptrac-baseline.yaml

# Analyze with baseline
vendor/bin/deptrac analyse
```

## CI Configuration

### GitHub Actions

```yaml
deptrac:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: shivammathur/setup-php@v2
      with:
        php-version: '8.4'
    - run: composer install
    - run: vendor/bin/deptrac analyse --fail-on-uncovered
```

### GitLab CI

```yaml
deptrac:
  script:
    - vendor/bin/deptrac analyse --formatter=junit --output=deptrac-report.xml
  artifacts:
    reports:
      junit: deptrac-report.xml
```

## Output Formats

```bash
# Console (default)
vendor/bin/deptrac analyse

# JUnit for CI
vendor/bin/deptrac analyse --formatter=junit --output=deptrac.xml

# GraphViz
vendor/bin/deptrac analyse --formatter=graphviz --output=deptrac.dot

# JSON
vendor/bin/deptrac analyse --formatter=json --output=deptrac.json
```

## Common Violations and Fixes

### Domain → Infrastructure

```
VIOLATION: Domain\Order\OrderService depends on Infrastructure\Doctrine\OrderRepository

FIX: Use interface in Domain, implementation in Infrastructure
- Domain\Order\Repository\OrderRepositoryInterface (interface)
- Infrastructure\Persistence\DoctrineOrderRepository (implementation)
```

### Cross-Context Dependency

```
VIOLATION: Order\Application\OrderService depends on Payment\Domain\Payment

FIX: Use Anti-Corruption Layer or Events
- Order emits OrderPlacedEvent
- Payment subscribes to event
- Or use ACL: Order\Infrastructure\PaymentGateway
```
