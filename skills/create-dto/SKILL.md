---
name: create-dto
description: Generates DTO (Data Transfer Object) for PHP 8.4. Creates immutable objects for layer boundaries, API requests/responses, and data serialization. Includes unit tests.
---

# DTO Generator

Generate DTOs for transferring data between layers, API boundaries, and external systems.

## DTO Characteristics

- **Immutable**: Read-only after creation
- **No Behavior**: Pure data container, no business logic
- **Serializable**: JSON/array conversion support
- **Typed**: Strictly typed properties
- **Validated**: Input validation at creation (for requests)
- **Layer-Specific**: Different DTOs for different purposes

## DTO Types

| Type | Purpose | Typical placement |
|------|---------|-------------------|
| Request DTO | API input validation | Alongside HTTP entry-point code |
| Response DTO | API output formatting | Alongside HTTP entry-point code |
| Command DTO | Use case input | Alongside the use case / command bus |
| Query Result DTO | Read model output | Alongside the query handler / read model |
| Integration DTO | External API data | Alongside the external-system integration code |

---

## Generation Process

### Step 1: Identify DTO Type

Determine the purpose and layer for the DTO.

### Step 2: Generate DTO Class

Place based on type (see "DTO Types" table above for typical placement). In all cases, the DTO lives alongside the code that consumes/produces it.

### Step 3: Add Conversion Methods

1. `fromArray()` — Create from raw data
2. `fromEntity()` — Create from domain entity (Response DTOs)
3. `toArray()` / `jsonSerialize()` — Serialize for output

### Step 4: Generate Tests

Mirror the production-code path under `tests/Unit/`.

---

## File Placement

| Type | Path |
|------|------|
| Request DTO | `src/{architecture-path}/Request/` |
| Response DTO | `src/{architecture-path}/Response/` |
| Application DTO | `src/{architecture-path}/DTO/` |
| Integration DTO | `src/{architecture-path}/{Service}/DTO/` |
| Unit Tests | `tests/Unit/{architecture-path}/` |

> `{architecture-path}` represents your project's architecture-specific folders. Each DTO type lives alongside the code that consumes or produces it — see the "DTO Types" table above. Adjust to your project's layout.

---

## Naming Conventions

| Type | Pattern | Example |
|------|---------|---------|
| Request | `{Action}{Entity}Request` | `CreateOrderRequest`, `UpdateUserRequest` |
| Response | `{Entity}Response` | `OrderResponse`, `UserResponse` |
| Collection | `{Entity}CollectionResponse` | `OrderCollectionResponse` |
| Application | `{Entity}DTO` | `UserDTO`, `OrderDTO` |
| Integration | `{Service}{Action}Response` | `PaymentGatewayResponse` |

---

## Quick Template Reference

### Request DTO

```php
final readonly class {Name}Request
{
    public function __construct(
        #[Assert\NotBlank]
        public string $field,
        #[Assert\Valid]
        public ?NestedRequest $nested = null
    ) {}

    public static function fromArray(array $data): self;
}
```

### Response DTO

```php
final readonly class {Name}Response implements \JsonSerializable
{
    public function __construct(
        public string $id,
        public string $name,
        /** @var array<ItemResponse> */
        public array $items = []
    ) {}

    public static function fromEntity({Entity} $entity): self;
    public function jsonSerialize(): array;
}
```

### Application DTO

```php
final readonly class {Name}DTO
{
    public function __construct(
        public string $id,
        public string $field
    ) {}

    public static function fromRequest({Name}Request $request): self;
    public function toArray(): array;
}
```

---

## Anti-patterns to Avoid

| Anti-pattern | Problem | Solution |
|--------------|---------|----------|
| Business Logic | DTO with calculations | Keep DTOs data-only |
| Mutable DTO | setters, state changes | Use readonly, immutable |
| Domain Objects | Returning entities from API | Map to Response DTO |
| Anemic Validation | No input validation | Use Assert attributes |
| Deep Nesting | Complex nested DTOs | Flatten or split |
| Missing Serialization | No JSON support | Implement JsonSerializable |

---

## References

For complete PHP templates and examples, see:
- `references/templates.md` — Request, Response, Application, Collection, Integration DTO templates
- `references/examples.md` — Order, User, Payment examples and tests
