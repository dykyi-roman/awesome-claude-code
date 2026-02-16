# Other Fake Implementations

Common fake implementations for testing beyond repositories.

## Collecting Event Dispatcher

```php
<?php

declare(strict_types=1);

namespace Tests\Fake;

use Psr\EventDispatcher\EventDispatcherInterface;

final class CollectingEventDispatcher implements EventDispatcherInterface
{
    /** @var list<object> */
    private array $events = [];

    public function dispatch(object $event): object
    {
        $this->events[] = $event;
        return $event;
    }

    /** @return list<object> */
    public function dispatchedEvents(): array
    {
        return $this->events;
    }

    /** @return list<object> */
    public function dispatchedEventsOf(string $eventClass): array
    {
        return array_values(array_filter(
            $this->events,
            fn(object $event) => $event instanceof $eventClass
        ));
    }

    public function hasDispatched(string $eventClass): bool
    {
        return count($this->dispatchedEventsOf($eventClass)) > 0;
    }

    public function clear(): void
    {
        $this->events = [];
    }
}
```

## Collecting Mailer

```php
<?php

declare(strict_types=1);

namespace Tests\Fake;

use App\Infrastructure\Email\MailerInterface;
use App\Infrastructure\Email\EmailMessage;

final class InMemoryMailer implements MailerInterface
{
    /** @var list<EmailMessage> */
    private array $sent = [];

    public function send(EmailMessage $message): void
    {
        $this->sent[] = $message;
    }

    /** @return list<EmailMessage> */
    public function sentMessages(): array
    {
        return $this->sent;
    }

    /** @return list<EmailMessage> */
    public function sentTo(string $email): array
    {
        return array_values(array_filter(
            $this->sent,
            fn(EmailMessage $msg) => $msg->to === $email
        ));
    }

    public function hasNotSentAny(): bool
    {
        return empty($this->sent);
    }

    public function clear(): void
    {
        $this->sent = [];
    }
}
```

## Frozen Clock

```php
<?php

declare(strict_types=1);

namespace Tests\Fake;

use Psr\Clock\ClockInterface;
use DateTimeImmutable;

final class FrozenClock implements ClockInterface
{
    public function __construct(
        private DateTimeImmutable $now
    ) {}

    public function now(): DateTimeImmutable
    {
        return $this->now;
    }

    public static function at(string $datetime): self
    {
        return new self(new DateTimeImmutable($datetime));
    }

    public static function now(): self
    {
        return new self(new DateTimeImmutable());
    }

    public function advance(string $interval): self
    {
        return new self($this->now->modify($interval));
    }
}
```

## Usage in Tests

```php
final class PlaceOrderHandlerTest extends TestCase
{
    private PlaceOrderHandler $handler;
    private InMemoryOrderRepository $orderRepository;
    private InMemoryProductRepository $productRepository;
    private CollectingEventDispatcher $eventDispatcher;

    protected function setUp(): void
    {
        $this->orderRepository = new InMemoryOrderRepository();
        $this->productRepository = new InMemoryProductRepository();
        $this->eventDispatcher = new CollectingEventDispatcher();

        $this->handler = new PlaceOrderHandler(
            $this->orderRepository,
            $this->productRepository,
            $this->eventDispatcher
        );
    }

    public function test_places_order(): void
    {
        // Arrange
        $product = ProductMother::book();
        $this->productRepository->save($product);

        // Act
        $orderId = $this->handler->handle(new PlaceOrderCommand(
            customerId: 'customer-123',
            items: [['productId' => $product->id()->toString(), 'quantity' => 2]]
        ));

        // Assert - check repository
        $order = $this->orderRepository->findById(OrderId::fromString($orderId));
        self::assertNotNull($order);

        // Assert - check events
        self::assertTrue($this->eventDispatcher->hasDispatched(OrderPlacedEvent::class));
    }
}
```
