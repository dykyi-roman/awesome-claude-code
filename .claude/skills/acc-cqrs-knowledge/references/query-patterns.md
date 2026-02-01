# Query Patterns

Detailed patterns for CQRS Query implementation in PHP.

## Query Definition

### What is a Query?

A Query is an immutable object representing a request to read data without side effects.

### Characteristics

- **Interrogative naming**: Get/Find/List + noun (GetOrderDetails, FindUserByEmail)
- **Immutable**: readonly class, no setters
- **No side effects**: never modifies state
- **Returns DTOs**: never domain entities
- **Can use optimized read models**: bypass domain model for performance

## PHP 8.5 Implementation

### Basic Query

```php
<?php

declare(strict_types=1);

namespace Application\Order\Query;

use Domain\Order\ValueObject\OrderId;

final readonly class GetOrderDetailsQuery
{
    public function __construct(
        public OrderId $orderId
    ) {}
}
```

### Query with Filtering

```php
<?php

declare(strict_types=1);

namespace Application\Order\Query;

use Domain\Order\ValueObject\CustomerId;
use Domain\Order\Enum\OrderStatus;

final readonly class ListOrdersQuery
{
    public function __construct(
        public ?CustomerId $customerId = null,
        public ?OrderStatus $status = null,
        public ?\DateTimeImmutable $fromDate = null,
        public ?\DateTimeImmutable $toDate = null,
        public int $limit = 50,
        public int $offset = 0
    ) {
        if ($limit < 1 || $limit > 100) {
            throw new InvalidArgumentException('Limit must be between 1 and 100');
        }
        if ($offset < 0) {
            throw new InvalidArgumentException('Offset must be non-negative');
        }
    }
}
```

### Query with Sorting

```php
<?php

declare(strict_types=1);

namespace Application\Product\Query;

final readonly class SearchProductsQuery
{
    public function __construct(
        public ?string $searchTerm = null,
        public ?CategoryId $categoryId = null,
        public SortField $sortBy = SortField::CreatedAt,
        public SortDirection $direction = SortDirection::Desc,
        public int $limit = 20,
        public int $offset = 0
    ) {}
}

enum SortField: string
{
    case Name = 'name';
    case Price = 'price';
    case CreatedAt = 'created_at';
    case Popularity = 'popularity';
}

enum SortDirection: string
{
    case Asc = 'asc';
    case Desc = 'desc';
}
```

## Query Naming Conventions

### Good Names

| Pattern | Use Case | Example |
|---------|----------|---------|
| `Get{Entity}` | Single item by ID | `GetOrderDetails`, `GetUserProfile` |
| `Find{Entity}By{Field}` | Single item by field | `FindUserByEmail`, `FindOrderByNumber` |
| `List{Entities}` | Collection with filters | `ListOrders`, `ListProducts` |
| `Search{Entities}` | Full-text search | `SearchProducts`, `SearchCustomers` |
| `Count{Entities}` | Counting | `CountPendingOrders` |
| `Check{Condition}` | Boolean check | `CheckEmailExists` |

### Bad Names (Avoid)

| Bad Name | Why | Better Name |
|----------|-----|-------------|
| `OrderQuery` | Vague | `GetOrderDetailsQuery` |
| `FetchOrders` | Inconsistent verb | `ListOrdersQuery` |
| `RetrieveUser` | Inconsistent verb | `GetUserQuery` |
| `GetAndUpdateOrder` | Has side effect | Split into Query + Command |

## Read Models

### What is a Read Model?

Optimized data structure for queries, separate from write model.

### PHP 8.5 Read Model Interface

```php
<?php

declare(strict_types=1);

namespace Application\Order\ReadModel;

use Domain\Order\ValueObject\OrderId;
use Domain\Order\ValueObject\CustomerId;
use Domain\Order\Enum\OrderStatus;

interface OrderReadModelInterface
{
    public function findById(OrderId $id): ?OrderDetailsDTO;

    /**
     * @return array<OrderListItemDTO>
     */
    public function findByCustomer(
        CustomerId $customerId,
        ?OrderStatus $status = null,
        int $limit = 50,
        int $offset = 0
    ): array;

    public function countByStatus(OrderStatus $status): int;
}
```

### Read Model DTO

```php
<?php

declare(strict_types=1);

namespace Application\Order\DTO;

final readonly class OrderDetailsDTO
{
    public function __construct(
        public string $orderId,
        public string $customerName,
        public string $customerEmail,
        public string $status,
        public int $totalAmount,
        public string $currency,
        /** @var array<OrderLineDTO> */
        public array $lines,
        public \DateTimeImmutable $createdAt,
        public ?\DateTimeImmutable $confirmedAt
    ) {}
}

final readonly class OrderLineDTO
{
    public function __construct(
        public string $productId,
        public string $productName,
        public int $quantity,
        public int $unitPrice,
        public int $lineTotal
    ) {}
}
```

### Read Model Implementation (Infrastructure)

```php
<?php

declare(strict_types=1);

namespace Infrastructure\ReadModel;

use Application\Order\ReadModel\OrderReadModelInterface;

final readonly class DbalOrderReadModel implements OrderReadModelInterface
{
    public function __construct(
        private Connection $connection
    ) {}

    public function findById(OrderId $id): ?OrderDetailsDTO
    {
        $sql = <<<SQL
            SELECT
                o.id as order_id,
                c.name as customer_name,
                c.email as customer_email,
                o.status,
                o.total_amount,
                o.currency,
                o.created_at,
                o.confirmed_at
            FROM orders o
            JOIN customers c ON c.id = o.customer_id
            WHERE o.id = :id
        SQL;

        $row = $this->connection->fetchAssociative($sql, ['id' => $id->value]);

        if ($row === false) {
            return null;
        }

        $lines = $this->fetchOrderLines($id);

        return new OrderDetailsDTO(
            orderId: $row['order_id'],
            customerName: $row['customer_name'],
            customerEmail: $row['customer_email'],
            status: $row['status'],
            totalAmount: (int) $row['total_amount'],
            currency: $row['currency'],
            lines: $lines,
            createdAt: new \DateTimeImmutable($row['created_at']),
            confirmedAt: $row['confirmed_at']
                ? new \DateTimeImmutable($row['confirmed_at'])
                : null
        );
    }
}
```

## Query Handler Patterns

### Basic Query Handler

```php
<?php

declare(strict_types=1);

namespace Application\Order\Query;

final readonly class GetOrderDetailsHandler
{
    public function __construct(
        private OrderReadModelInterface $readModel
    ) {}

    public function __invoke(GetOrderDetailsQuery $query): ?OrderDetailsDTO
    {
        return $this->readModel->findById($query->orderId);
    }
}
```

### Query Handler with Exception

```php
<?php

declare(strict_types=1);

namespace Application\Order\Query;

final readonly class GetOrderDetailsHandler
{
    public function __construct(
        private OrderReadModelInterface $readModel
    ) {}

    public function __invoke(GetOrderDetailsQuery $query): OrderDetailsDTO
    {
        $order = $this->readModel->findById($query->orderId);

        if ($order === null) {
            throw new OrderNotFoundException($query->orderId);
        }

        return $order;
    }
}
```

### Paginated Query Handler

```php
<?php

declare(strict_types=1);

namespace Application\Order\Query;

final readonly class ListOrdersHandler
{
    public function __construct(
        private OrderReadModelInterface $readModel
    ) {}

    public function __invoke(ListOrdersQuery $query): PaginatedResult
    {
        $items = $this->readModel->findByCustomer(
            customerId: $query->customerId,
            status: $query->status,
            limit: $query->limit,
            offset: $query->offset
        );

        $total = $this->readModel->countByCustomer(
            customerId: $query->customerId,
            status: $query->status
        );

        return new PaginatedResult(
            items: $items,
            total: $total,
            limit: $query->limit,
            offset: $query->offset
        );
    }
}
```

## Anti-Patterns

### Query with Side Effects

```php
// BAD - Query modifies state
final readonly class GetOrderDetailsHandler
{
    public function __invoke(GetOrderDetailsQuery $query): OrderDetailsDTO
    {
        $order = $this->readModel->findById($query->orderId);

        // BAD: Side effect in query
        $this->logger->info('Order viewed', ['id' => $query->orderId]);

        // BAD: Updating state
        $this->repository->incrementViewCount($query->orderId);

        return $order;
    }
}

// GOOD - Pure query, side effects via events
final readonly class GetOrderDetailsHandler
{
    public function __invoke(GetOrderDetailsQuery $query): OrderDetailsDTO
    {
        return $this->readModel->findById($query->orderId);
        // Analytics handled by separate event subscriber
    }
}
```

### Returning Domain Entities

```php
// BAD - Returns domain entity
final readonly class GetOrderHandler
{
    public function __invoke(GetOrderQuery $query): Order  // BAD!
    {
        return $this->repository->findById($query->orderId);
    }
}

// GOOD - Returns DTO
final readonly class GetOrderDetailsHandler
{
    public function __invoke(GetOrderDetailsQuery $query): OrderDetailsDTO
    {
        return $this->readModel->findById($query->orderId);
    }
}
```

## Detection Patterns

```bash
# Good - Query classes exist
Glob: **/Query/**/*Query.php
Grep: "final readonly class.*Query" --glob "**/*.php"

# Good - Proper naming
Grep: "class (Get|Find|List|Search|Count|Check).*Query" --glob "**/*.php"

# Good - Returns DTO
Grep: "function __invoke.*Query.*\): .*DTO" --glob "**/*Handler.php"

# Bad - Query with side effects
Grep: "->save\(|->persist\(|->dispatch\(" --glob "**/Query/**/*Handler.php"

# Bad - Returns entity
Grep: "function __invoke.*Query.*\): (Order|User|Product|Customer)[^D]" --glob "**/*Handler.php"

# Bad - Command-like query names
Grep: "class (Create|Update|Delete|Process).*Query" --glob "**/*.php"
```

## Read Model vs Repository

| Aspect | Read Model | Repository |
|--------|------------|------------|
| Purpose | Query optimization | Domain persistence |
| Returns | DTOs | Domain entities |
| Used by | Query handlers | Command handlers |
| Can join | Multiple tables/aggregates | Single aggregate |
| Consistency | Eventually consistent OK | Strong consistency |
| Location | Application/Infrastructure | Domain (interface) |
