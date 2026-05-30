---
name: create-component
description: Generates Component pattern classes — private internal services for rich business logic, scoped to one bounded context, not exposed across contexts. Pattern from Layered Architecture (see `layer-arch-knowledge`); analogous to a Strategy + Composite combination used as an implementation detail of a single context. Includes interface, concrete strategies, optional composite, and unit tests.
---

# Component Generator

Generate Component-pattern classes for rich business logic that lives privately inside a bounded context. Unlike a `DomainService` (which can be public across contexts) or a `Service` (cross-context public API), a Component is an **implementation detail of one context** — typically pluggable strategies for a single domain calculation or decision.

## Component characteristics

- **Private to one bounded context**: never imported or used by other modules
- **Interface-driven**: a small focused interface (one or two methods)
- **Multiple implementations** common: strategies, decorators, composites of itself
- **Stateless**: `final readonly` by default; no instance state between calls
- **Rich domain logic**: contains business rules that don't belong directly in entities (e.g. fee calculation policies, scoring algorithms, transformation rules)
- **No infrastructure dependencies in the contract**: depends on Value Objects / Entities; concrete impls may depend on infrastructure ports

## When to use Component vs alternatives

| Scenario | Use this |
|----------|----------|
| Multiple algorithms for one decision (percentage vs flat fee) | **Component** with interface + strategies |
| One operation across multiple aggregates | `acc:create-domain-service` |
| Cross-context public API | `Service/` (regular service, see `layer-arch-knowledge`) |
| One-shot calculation in an entity | Entity method (no separate class) |
| Reusable across contexts | `acc:create-domain-service` in `Domain/Shared/` |

## Structure

A Component folder holds its interface + implementations together:

```
Component/
└── {ConceptName}/
    ├── {ConceptName}Interface.php
    ├── {Strategy1}{ConceptName}.php
    ├── {Strategy2}{ConceptName}.php
    └── Composite{ConceptName}.php  (optional)
```

Example for fee calculation:

```
Component/
└── FeeCalculator/
    ├── FeeCalculatorInterface.php
    ├── PercentageFeeCalculator.php
    ├── FlatFeeCalculator.php
    └── CompositeFeeCalculator.php
```

Folder placement varies by your project's architecture; the pattern itself is independent of where the files live. Whatever folder hosts internal domain helpers in your project is where Components belong.

## Templates

### Interface

```php
<?php

declare(strict_types=1);

namespace Component\{ConceptName};

use ValueObject\Money;

interface {ConceptName}Interface
{
    public function calculate(Money $amount): Money;
}
```

### Strategy implementation

```php
<?php

declare(strict_types=1);

namespace Component\{ConceptName};

use ValueObject\Money;

final readonly class Percentage{ConceptName} implements {ConceptName}Interface
{
    public function __construct(
        private float $rate,
    ) {}

    public function calculate(Money $amount): Money
    {
        return $amount->multiply($this->rate);
    }
}
```

### Flat / constant strategy

```php
<?php

declare(strict_types=1);

namespace Component\{ConceptName};

use ValueObject\Money;

final readonly class Flat{ConceptName} implements {ConceptName}Interface
{
    public function __construct(
        private Money $fee,
    ) {}

    public function calculate(Money $amount): Money
    {
        return $this->fee;
    }
}
```

### Composite (sum of multiple strategies)

```php
<?php

declare(strict_types=1);

namespace Component\{ConceptName};

use ValueObject\Money;

final readonly class Composite{ConceptName} implements {ConceptName}Interface
{
    /** @param list<{ConceptName}Interface> $components */
    public function __construct(
        private array $components,
    ) {}

    public function calculate(Money $amount): Money
    {
        $total = Money::zero($amount->currency());

        foreach ($this->components as $component) {
            $total = $total->add($component->calculate($amount));
        }

        return $total;
    }
}
```

### Unit test

```php
<?php

declare(strict_types=1);

use PHPUnit\Framework\TestCase;

final class Percentage{ConceptName}Test extends TestCase
{
    public function testAppliesRateToAmount(): void
    {
        $calculator = new Percentage{ConceptName}(0.05);

        $result = $calculator->calculate(Money::fromCents(10_000, Currency::USD));

        $this->assertSame(500, $result->cents());
    }

    public function testZeroAmountYieldsZero(): void
    {
        $calculator = new Percentage{ConceptName}(0.10);

        $result = $calculator->calculate(Money::zero(Currency::USD));

        $this->assertSame(0, $result->cents());
    }
}
```

## Generation steps

1. **Identify the concept** the Component represents (e.g. FeeCalculator, ScoringRule, PricingPolicy, DocumentParser).
2. **Define the interface** — a focused method or two. Don't overload it.
3. **Generate at least one concrete strategy**. Common follow-ups: a flat/null variant, a composite for combining strategies.
4. **Wire via DI** — register implementations in the bounded context's services config, often using a service tag so consumers can be injected with `iterable<{ConceptName}Interface>`.
5. **Generate unit tests** for each implementation.

## Detection patterns

```bash
# Find existing Components
Glob: **/Component/**/*Interface.php
Grep: "implements .*Component" --glob "**/*.php"

# Find Components missing tests
Glob: **/Component/**/*.php
# (compare with) tests/**/Component/**/*Test.php

# Find Components exposed across contexts (violation)
Grep: "use .*\\\\(?!{OwningContext})\\\\Component\\\\" --glob "**/*.php"
```

## Antipatterns

| Antipattern | Why it's bad | Fix |
|-------------|--------------|-----|
| Component imported by another bounded context | Breaks context isolation | Move the contract to `Domain/Shared/` or expose via a Service |
| Component with `save()` / persistence calls | Business logic mixed with persistence | Pass aggregates as arguments; persist in Application/Use Case layer |
| Stateful Component (mutable properties) | Hard to reason about; shared-state bugs | Mark `final readonly`; pass state via method arguments |
| Component as one massive class | Misses the Strategy benefit | Split into multiple implementations behind the interface |
| Component injected directly into an Action/Controller | Should go through Application orchestration | Inject into a UseCase / Handler instead |

## References

- See `layer-arch-knowledge` for the 3-layer Domain-centric architecture that names this pattern.
- See `acc:create-domain-service` for the cross-context-capable alternative.
- See `acc:create-strategy` for the underlying GoF pattern.
