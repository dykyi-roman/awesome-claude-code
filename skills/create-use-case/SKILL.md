---
name: create-use-case
description: Generates Application Use Cases for PHP 8.4. Creates orchestration services that coordinate domain objects, handle transactions, and dispatch events. Includes unit tests.
---

# Use Case Generator

Generate Application-layer Use Cases that orchestrate domain operations.

## Use Case Characteristics

- **Single responsibility**: One operation per use case
- **Orchestration**: Coordinates domain objects
- **Transaction boundary**: Manages atomicity
- **Event dispatch**: Publishes domain events
- **No business logic**: Delegates to domain
- **Framework agnostic**: No HTTP/CLI concerns

## When to Use

| Scenario | Example |
|----------|---------|
| Create operation | `CreateOrderUseCase` |
| State transition | `ConfirmOrderUseCase` |
| External service integration | `ProcessPaymentUseCase` |
| Multi-step workflow | `CheckoutUseCase` |

---

## Generation Process

### Step 1: Generate Use Case

Place in a `UseCase/` folder wherever your project coordinates use cases.

1. `{Name}UseCase.php` — Main orchestration class

### Step 2: Generate Input DTO

Place in a sibling `DTO/` folder.

1. `{Name}Input.php` — Input data container

### Step 3: Generate Output DTO

Co-located with the Input DTO in the same `DTO/` folder.

1. `{Name}Output.php` — Result data container

### Step 4: Generate Tests

Mirror the production-code path under `tests/Unit/`.

---

## File Placement

| Component | Path |
|-----------|------|
| Use Case | `src/{architecture-path}/UseCase/{Name}UseCase.php` |
| Input DTO | `src/{architecture-path}/DTO/{Name}Input.php` |
| Output DTO | `src/{architecture-path}/DTO/{Name}Output.php` |
| Unit Tests | `tests/Unit/{architecture-path}/UseCase/` |

> `{architecture-path}` represents your project's architecture-specific folders. Use Cases typically live wherever your project coordinates application workflows (Application layer in Clean/Layered, the hexagon in Hexagonal, the feature folder in Package-by-Feature, the controllers in MVC). Adjust to your project's layout.

---

## Naming Conventions

| Pattern | Example |
|---------|---------|
| Use Case | `{Verb}{Entity}UseCase` |
| Input DTO | `{Name}Input` |
| Output DTO | `{Name}Output` or `{Entity}{Result}Output` |

---

## Quick Template Reference

### Use Case

```php
final readonly class {Name}UseCase
{
    public function __construct(
        private {Repository}Interface $repository,
        private EventDispatcherInterface $events,
        private TransactionManagerInterface $transaction
    ) {}

    public function execute({Name}Input $input): {Name}Output
    {
        return $this->transaction->transactional(function () use ($input) {
            $aggregate = $this->repository->findById($input->id);
            $aggregate->doSomething($input->data);
            $this->repository->save($aggregate);

            foreach ($aggregate->releaseEvents() as $event) {
                $this->events->dispatch($event);
            }

            return new {Name}Output(...);
        });
    }
}
```

### Input DTO

```php
final readonly class {Name}Input
{
    public function __construct(
        public {ValueObject} $id,
        {additionalProperties}
    ) {}
}
```

### Output DTO

```php
final readonly class {Name}Output
{
    public function __construct(
        public string $id,
        {resultProperties}
    ) {}

    public function toArray(): array
    {
        return ['id' => $this->id, ...];
    }
}
```

---

## Anti-patterns to Avoid

| Anti-pattern | Problem | Solution |
|--------------|---------|----------|
| Business Logic | Decisions in use case | Delegate to domain |
| Multiple Aggregates | Transaction spans aggregates | One aggregate per transaction |
| Direct Repo Calls | Bypassing use case | Always use use case |
| Missing Transaction | No atomicity | Wrap in transaction |
| External in Transaction | Long-running transactions | External calls outside |

---

## References

For complete PHP templates and examples, see:
- `references/templates.md` — UseCase, Input, Output, Test templates with design principles
- `references/examples.md` — CreateOrder, ConfirmOrder, ProcessPayment examples and tests
