# Factory Pattern Templates

## Static Factory (Simple)

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext}\Factory;

use Domain\{BoundedContext}\Entity\{Entity};
use Domain\{BoundedContext}\ValueObject\{ValueObjects};
use Domain\{BoundedContext}\Exception\{ValidationExceptions};

final class {Name}Factory
{
    /**
     * @throws {ValidationException}
     */
    public static function create({parameters}): {Entity}
    {
        self::validate({parameters});

        return new {Entity}(
            {constructorArguments}
        );
    }

    public static function createFrom{Source}({SourceType} $source): {Entity}
    {
        return new {Entity}(
            {mappedArguments}
        );
    }

    /**
     * Reconstitute from persistence (no validation, assumes valid data)
     */
    public static function reconstitute(
        {allFields}
    ): {Entity} {
        return new {Entity}(
            {allArguments}
        );
    }

    private static function validate({parameters}): void
    {
        {validationLogic}
    }
}
```

---

## Instance Factory (With Dependencies)

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext}\Factory;

use Domain\{BoundedContext}\Entity\{Entity};
use Domain\{BoundedContext}\Repository\{RepositoryInterface};
use Domain\{BoundedContext}\Service\{DomainService};

final readonly class {Name}Factory
{
    public function __construct(
        private {RepositoryInterface} $repository,
        private {DomainService} $service
    ) {}

    public function create({parameters}): {Entity}
    {
        {creationLogicWithDependencies}
    }
}
```

---

## Test Template

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\{BoundedContext}\Factory;

use Domain\{BoundedContext}\Factory\{Name}Factory;
use Domain\{BoundedContext}\Entity\{Entity};
use Domain\{BoundedContext}\ValueObject\{ValueObjects};
use Domain\{BoundedContext}\Exception\{Exceptions};
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass({Name}Factory::class)]
final class {Name}FactoryTest extends TestCase
{
    public function testCreatesValidEntity(): void
    {
        $entity = {Name}Factory::create(
            {validParameters}
        );

        self::assertInstanceOf({Entity}::class, $entity);
        {additionalAssertions}
    }

    public function testCreateFrom{Source}MapsCorrectly(): void
    {
        $source = {createSource};

        $entity = {Name}Factory::createFrom{Source}($source);

        {assertMapping}
    }

    public function testThrowsOnInvalidData(): void
    {
        $this->expectException({ValidationException}::class);

        {Name}Factory::create({invalidParameters});
    }

    public function testReconstituteCreatesWithExactData(): void
    {
        $entity = {Name}Factory::reconstitute(
            {allFieldValues}
        );

        {assertAllFields}
    }
}
```
