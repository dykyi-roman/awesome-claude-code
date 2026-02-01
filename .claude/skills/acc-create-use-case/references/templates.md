# Use Case Pattern Templates

## Use Case Template

```php
<?php

declare(strict_types=1);

namespace Application\{BoundedContext}\UseCase;

use Application\{BoundedContext}\DTO\{InputDTO};
use Application\{BoundedContext}\DTO\{OutputDTO};
use Domain\{BoundedContext}\Repository\{Repository}Interface;
use Domain\Shared\EventDispatcherInterface;
use Domain\Shared\TransactionManagerInterface;

final readonly class {Name}UseCase
{
    public function __construct(
        private {Repository}Interface ${repository},
        private EventDispatcherInterface $events,
        private TransactionManagerInterface $transaction
    ) {}

    public function execute({InputDTO} $input): {OutputDTO}
    {
        return $this->transaction->transactional(function () use ($input) {
            {useCaseLogic}

            foreach ($aggregate->releaseEvents() as $event) {
                $this->events->dispatch($event);
            }

            return {result};
        });
    }
}
```

---

## Input DTO Template

```php
<?php

declare(strict_types=1);

namespace Application\{BoundedContext}\DTO;

use Domain\{BoundedContext}\ValueObject\{ValueObject};

final readonly class {Name}Input
{
    public function __construct(
        public {ValueObject} $id,
        {additionalProperties}
    ) {}
}
```

---

## Output DTO Template

```php
<?php

declare(strict_types=1);

namespace Application\{BoundedContext}\DTO;

final readonly class {Name}Output
{
    public function __construct(
        public string $id,
        {resultProperties}
    ) {}

    public function toArray(): array
    {
        return [
            'id' => $this->id,
            {arrayMapping}
        ];
    }
}
```

---

## Test Template

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Application\{BoundedContext}\UseCase;

use Application\{BoundedContext}\UseCase\{Name}UseCase;
use Application\{BoundedContext}\DTO\{Name}Input;
use Application\{BoundedContext}\DTO\{Name}Output;
use Domain\{BoundedContext}\Repository\{Repository}Interface;
use Domain\Shared\EventDispatcherInterface;
use Domain\Shared\TransactionManagerInterface;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass({Name}UseCase::class)]
final class {Name}UseCaseTest extends TestCase
{
    private {Repository}Interface $repository;
    private EventDispatcherInterface $events;
    private TransactionManagerInterface $transaction;
    private {Name}UseCase $useCase;

    protected function setUp(): void
    {
        $this->repository = $this->createMock({Repository}Interface::class);
        $this->events = $this->createMock(EventDispatcherInterface::class);
        $this->transaction = $this->createMock(TransactionManagerInterface::class);

        $this->transaction->method('transactional')
            ->willReturnCallback(fn (callable $callback) => $callback());

        $this->useCase = new {Name}UseCase(
            $this->repository,
            $this->events,
            $this->transaction
        );
    }

    public function testExecutesSuccessfully(): void
    {
        {testSetup}

        $input = new {Name}Input({inputData});

        $result = $this->useCase->execute($input);

        self::assertInstanceOf({Name}Output::class, $result);
        {assertions}
    }
}
```

---

## Design Principles

### Orchestration, Not Decision

```php
// GOOD: Orchestration - delegates decisions to domain
public function execute(ConfirmOrderInput $input): OrderConfirmedOutput
{
    $order = $this->orders->findById($input->orderId);
    $order->confirm();  // Domain decides if confirmation is valid
    $this->orders->save($order);
    // ...
}

// BAD: Business logic in use case
public function execute(ConfirmOrderInput $input): OrderConfirmedOutput
{
    $order = $this->orders->findById($input->orderId);

    // BAD: Business logic belongs in domain
    if ($order->getStatus() === 'draft' && count($order->getLines()) > 0) {
        $order->setStatus('confirmed');
    }
}
```

### Transaction Management

```php
// GOOD: Clear transaction boundary
public function execute(Input $input): Output
{
    return $this->transaction->transactional(function () use ($input) {
        // All operations here are atomic
        $order = $this->orders->findById($input->orderId);
        $order->confirm();
        $this->orders->save($order);
        return new Output(...);
    });
}
```

### External Services Outside Transaction

```php
// GOOD: External call outside transaction
public function execute(Input $input): Output
{
    // External service call - can fail, can be retried
    $result = $this->externalService->call($input->data);

    // Only then start transaction
    return $this->transaction->transactional(function () use ($result) {
        // Update local state based on external result
    });
}
```
