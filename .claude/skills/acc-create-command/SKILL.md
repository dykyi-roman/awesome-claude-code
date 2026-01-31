---
name: acc-create-command
description: Generates CQRS Commands and Handlers for PHP 8.4. Creates immutable command DTOs with handlers that modify state. Includes unit tests.
---

# Command Generator

Generate CQRS-compliant Commands and Command Handlers with tests.

## Command Characteristics

- **Immutable**: `final readonly class`
- **Imperative naming**: Verb + noun (CreateOrder, ConfirmPayment)
- **Self-validating**: Validates invariants in constructor
- **Intent-revealing**: Name describes what should happen
- **Returns void or ID**: Never returns data

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

## Complete Command Examples

### CreateOrder Command

```php
<?php

declare(strict_types=1);

namespace Application\Order\Command;

use Domain\Order\ValueObject\CustomerId;

final readonly class CreateOrderCommand
{
    /**
     * @param array<array{productId: string, productName: string, quantity: int, unitPriceCents: int, currency: string}> $lines
     */
    public function __construct(
        public CustomerId $customerId,
        public array $lines
    ) {
        if (empty($lines)) {
            throw new \InvalidArgumentException('Order must have at least one line');
        }
    }

    public static function fromArray(array $data): self
    {
        return new self(
            customerId: new CustomerId($data['customer_id']),
            lines: $data['lines']
        );
    }
}
```

### CreateOrder Handler

```php
<?php

declare(strict_types=1);

namespace Application\Order\Handler;

use Application\Order\Command\CreateOrderCommand;
use Domain\Order\Entity\Order;
use Domain\Order\Repository\OrderRepositoryInterface;
use Domain\Order\ValueObject\OrderId;
use Domain\Order\ValueObject\ProductId;
use Domain\Order\ValueObject\Money;
use Domain\Shared\EventDispatcherInterface;

final readonly class CreateOrderHandler
{
    public function __construct(
        private OrderRepositoryInterface $orders,
        private EventDispatcherInterface $events
    ) {}

    public function __invoke(CreateOrderCommand $command): OrderId
    {
        $order = Order::create(
            id: $this->orders->nextIdentity(),
            customerId: $command->customerId
        );

        foreach ($command->lines as $lineData) {
            $order->addLine(
                productId: new ProductId($lineData['productId']),
                productName: $lineData['productName'],
                quantity: $lineData['quantity'],
                unitPrice: new Money($lineData['unitPriceCents'], $lineData['currency'])
            );
        }

        $this->orders->save($order);

        foreach ($order->releaseEvents() as $event) {
            $this->events->dispatch($event);
        }

        return $order->id();
    }
}
```

### ConfirmOrder Command

```php
<?php

declare(strict_types=1);

namespace Application\Order\Command;

use Domain\Order\ValueObject\OrderId;

final readonly class ConfirmOrderCommand
{
    public function __construct(
        public OrderId $orderId
    ) {}

    public static function fromArray(array $data): self
    {
        return new self(
            orderId: new OrderId($data['order_id'])
        );
    }
}
```

### ConfirmOrder Handler

```php
<?php

declare(strict_types=1);

namespace Application\Order\Handler;

use Application\Order\Command\ConfirmOrderCommand;
use Domain\Order\Repository\OrderRepositoryInterface;
use Domain\Order\Exception\OrderNotFoundException;
use Domain\Shared\EventDispatcherInterface;

final readonly class ConfirmOrderHandler
{
    public function __construct(
        private OrderRepositoryInterface $orders,
        private EventDispatcherInterface $events
    ) {}

    public function __invoke(ConfirmOrderCommand $command): void
    {
        $order = $this->orders->findById($command->orderId);

        if ($order === null) {
            throw new OrderNotFoundException($command->orderId);
        }

        $order->confirm();

        $this->orders->save($order);

        foreach ($order->releaseEvents() as $event) {
            $this->events->dispatch($event);
        }
    }
}
```

### CancelOrder Command

```php
<?php

declare(strict_types=1);

namespace Application\Order\Command;

use Domain\Order\ValueObject\OrderId;

final readonly class CancelOrderCommand
{
    public function __construct(
        public OrderId $orderId,
        public string $reason
    ) {
        if (empty(trim($reason))) {
            throw new \InvalidArgumentException('Cancellation reason is required');
        }
    }

    public static function fromArray(array $data): self
    {
        return new self(
            orderId: new OrderId($data['order_id']),
            reason: $data['reason']
        );
    }
}
```

### CancelOrder Handler

```php
<?php

declare(strict_types=1);

namespace Application\Order\Handler;

use Application\Order\Command\CancelOrderCommand;
use Domain\Order\Repository\OrderRepositoryInterface;
use Domain\Order\Exception\OrderNotFoundException;
use Domain\Shared\EventDispatcherInterface;

final readonly class CancelOrderHandler
{
    public function __construct(
        private OrderRepositoryInterface $orders,
        private EventDispatcherInterface $events
    ) {}

    public function __invoke(CancelOrderCommand $command): void
    {
        $order = $this->orders->findById($command->orderId);

        if ($order === null) {
            throw new OrderNotFoundException($command->orderId);
        }

        $order->cancel($command->reason);

        $this->orders->save($order);

        foreach ($order->releaseEvents() as $event) {
            $this->events->dispatch($event);
        }
    }
}
```

## Test Templates

### Command Test

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Application\Order\Command;

use Application\Order\Command\CreateOrderCommand;
use Domain\Order\ValueObject\CustomerId;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(CreateOrderCommand::class)]
final class CreateOrderCommandTest extends TestCase
{
    public function testCreatesWithValidData(): void
    {
        $command = new CreateOrderCommand(
            customerId: new CustomerId('customer-123'),
            lines: [
                [
                    'productId' => 'product-1',
                    'productName' => 'Test Product',
                    'quantity' => 2,
                    'unitPriceCents' => 1000,
                    'currency' => 'USD',
                ],
            ]
        );

        self::assertSame('customer-123', $command->customerId->value);
        self::assertCount(1, $command->lines);
    }

    public function testRejectsEmptyLines(): void
    {
        $this->expectException(\InvalidArgumentException::class);
        $this->expectExceptionMessage('Order must have at least one line');

        new CreateOrderCommand(
            customerId: new CustomerId('customer-123'),
            lines: []
        );
    }

    public function testCreatesFromArray(): void
    {
        $command = CreateOrderCommand::fromArray([
            'customer_id' => 'customer-123',
            'lines' => [
                [
                    'productId' => 'product-1',
                    'productName' => 'Test',
                    'quantity' => 1,
                    'unitPriceCents' => 500,
                    'currency' => 'USD',
                ],
            ],
        ]);

        self::assertSame('customer-123', $command->customerId->value);
    }
}
```

### Handler Test

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Application\Order\Handler;

use Application\Order\Command\CreateOrderCommand;
use Application\Order\Handler\CreateOrderHandler;
use Domain\Order\Entity\Order;
use Domain\Order\Repository\OrderRepositoryInterface;
use Domain\Order\ValueObject\CustomerId;
use Domain\Order\ValueObject\OrderId;
use Domain\Shared\EventDispatcherInterface;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(CreateOrderHandler::class)]
final class CreateOrderHandlerTest extends TestCase
{
    private OrderRepositoryInterface $orders;
    private EventDispatcherInterface $events;
    private CreateOrderHandler $handler;

    protected function setUp(): void
    {
        $this->orders = $this->createMock(OrderRepositoryInterface::class);
        $this->events = $this->createMock(EventDispatcherInterface::class);
        $this->handler = new CreateOrderHandler($this->orders, $this->events);
    }

    public function testCreatesOrderAndReturnsId(): void
    {
        $expectedId = OrderId::generate();

        $this->orders->expects(self::once())
            ->method('nextIdentity')
            ->willReturn($expectedId);

        $this->orders->expects(self::once())
            ->method('save')
            ->with(self::isInstanceOf(Order::class));

        $this->events->expects(self::atLeastOnce())
            ->method('dispatch');

        $command = new CreateOrderCommand(
            customerId: new CustomerId('customer-123'),
            lines: [
                [
                    'productId' => 'product-1',
                    'productName' => 'Test Product',
                    'quantity' => 1,
                    'unitPriceCents' => 1000,
                    'currency' => 'USD',
                ],
            ]
        );

        $result = ($this->handler)($command);

        self::assertTrue($expectedId->equals($result));
    }
}
```

## Command Naming Conventions

| Action | Command Name | Returns |
|--------|--------------|---------|
| Create new | `CreateOrderCommand` | ID |
| Confirm/Approve | `ConfirmOrderCommand` | void |
| Cancel/Reject | `CancelOrderCommand` | void |
| Update property | `UpdateShippingAddressCommand` | void |
| Add child | `AddOrderLineCommand` | void |
| Remove child | `RemoveOrderLineCommand` | void |

## Handler Patterns

### Standard Handler Flow

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

## Generation Instructions

When asked to create a Command:

1. **Name imperatively** (verb + noun)
2. **Define required data** as constructor parameters
3. **Add validation** for command invariants
4. **Create handler** with standard flow
5. **Generate tests** for command and handler

## Usage

To generate a Command, provide:
- Name (e.g., "CreateOrder", "ConfirmPayment")
- Bounded Context (e.g., "Order", "Payment")
- Data fields needed
- Whether it returns ID or void
- Validation rules
