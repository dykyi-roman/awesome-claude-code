# Builder Pattern Templates

## Builder Interface

**File:** `src/Domain/{BoundedContext}/Builder/{Name}BuilderInterface.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext}\Builder;

interface {Name}BuilderInterface
{
    public function with{Property1}({Type1} $value): self;

    public function with{Property2}({Type2} $value): self;

    public function build(): {Product};

    public function reset(): self;
}
```

---

## Concrete Builder

**File:** `src/Domain/{BoundedContext}/Builder/{Name}Builder.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext}\Builder;

final class {Name}Builder implements {Name}BuilderInterface
{
    private ?{Type1} ${property1} = null;
    private ?{Type2} ${property2} = null;
    private array $errors = [];

    public function with{Property1}({Type1} $value): self
    {
        $this->{property1} = $value;
        return $this;
    }

    public function with{Property2}({Type2} $value): self
    {
        $this->{property2} = $value;
        return $this;
    }

    public function build(): {Product}
    {
        $this->validate();

        if ($this->errors !== []) {
            throw new BuilderValidationException($this->errors);
        }

        return new {Product}(
            {property1}: $this->{property1},
            {property2}: $this->{property2}
        );
    }

    public function reset(): self
    {
        $this->{property1} = null;
        $this->{property2} = null;
        $this->errors = [];
        return $this;
    }

    private function validate(): void
    {
        if ($this->{property1} === null) {
            $this->errors[] = '{Property1} is required';
        }
        {additionalValidation}
    }
}
```

---

## BuilderValidationException

**File:** `src/Domain/{BoundedContext}/Builder/BuilderValidationException.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext}\Builder;

final class BuilderValidationException extends \InvalidArgumentException
{
    /**
     * @param array<string> $errors
     */
    public function __construct(
        public readonly array $errors
    ) {
        parent::__construct(sprintf('Builder validation failed: %s', implode(', ', $errors)));
    }
}
```

---

## Query Builder

**File:** `src/Infrastructure/Query/QueryBuilderInterface.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Query;

interface QueryBuilderInterface
{
    public function select(string ...$columns): self;

    public function from(string $table): self;

    public function where(string $column, string $operator, mixed $value): self;

    public function andWhere(string $column, string $operator, mixed $value): self;

    public function orWhere(string $column, string $operator, mixed $value): self;

    public function orderBy(string $column, string $direction = 'ASC'): self;

    public function limit(int $limit): self;

    public function offset(int $offset): self;

    public function build(): Query;
}
```

**File:** `src/Infrastructure/Query/QueryBuilder.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Query;

final class QueryBuilder implements QueryBuilderInterface
{
    private array $select = ['*'];
    private ?string $from = null;
    private array $where = [];
    private array $orderBy = [];
    private ?int $limit = null;
    private ?int $offset = null;
    private array $parameters = [];

    public function select(string ...$columns): self
    {
        $this->select = $columns ?: ['*'];
        return $this;
    }

    public function from(string $table): self
    {
        $this->from = $table;
        return $this;
    }

    public function where(string $column, string $operator, mixed $value): self
    {
        $this->where[] = ['type' => 'AND', 'column' => $column, 'operator' => $operator, 'value' => $value];
        return $this;
    }

    public function andWhere(string $column, string $operator, mixed $value): self
    {
        return $this->where($column, $operator, $value);
    }

    public function orWhere(string $column, string $operator, mixed $value): self
    {
        $this->where[] = ['type' => 'OR', 'column' => $column, 'operator' => $operator, 'value' => $value];
        return $this;
    }

    public function orderBy(string $column, string $direction = 'ASC'): self
    {
        $this->orderBy[] = ['column' => $column, 'direction' => strtoupper($direction)];
        return $this;
    }

    public function limit(int $limit): self
    {
        $this->limit = $limit;
        return $this;
    }

    public function offset(int $offset): self
    {
        $this->offset = $offset;
        return $this;
    }

    public function build(): Query
    {
        if ($this->from === null) {
            throw new \LogicException('Table name is required');
        }

        $sql = sprintf('SELECT %s FROM %s', implode(', ', $this->select), $this->from);

        if ($this->where !== []) {
            $sql .= ' WHERE ' . $this->buildWhereClause();
        }

        if ($this->orderBy !== []) {
            $sql .= ' ORDER BY ' . $this->buildOrderByClause();
        }

        if ($this->limit !== null) {
            $sql .= sprintf(' LIMIT %d', $this->limit);
        }

        if ($this->offset !== null) {
            $sql .= sprintf(' OFFSET %d', $this->offset);
        }

        return new Query($sql, $this->parameters);
    }

    private function buildWhereClause(): string
    {
        $parts = [];
        foreach ($this->where as $i => $condition) {
            $paramName = ':p' . $i;
            $clause = sprintf('%s %s %s', $condition['column'], $condition['operator'], $paramName);

            if ($i > 0) {
                $clause = $condition['type'] . ' ' . $clause;
            }

            $parts[] = $clause;
            $this->parameters[$paramName] = $condition['value'];
        }

        return implode(' ', $parts);
    }

    private function buildOrderByClause(): string
    {
        return implode(', ', array_map(
            fn($o) => sprintf('%s %s', $o['column'], $o['direction']),
            $this->orderBy
        ));
    }
}
```

---

## Director Template

**File:** `src/Domain/{BoundedContext}/Builder/{Name}Director.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext}\Builder;

final readonly class {Name}Director
{
    public function __construct(
        private {Name}BuilderInterface $builder
    ) {}

    public function buildMinimal{Name}(/* params */): {Product}
    {
        return $this->builder
            ->reset()
            ->with{RequiredProperty1}($value1)
            ->with{RequiredProperty2}($value2)
            ->build();
    }

    public function buildFull{Name}(/* all params */): {Product}
    {
        return $this->builder
            ->reset()
            ->with{Property1}($value1)
            ->with{Property2}($value2)
            // ... all properties
            ->build();
    }
}
```
