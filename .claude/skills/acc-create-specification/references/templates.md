# Specification Pattern Templates

## Base Specification Interface

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\Specification;

/**
 * @template T
 */
interface SpecificationInterface
{
    /**
     * @param T $candidate
     */
    public function isSatisfiedBy(mixed $candidate): bool;

    /**
     * @return self<T>
     */
    public function and(self $other): self;

    /**
     * @return self<T>
     */
    public function or(self $other): self;

    /**
     * @return self<T>
     */
    public function not(): self;
}
```

---

## Abstract Specification

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\Specification;

/**
 * @template T
 * @implements SpecificationInterface<T>
 */
abstract class AbstractSpecification implements SpecificationInterface
{
    abstract public function isSatisfiedBy(mixed $candidate): bool;

    public function and(SpecificationInterface $other): SpecificationInterface
    {
        return new AndSpecification($this, $other);
    }

    public function or(SpecificationInterface $other): SpecificationInterface
    {
        return new OrSpecification($this, $other);
    }

    public function not(): SpecificationInterface
    {
        return new NotSpecification($this);
    }
}
```

---

## Composite Specifications

### AndSpecification

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\Specification;

/**
 * @template T
 * @extends AbstractSpecification<T>
 */
final readonly class AndSpecification extends AbstractSpecification
{
    public function __construct(
        private SpecificationInterface $left,
        private SpecificationInterface $right
    ) {}

    public function isSatisfiedBy(mixed $candidate): bool
    {
        return $this->left->isSatisfiedBy($candidate)
            && $this->right->isSatisfiedBy($candidate);
    }
}
```

### OrSpecification

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\Specification;

/**
 * @template T
 * @extends AbstractSpecification<T>
 */
final readonly class OrSpecification extends AbstractSpecification
{
    public function __construct(
        private SpecificationInterface $left,
        private SpecificationInterface $right
    ) {}

    public function isSatisfiedBy(mixed $candidate): bool
    {
        return $this->left->isSatisfiedBy($candidate)
            || $this->right->isSatisfiedBy($candidate);
    }
}
```

### NotSpecification

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\Specification;

/**
 * @template T
 * @extends AbstractSpecification<T>
 */
final readonly class NotSpecification extends AbstractSpecification
{
    public function __construct(
        private SpecificationInterface $wrapped
    ) {}

    public function isSatisfiedBy(mixed $candidate): bool
    {
        return !$this->wrapped->isSatisfiedBy($candidate);
    }
}
```

---

## Concrete Specification Template

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext}\Specification;

use Domain\{BoundedContext}\Entity\{Entity};
use Domain\Shared\Specification\AbstractSpecification;

/**
 * @extends AbstractSpecification<{Entity}>
 */
final readonly class {Name}Specification extends AbstractSpecification
{
    public function __construct(
        {constructorParameters}
    ) {}

    public function isSatisfiedBy(mixed $candidate): bool
    {
        if (!$candidate instanceof {Entity}) {
            return false;
        }

        return {businessRule};
    }
}
```

---

## Repository Integration

### Repository Interface with Specification

```php
<?php

declare(strict_types=1);

namespace Domain\Order\Repository;

use Domain\Order\Entity\Order;
use Domain\Shared\Specification\SpecificationInterface;

interface OrderRepositoryInterface
{
    /** @return array<Order> */
    public function findBySpecification(SpecificationInterface $specification): array;

    public function countBySpecification(SpecificationInterface $specification): int;
}
```

### Doctrine Repository Implementation

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Persistence\Doctrine\Repository;

use Domain\Order\Repository\OrderRepositoryInterface;
use Domain\Shared\Specification\SpecificationInterface;

final readonly class DoctrineOrderRepository implements OrderRepositoryInterface
{
    public function findBySpecification(SpecificationInterface $specification): array
    {
        $all = $this->findAll();
        return array_filter($all, fn($order) => $specification->isSatisfiedBy($order));
    }

    public function findBySpecificationOptimized(SpecificationInterface $specification): array
    {
        if ($specification instanceof QueryableSpecification) {
            return $this->findByQueryBuilder($specification->toQueryBuilder($this->qb));
        }

        return $this->findBySpecification($specification);
    }
}
```

---

## Test Template

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\{BoundedContext}\Specification;

use Domain\{BoundedContext}\Specification\{Name}Specification;
use Domain\{BoundedContext}\Entity\{Entity};
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\Attributes\DataProvider;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass({Name}Specification::class)]
final class {Name}SpecificationTest extends TestCase
{
    public function testIsSatisfiedByMatchingEntity(): void
    {
        $specification = new {Name}Specification({parameters});
        $entity = $this->createMatchingEntity();

        self::assertTrue($specification->isSatisfiedBy($entity));
    }

    public function testIsNotSatisfiedByNonMatchingEntity(): void
    {
        $specification = new {Name}Specification({parameters});
        $entity = $this->createNonMatchingEntity();

        self::assertFalse($specification->isSatisfiedBy($entity));
    }

    public function testReturnsFalseForWrongType(): void
    {
        $specification = new {Name}Specification({parameters});

        self::assertFalse($specification->isSatisfiedBy(new \stdClass()));
    }

    public function testCanBeComposedWithAnd(): void
    {
        $spec1 = new {Name}Specification({params1});
        $spec2 = new {Other}Specification({params2});

        $combined = $spec1->and($spec2);

        self::assertTrue($combined->isSatisfiedBy($this->createMatchingBoth()));
        self::assertFalse($combined->isSatisfiedBy($this->createMatchingOnlyFirst()));
    }

    public function testCanBeNegated(): void
    {
        $specification = new {Name}Specification({parameters});
        $negated = $specification->not();

        self::assertFalse($negated->isSatisfiedBy($this->createMatchingEntity()));
        self::assertTrue($negated->isSatisfiedBy($this->createNonMatchingEntity()));
    }

    {additionalTests}
}
```
