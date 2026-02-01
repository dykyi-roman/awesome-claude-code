# Indirection Pattern

## Definition

Assign responsibility to an intermediate object to mediate between other components or services so that they are not directly coupled.

## When to Apply

- Need to decouple two components
- External system integration
- Avoid direct dependency on volatile classes
- Enable substitution of implementations

## Key Indicators

### When to Use

| Situation | Indirection |
|-----------|-------------|
| External API | Adapter |
| Event handling | Event Dispatcher |
| Multiple handlers | Mediator |
| Configuration | Service Factory |
| Caching | Cache Decorator |

### Benefits

- Reduces direct coupling
- Enables substitution
- Improves testability
- Isolates change impact

## Patterns

### Adapter

```php
<?php

declare(strict_types=1);

// Indirection: Adapter isolates external system
interface PaymentGateway
{
    public function charge(PaymentRequest $request): PaymentResult;
    public function refund(TransactionId $id): RefundResult;
}

// Adapter provides indirection to Stripe
final readonly class StripeAdapter implements PaymentGateway
{
    public function __construct(
        private StripeClient $stripe,
    ) {}

    public function charge(PaymentRequest $request): PaymentResult
    {
        $charge = $this->stripe->charges->create([
            'amount' => $request->amount->cents,
            'currency' => $request->currency->code,
            'source' => $request->token,
            'metadata' => [
                'order_id' => $request->orderId->value,
            ],
        ]);

        return new PaymentResult(
            new TransactionId($charge->id),
            $charge->status === 'succeeded',
            $charge->failure_message,
        );
    }

    public function refund(TransactionId $id): RefundResult
    {
        $refund = $this->stripe->refunds->create([
            'charge' => $id->value,
        ]);

        return new RefundResult(
            $refund->status === 'succeeded',
            $refund->failure_reason,
        );
    }
}

// Application depends on interface, not Stripe
final readonly class ProcessPaymentHandler
{
    public function __construct(
        private PaymentGateway $gateway, // Indirection
    ) {}

    public function __invoke(ProcessPaymentCommand $command): PaymentResult
    {
        return $this->gateway->charge($command->toRequest());
    }
}
```

### Mediator

```php
<?php

declare(strict_types=1);

// Indirection: Mediator coordinates components
interface CommandBus
{
    public function dispatch(Command $command): mixed;
}

final class SyncCommandBus implements CommandBus
{
    /** @var array<string, callable> */
    private array $handlers = [];

    public function register(string $commandClass, callable $handler): void
    {
        $this->handlers[$commandClass] = $handler;
    }

    public function dispatch(Command $command): mixed
    {
        $commandClass = get_class($command);

        if (!isset($this->handlers[$commandClass])) {
            throw new NoHandlerException($commandClass);
        }

        return ($this->handlers[$commandClass])($command);
    }
}

// Components don't know each other - mediated
final readonly class OrderController
{
    public function __construct(
        private CommandBus $commandBus, // Indirection
    ) {}

    public function create(CreateOrderRequest $request): Response
    {
        $orderId = $this->commandBus->dispatch(
            new CreateOrderCommand($request->customerId(), $request->items()),
        );

        return new JsonResponse(['id' => $orderId->value]);
    }
}
```

### Event Dispatcher

```php
<?php

declare(strict_types=1);

// Indirection: Event dispatcher decouples publishers from subscribers
interface EventDispatcher
{
    public function dispatch(DomainEvent ...$events): void;
}

final class AsyncEventDispatcher implements EventDispatcher
{
    public function __construct(
        private MessageBus $messageBus,
    ) {}

    public function dispatch(DomainEvent ...$events): void
    {
        foreach ($events as $event) {
            $this->messageBus->dispatch(
                new EventMessage($event),
            );
        }
    }
}

// Publisher doesn't know subscribers
final readonly class PlaceOrderHandler
{
    public function __construct(
        private OrderRepository $orders,
        private EventDispatcher $events, // Indirection
    ) {}

    public function __invoke(PlaceOrderCommand $command): OrderId
    {
        $order = Order::place(/* ... */);
        $this->orders->save($order);
        $this->events->dispatch(...$order->releaseEvents());

        return $order->id;
    }
}

// Subscriber doesn't know publisher
final readonly class SendOrderConfirmationOnOrderPlaced
{
    public function __construct(
        private OrderReader $orders,
        private Mailer $mailer,
    ) {}

    public function __invoke(OrderPlaced $event): void
    {
        $order = $this->orders->get($event->orderId);
        $this->mailer->send(new OrderConfirmation($order));
    }
}
```

### Anti-Corruption Layer

```php
<?php

declare(strict_types=1);

// Indirection: ACL protects domain from external models
interface LegacyOrderAdapter
{
    public function import(string $legacyId): Order;
    public function export(Order $order): void;
}

final readonly class LegacyErpAdapter implements LegacyOrderAdapter
{
    public function __construct(
        private ErpClient $erp,
        private OrderTranslator $translator,
    ) {}

    public function import(string $legacyId): Order
    {
        // Get legacy data
        $legacyOrder = $this->erp->getOrder($legacyId);

        // Translate to our domain model
        return $this->translator->toDomain($legacyOrder);
    }

    public function export(Order $order): void
    {
        // Translate to legacy format
        $legacyData = $this->translator->toLegacy($order);

        // Send to legacy system
        $this->erp->createOrder($legacyData);
    }
}

final readonly class OrderTranslator
{
    public function toDomain(LegacyOrder $legacy): Order
    {
        return new Order(
            new OrderId($legacy->ORDER_NUMBER),
            new CustomerId($legacy->CUST_ID),
            $this->translateLines($legacy->LINES),
            $this->translateStatus($legacy->STATUS_CODE),
        );
    }

    public function toLegacy(Order $order): LegacyOrder
    {
        return new LegacyOrder(
            ORDER_NUMBER: $order->id->value,
            CUST_ID: $order->customerId->value,
            LINES: $this->translateLinesToLegacy($order->lines),
            STATUS_CODE: $this->translateStatusToLegacy($order->status),
        );
    }
}
```

### Decorator (Transparent Indirection)

```php
<?php

declare(strict_types=1);

// Indirection: Decorator adds behavior transparently
interface Cache
{
    public function get(string $key): mixed;
    public function set(string $key, mixed $value, int $ttl = 3600): void;
}

final readonly class LoggingCache implements Cache
{
    public function __construct(
        private Cache $inner,
        private LoggerInterface $logger,
    ) {}

    public function get(string $key): mixed
    {
        $this->logger->debug('Cache get', ['key' => $key]);
        $value = $this->inner->get($key);
        $this->logger->debug('Cache result', [
            'key' => $key,
            'hit' => $value !== null,
        ]);
        return $value;
    }

    public function set(string $key, mixed $value, int $ttl = 3600): void
    {
        $this->logger->debug('Cache set', ['key' => $key, 'ttl' => $ttl]);
        $this->inner->set($key, $value, $ttl);
    }
}

// Stack decorators
$cache = new LoggingCache(
    new MetricsCache(
        new RedisCache($redis),
        $metrics,
    ),
    $logger,
);
```

### Facade

```php
<?php

declare(strict_types=1);

// Indirection: Facade simplifies subsystem access
interface OrderingFacade
{
    public function placeOrder(PlaceOrderRequest $request): OrderId;
    public function cancelOrder(OrderId $id): void;
    public function getOrderStatus(OrderId $id): OrderStatusDTO;
}

final readonly class DefaultOrderingFacade implements OrderingFacade
{
    public function __construct(
        private CommandBus $commands,
        private QueryBus $queries,
    ) {}

    public function placeOrder(PlaceOrderRequest $request): OrderId
    {
        return $this->commands->dispatch(
            new PlaceOrderCommand(
                $request->customerId,
                $request->items,
            ),
        );
    }

    public function cancelOrder(OrderId $id): void
    {
        $this->commands->dispatch(new CancelOrderCommand($id));
    }

    public function getOrderStatus(OrderId $id): OrderStatusDTO
    {
        return $this->queries->dispatch(new GetOrderStatusQuery($id));
    }
}
```

## DDD Application

### Ports and Adapters

```php
<?php

declare(strict_types=1);

// Port (Domain interface)
namespace Domain\Port;

interface NotificationService
{
    public function notify(CustomerId $customerId, Notification $notification): void;
}

// Adapter (Infrastructure implementation)
namespace Infrastructure\Adapter;

use Domain\Port\NotificationService;

final readonly class EmailNotificationAdapter implements NotificationService
{
    public function __construct(
        private Mailer $mailer,
        private CustomerReader $customers,
    ) {}

    public function notify(CustomerId $customerId, Notification $notification): void
    {
        $customer = $this->customers->get($customerId);

        $this->mailer->send(
            $customer->email,
            $notification->subject,
            $notification->body,
        );
    }
}

// Domain service uses port (indirection)
final readonly class OrderService
{
    public function __construct(
        private OrderRepository $orders,
        private NotificationService $notifications, // Port
    ) {}

    public function complete(OrderId $id): void
    {
        $order = $this->orders->get($id);
        $order->complete();
        $this->orders->save($order);

        $this->notifications->notify(
            $order->customerId,
            new OrderCompletedNotification($order),
        );
    }
}
```

## Anti-patterns

### Over-Indirection

```php
<?php

// ANTIPATTERN: Too many layers of indirection
$result = $controller->handle(
    $request->validate(
        $validator->createFrom(
            $factory->createValidator(
                $config->get('validation.order'),
            ),
        ),
    ),
);

// FIX: Reduce unnecessary layers
$result = $controller->handle($request);
```

## Metrics

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| Indirection layers | 1-2 | 3 | >3 |
| Adapter complexity | <50 LOC | 50-100 | >100 |
| Interface methods | ≤5 | 6-8 | >8 |
