# Command Pattern Templates

## Command Template

```php
<?php

declare(strict_types=1);

namespace Application\{BoundedContext}\Command;

use Domain\{BoundedContext}\ValueObject\{ValueObjects};

final readonly class {Name}Command
{
    public function __construct(
        {properties}
    ) {
        {validation}
    }

    public static function fromArray(array $data): self
    {
        return new self(
            {fromArrayMapping}
        );
    }
}
```

---

## Handler Template

```php
<?php

declare(strict_types=1);

namespace Application\{BoundedContext}\Handler;

use Application\{BoundedContext}\Command\{Name}Command;
use Domain\{BoundedContext}\Repository\{AggregateRoot}RepositoryInterface;
use Domain\Shared\EventDispatcherInterface;

final readonly class {Name}Handler
{
    public function __construct(
        private {AggregateRoot}RepositoryInterface ${aggregateRoot}s,
        private EventDispatcherInterface $events
    ) {}

    public function __invoke({Name}Command $command): {ReturnType}
    {
        {handlerLogic}
    }
}
```

---

## Handler Patterns

### Standard Handler Flow (Update)

```php
public function __invoke(SomeCommand $command): void
{
    // 1. Load aggregate
    $aggregate = $this->repository->findById($command->aggregateId);

    if ($aggregate === null) {
        throw new NotFoundException($command->aggregateId);
    }

    // 2. Execute domain behavior
    $aggregate->doSomething($command->data);

    // 3. Persist
    $this->repository->save($aggregate);

    // 4. Dispatch events
    foreach ($aggregate->releaseEvents() as $event) {
        $this->events->dispatch($event);
    }
}
```

### Create Handler Flow

```php
public function __invoke(CreateCommand $command): AggregateId
{
    // 1. Create aggregate
    $aggregate = Aggregate::create(
        id: $this->repository->nextIdentity(),
        ...
    );

    // 2. Persist
    $this->repository->save($aggregate);

    // 3. Dispatch events
    foreach ($aggregate->releaseEvents() as $event) {
        $this->events->dispatch($event);
    }

    // 4. Return ID
    return $aggregate->id();
}
```

---

## Test Templates

### Command Test

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Application\{BoundedContext}\Command;

use Application\{BoundedContext}\Command\{Name}Command;
use Domain\{BoundedContext}\ValueObject\{ValueObject};
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass({Name}Command::class)]
final class {Name}CommandTest extends TestCase
{
    public function testCreatesWithValidData(): void
    {
        $command = new {Name}Command(
            {validParameters}
        );

        {assertions}
    }

    public function testRejectsInvalidData(): void
    {
        $this->expectException(\InvalidArgumentException::class);

        new {Name}Command({invalidParameters});
    }

    public function testCreatesFromArray(): void
    {
        $command = {Name}Command::fromArray([
            {arrayData}
        ]);

        {assertions}
    }
}
```

### Handler Test

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Application\{BoundedContext}\Handler;

use Application\{BoundedContext}\Command\{Name}Command;
use Application\{BoundedContext}\Handler\{Name}Handler;
use Domain\{BoundedContext}\Entity\{Entity};
use Domain\{BoundedContext}\Repository\{Entity}RepositoryInterface;
use Domain\Shared\EventDispatcherInterface;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass({Name}Handler::class)]
final class {Name}HandlerTest extends TestCase
{
    private {Entity}RepositoryInterface $repository;
    private EventDispatcherInterface $events;
    private {Name}Handler $handler;

    protected function setUp(): void
    {
        $this->repository = $this->createMock({Entity}RepositoryInterface::class);
        $this->events = $this->createMock(EventDispatcherInterface::class);
        $this->handler = new {Name}Handler($this->repository, $this->events);
    }

    public function testHandlesCommandSuccessfully(): void
    {
        {testSetup}

        $command = new {Name}Command({commandData});

        $result = ($this->handler)($command);

        {assertions}
    }
}
```
