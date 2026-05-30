---
name: create-query
description: Generates CQRS Queries and Handlers for PHP 8.4. Creates read-only query DTOs with handlers that return data without side effects. Includes unit tests.
---

# Query Generator

Generate CQRS-compliant Queries and Query Handlers with tests.

## Query Characteristics

- **Immutable**: `final readonly class`
- **Interrogative naming**: Get/Find/List + noun
- **No side effects**: Handler never modifies state
- **Returns DTOs**: Never returns domain entities
- **Read-optimized**: Can use dedicated read models

---

## Generation Process

### Step 1: Generate Query

Place in your project's CQRS Query folder.

1. `{Name}Query.php` — Immutable query DTO with parameters

### Step 2: Generate Handler

Place in a sibling `Handler/` folder.

1. `{Name}Handler.php` — Read model consumer

### Step 3: Generate DTOs

Place in a sibling `DTO/` folder.

1. `{Name}DTO.php` — Result data structure
2. `PaginatedResultDTO.php` — For list queries (optional)

### Step 4: Generate Read Model Interface

Place in a sibling `ReadModel/` folder — the read-side abstraction is a distinct concept from the handler that consumes it.

1. `{Name}ReadModelInterface.php` — Query methods contract

### Step 5: Generate Tests

Mirror the production-code path under `tests/Unit/`.

---

## File Placement

| Component | Path |
|-----------|------|
| Query | `src/{architecture-path}/Query/{Name}Query.php` |
| Handler | `src/{architecture-path}/Handler/{Name}Handler.php` |
| DTO | `src/{architecture-path}/DTO/{Name}DTO.php` |
| Read Model Interface | `src/{architecture-path}/ReadModel/{Name}ReadModelInterface.php` |
| Unit Tests | `tests/Unit/{architecture-path}/` |

> `{architecture-path}` represents your project's architecture-specific folders. CQRS Queries and Handlers typically live wherever your project coordinates use cases. Adjust to your project's layout.

---

## Query Naming Conventions

| Purpose | Query Name | Returns |
|---------|------------|---------|
| Single by ID | `GetOrderDetailsQuery` | DTO or throws |
| Single by field | `FindUserByEmailQuery` | DTO or null |
| List/Collection | `ListOrdersQuery` | PaginatedResult |
| Search | `SearchProductsQuery` | array of DTOs |
| Count | `CountPendingOrdersQuery` | int |
| Check existence | `CheckEmailExistsQuery` | bool |

---

## Quick Template Reference

### Query

```php
final readonly class {Name}Query
{
    public function __construct(
        public {IdType} $id
    ) {}
}
```

### Query with Pagination

```php
final readonly class List{Name}Query
{
    public function __construct(
        public ?{FilterType} $filter = null,
        public int $limit = 20,
        public int $offset = 0,
        public string $sortBy = 'created_at',
        public string $sortDirection = 'desc'
    ) {
        if ($limit < 1 || $limit > 100) {
            throw new \InvalidArgumentException('Limit must be between 1 and 100');
        }
    }
}
```

### Handler

```php
final readonly class {Name}Handler
{
    public function __construct(
        private {ReadModelInterface} $readModel
    ) {}

    public function __invoke({Name}Query $query): {ResultDTO}
    {
        $result = $this->readModel->findById($query->id->value);

        if ($result === null) {
            throw new {NotFoundException}($query->id);
        }

        return $result;
    }
}
```

---

## Anti-patterns to Avoid

| Anti-pattern | Problem | Solution |
|--------------|---------|----------|
| Side Effects | Handler modifies state | Keep read-only |
| Returning Entities | Leaking domain | Return DTOs only |
| No Validation | Invalid parameters | Validate in constructor |
| Unbounded Lists | Performance issues | Always paginate |
| Missing Read Model | Querying write model | Use dedicated read model |

---

## References

For complete PHP templates and examples, see:
- `references/templates.md` — Query, Handler, DTO, PaginatedResult, ReadModel templates
- `references/examples.md` — GetOrderDetails, ListOrders, OrderDTO examples and tests
