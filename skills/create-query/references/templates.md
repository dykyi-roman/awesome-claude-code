# Query Pattern Templates

## Query Template

```php
<?php

declare(strict_types=1);

namespace Application\{BoundedContext}\Query;

final readonly class {Name}Query
{
    public function __construct(
        {properties}
    ) {
        {validation}
    }
}
```

---

## Handler Template

```php
<?php

declare(strict_types=1);

namespace Application\{BoundedContext}\Handler;

use Application\{BoundedContext}\Query\{Name}Query;
use Application\{BoundedContext}\DTO\{ResultDTO};
use Application\{BoundedContext}\ReadModel\{ReadModelInterface};

final readonly class {Name}Handler
{
    public function __construct(
        private {ReadModelInterface} $readModel
    ) {}

    public function __invoke({Name}Query $query): {ReturnType}
    {
        return $this->readModel->{readMethod}($query->{params});
    }
}
```

---

## DTO Template

```php
<?php

declare(strict_types=1);

namespace Application\{BoundedContext}\DTO;

final readonly class {Name}DTO
{
    public function __construct(
        {properties}
    ) {}

    public static function fromArray(array $data): self
    {
        return new self(
            {fromArrayMapping}
        );
    }

    public function toArray(): array
    {
        return [
            {toArrayMapping}
        ];
    }
}
```

---

## Paginated Result DTO

```php
<?php

declare(strict_types=1);

namespace Application\{BoundedContext}\DTO;

final readonly class PaginatedResultDTO
{
    /**
     * @param array<{ItemDTO}> $items
     */
    public function __construct(
        public array $items,
        public int $total,
        public int $limit,
        public int $offset
    ) {}

    public function hasMore(): bool
    {
        return ($this->offset + count($this->items)) < $this->total;
    }

    public function page(): int
    {
        return (int) floor($this->offset / $this->limit) + 1;
    }

    public function totalPages(): int
    {
        return (int) ceil($this->total / $this->limit);
    }

    public function toArray(): array
    {
        return [
            'items' => array_map(fn ($item) => $item->toArray(), $this->items),
            'pagination' => [
                'total' => $this->total,
                'limit' => $this->limit,
                'offset' => $this->offset,
                'page' => $this->page(),
                'total_pages' => $this->totalPages(),
                'has_more' => $this->hasMore(),
            ],
        ];
    }
}
```

---

## Read Model Interface

```php
<?php

declare(strict_types=1);

namespace Application\{BoundedContext}\ReadModel;

use Application\{BoundedContext}\DTO\{DetailsDTO};
use Application\{BoundedContext}\DTO\{ListItemDTO};

interface {Name}ReadModelInterface
{
    public function findById(string $id): ?{DetailsDTO};

    /**
     * @return array<{ListItemDTO}>
     */
    public function findAll(
        ?string $filterId = null,
        ?string $status = null,
        int $limit = 20,
        int $offset = 0,
        string $sortBy = 'created_at',
        string $sortDirection = 'desc'
    ): array;

    public function count(?string $filterId = null, ?string $status = null): int;
}
```

---

## Test Templates

### Query Test

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Application\{BoundedContext}\Query;

use Application\{BoundedContext}\Query\{Name}Query;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass({Name}Query::class)]
final class {Name}QueryTest extends TestCase
{
    public function testCreatesWithDefaults(): void
    {
        $query = new {Name}Query();

        self::assertNull($query->filterId);
        self::assertSame(20, $query->limit);
        self::assertSame(0, $query->offset);
    }

    public function testCreatesWithFilters(): void
    {
        $query = new {Name}Query(
            filterId: 'some-id',
            limit: 50,
            offset: 100
        );

        self::assertSame('some-id', $query->filterId);
        self::assertSame(50, $query->limit);
        self::assertSame(100, $query->offset);
    }

    public function testRejectsInvalidLimit(): void
    {
        $this->expectException(\InvalidArgumentException::class);

        new {Name}Query(limit: 0);
    }

    public function testRejectsNegativeOffset(): void
    {
        $this->expectException(\InvalidArgumentException::class);

        new {Name}Query(offset: -1);
    }
}
```

### Handler Test

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Application\{BoundedContext}\Handler;

use Application\{BoundedContext}\Handler\{Name}Handler;
use Application\{BoundedContext}\Query\{Name}Query;
use Application\{BoundedContext}\DTO\{ResultDTO};
use Application\{BoundedContext}\ReadModel\{ReadModelInterface};
use Domain\{BoundedContext}\Exception\{NotFoundException};
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass({Name}Handler::class)]
final class {Name}HandlerTest extends TestCase
{
    private {ReadModelInterface} $readModel;
    private {Name}Handler $handler;

    protected function setUp(): void
    {
        $this->readModel = $this->createMock({ReadModelInterface}::class);
        $this->handler = new {Name}Handler($this->readModel);
    }

    public function testReturnsResult(): void
    {
        $id = 'entity-123';
        $expectedDTO = $this->createDTO($id);

        $this->readModel->expects(self::once())
            ->method('findById')
            ->with($id)
            ->willReturn($expectedDTO);

        $query = new {Name}Query(new {Id}($id));

        $result = ($this->handler)($query);

        self::assertSame($expectedDTO, $result);
    }

    public function testThrowsWhenNotFound(): void
    {
        $this->readModel->expects(self::once())
            ->method('findById')
            ->willReturn(null);

        $query = new {Name}Query(new {Id}('non-existent'));

        $this->expectException({NotFoundException}::class);

        ($this->handler)($query);
    }

    private function createDTO(string $id): {ResultDTO}
    {
        return new {ResultDTO}(
            id: $id,
            {dtoProperties}
        );
    }
}
```
