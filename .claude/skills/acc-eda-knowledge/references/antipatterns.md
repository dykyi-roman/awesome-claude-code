# Event-Driven Architecture Antipatterns

Common violations in EDA with detection patterns and fixes.

## Critical Violations

### 1. Synchronous Calls Disguised as Events

**Description:** Event handler makes synchronous HTTP/RPC calls to other services.

**Why Critical:** Defeats the purpose of async architecture, creates tight coupling, cascading failures.

**Detection:**
```bash
# HTTP clients in event handlers
Grep: "HttpClient|Guzzle|curl_" --glob "**/EventHandler/**/*.php"

# Direct service calls
Grep: "->call\(|->request\(" --glob "**/EventHandler/**/*.php"
```

**Bad:**
```php
namespace Application\Order\EventHandler;

final readonly class NotifyWarehouseOnOrderPlaced
{
    public function __construct(
        private HttpClientInterface $httpClient  // VIOLATION!
    ) {}

    public function __invoke(OrderPlaced $event): void
    {
        // Synchronous HTTP call in event handler!
        $this->httpClient->request('POST', 'http://warehouse/api/reserve', [
            'json' => ['order_id' => $event->orderId],
        ]);
    }
}
```

**Good:**
```php
namespace Application\Order\EventHandler;

final readonly class NotifyWarehouseOnOrderPlaced
{
    public function __construct(
        private EventPublisherInterface $events
    ) {}

    public function __invoke(OrderPlaced $event): void
    {
        // Publish integration event instead
        $this->events->publish(new ReserveInventoryRequested(
            orderId: $event->orderId,
            lines: $event->lineItems
        ));
    }
}
```

### 2. Missing Idempotency

**Description:** Event handlers don't handle duplicate messages.

**Why Critical:** Message brokers deliver at-least-once, duplicates cause data corruption.

**Detection:**
```bash
# Handlers without idempotency check
Grep: "public function __invoke|public function handle" --glob "**/EventHandler/**/*.php" -A 10 | grep -v "exists\|processed\|idempotent"
```

**Bad:**
```php
namespace Application\Order\EventHandler;

final readonly class ProcessPaymentOnOrderPlaced
{
    public function __invoke(OrderPlaced $event): void
    {
        // No idempotency check!
        // If event is delivered twice, customer is charged twice!
        $this->paymentService->charge(
            $event->customerId,
            $event->totalCents
        );
    }
}
```

**Good:**
```php
namespace Application\Order\EventHandler;

final readonly class ProcessPaymentOnOrderPlaced
{
    public function __construct(
        private PaymentServiceInterface $payments,
        private ProcessedEventRepositoryInterface $processedEvents
    ) {}

    public function __invoke(OrderPlaced $event): void
    {
        // Idempotency check
        if ($this->processedEvents->exists($event->eventId)) {
            return;
        }

        // Or check by business key
        if ($this->payments->existsForOrder($event->orderId)) {
            return;
        }

        $this->payments->charge(
            $event->customerId,
            $event->totalCents
        );

        $this->processedEvents->markAsProcessed($event->eventId);
    }
}
```

### 3. Event Data Coupling

**Description:** Event contains entity references or requires fetching additional data.

**Why Critical:** Consumer depends on producer's data model, tight coupling.

**Detection:**
```bash
# Entity references in events
Grep: "->findById|->load\(" --glob "**/EventHandler/**/*.php"

# Events with minimal data
Grep: "class.*Event" --glob "**/Event/**/*.php" -A 20 | grep "public function __construct" -A 5
```

**Bad:**
```php
namespace Domain\Order\Event;

final readonly class OrderPlaced implements DomainEvent
{
    public function __construct(
        public string $orderId  // Only ID, no data!
    ) {}
}

// Consumer must fetch data
namespace Application\Notification\EventHandler;

final readonly class SendOrderConfirmation
{
    public function __invoke(OrderPlaced $event): void
    {
        // Must call Order service to get details - COUPLING!
        $order = $this->orderService->getOrder($event->orderId);

        $this->emailService->send(
            $order->customerEmail(),
            'Order confirmation',
            ['total' => $order->total()]
        );
    }
}
```

**Good:**
```php
namespace Domain\Order\Event;

final readonly class OrderPlaced implements DomainEvent
{
    public function __construct(
        public string $eventId,
        public string $orderId,
        public string $customerId,
        public string $customerEmail,
        public array $lineItems,
        public int $totalCents,
        public \DateTimeImmutable $occurredAt
    ) {}
}

// Consumer is self-sufficient
namespace Application\Notification\EventHandler;

final readonly class SendOrderConfirmation
{
    public function __invoke(OrderPlaced $event): void
    {
        // All needed data in event
        $this->emailService->send(
            $event->customerEmail,
            'Order confirmation',
            ['total' => $event->totalCents / 100]
        );
    }
}
```

### 4. Missing Dead Letter Queue

**Description:** Failed messages are lost or retried infinitely.

**Why Critical:** Data loss, infinite loops, system instability.

**Detection:**
```bash
# Check queue configuration
Grep: "x-dead-letter|dead_letter|dlq" --glob "**/config/**/*.yaml"

# Handlers without error handling
Grep: "public function __invoke|handle\(" --glob "**/EventHandler/**/*.php" -A 20 | grep -v "try\|catch"
```

**Bad:**
```php
// No DLQ configured
$channel->queue_declare('orders', durable: true);

// Consumer without error handling
final readonly class OrderEventConsumer
{
    public function consume(AMQPMessage $message): void
    {
        $payload = json_decode($message->getBody(), true);
        $this->handler->handle($payload);
        $message->ack();
        // If handler throws - message lost or infinite retry!
    }
}
```

**Good:**
```php
// DLQ configured
$channel->queue_declare('orders', durable: true, arguments: [
    'x-dead-letter-exchange' => 'orders.dlq',
    'x-dead-letter-routing-key' => 'orders.failed',
]);

// Consumer with proper error handling
final readonly class OrderEventConsumer
{
    public function consume(AMQPMessage $message): void
    {
        try {
            $payload = json_decode($message->getBody(), true);
            $this->handler->handle($payload);
            $message->ack();

        } catch (RetryableException $e) {
            $message->nack(requeue: true);

        } catch (\Throwable $e) {
            $this->logger->error('Processing failed', ['error' => $e->getMessage()]);
            $message->nack(requeue: false); // Goes to DLQ
        }
    }
}
```

## Warnings

### 5. Fire and Forget Publishing

**Description:** Events published without confirmation or error handling.

**Why Bad:** Silent message loss, inconsistent state.

**Detection:**
```bash
# Publish without confirmation
Grep: "->publish\(" --glob "**/*.php" -B 5 -A 5 | grep -v "try\|catch\|confirm"
```

**Bad:**
```php
final readonly class OrderService
{
    public function placeOrder(CreateOrderDTO $dto): OrderDTO
    {
        $order = Order::place(...);
        $this->orders->save($order);

        // Fire and forget - if broker is down, event is lost!
        $this->events->publish(new OrderPlaced(...));

        return OrderDTO::fromEntity($order);
    }
}
```

**Good:**
```php
final readonly class OrderService
{
    public function placeOrder(CreateOrderDTO $dto): OrderDTO
    {
        return $this->transaction->transactional(function () use ($dto) {
            $order = Order::place(...);
            $this->orders->save($order);

            // Store in outbox - same transaction
            $this->outbox->save(OutboxMessage::fromEvent(new OrderPlaced(...)));

            return OrderDTO::fromEntity($order);
        });

        // Separate process publishes from outbox
    }
}
```

### 6. Events in Controllers

**Description:** Domain events created in presentation layer.

**Why Bad:** Bypasses domain logic, inconsistent event creation.

**Detection:**
```bash
Grep: "new.*Event\(" --glob "**/Controller/**/*.php"
Grep: "->publish\(" --glob "**/Controller/**/*.php"
```

**Bad:**
```php
namespace Presentation\Api\Order;

final readonly class OrderController
{
    public function create(Request $request): JsonResponse
    {
        $order = new Order($request->get('customer_id'));
        $this->orderRepository->save($order);

        // Event creation in controller!
        $this->eventPublisher->publish(new OrderPlaced(
            orderId: $order->id()
        ));

        return new JsonResponse(['id' => $order->id()]);
    }
}
```

**Good:**
```php
namespace Presentation\Api\Order;

final readonly class OrderController
{
    public function create(CreateOrderRequest $request): JsonResponse
    {
        // Delegate to application layer
        $result = $this->createOrderUseCase->execute(
            CreateOrderDTO::fromRequest($request)
        );

        return new JsonResponse(['id' => $result->orderId]);
    }
}

// Events created in domain
namespace Domain\Order\Entity;

final class Order
{
    public static function place(...): self
    {
        $order = new self(...);
        $order->events[] = new OrderPlaced(...);  // Domain creates event
        return $order;
    }
}
```

### 7. Blocking Event Handlers

**Description:** Handler does heavy processing synchronously.

**Why Bad:** Blocks message consumption, queue backlog, timeouts.

**Detection:**
```bash
# Long operations in handlers
Grep: "sleep\(|file_get_contents|curl_exec" --glob "**/EventHandler/**/*.php"

# Database-heavy operations
Grep: "foreach.*->save\(|while.*->persist" --glob "**/EventHandler/**/*.php"
```

**Bad:**
```php
final readonly class GenerateReportOnDayEnd
{
    public function __invoke(DayEnded $event): void
    {
        // Heavy processing blocks consumer
        $orders = $this->orders->findByDate($event->date);

        foreach ($orders as $order) {  // Could be thousands
            $this->reportGenerator->addOrder($order);
        }

        $this->reportGenerator->generate();  // Takes minutes
        $this->emailService->send(...);
    }
}
```

**Good:**
```php
final readonly class GenerateReportOnDayEnd
{
    public function __invoke(DayEnded $event): void
    {
        // Dispatch to background job
        $this->jobDispatcher->dispatch(new GenerateReportJob(
            date: $event->date
        ));
    }
}

// Or use chunked processing
final readonly class OrderReportProjector
{
    public function __invoke(OrderPlaced $event): void
    {
        // Incremental update - fast
        $this->reportStore->incrementDailyTotal(
            $event->occurredAt->format('Y-m-d'),
            $event->totalCents
        );
    }
}
```

### 8. Missing Event Versioning

**Description:** No strategy for evolving event schemas.

**Why Bad:** Breaking changes crash consumers, can't evolve system.

**Detection:**
```bash
# Events without version
Grep: "class.*Event" --glob "**/Event/**/*.php" -A 10 | grep -v "VERSION\|version"
```

**Bad:**
```php
// V1 Event
final readonly class OrderPlaced
{
    public function __construct(
        public string $orderId,
        public int $total  // Changed to totalCents in V2!
    ) {}
}

// Breaking change - old consumers crash
```

**Good:**
```php
final readonly class OrderPlaced
{
    public const VERSION = 2;

    public function __construct(
        public string $eventId,
        public string $orderId,
        public int $totalCents,  // Clear naming
        public \DateTimeImmutable $occurredAt
    ) {}

    public function version(): int
    {
        return self::VERSION;
    }
}

// Upcaster for old events
final readonly class OrderPlacedUpcaster
{
    public function upcast(array $payload, int $fromVersion): array
    {
        if ($fromVersion === 1) {
            $payload['totalCents'] = $payload['total'];
            unset($payload['total']);
        }
        return $payload;
    }
}
```

### 9. Temporal Coupling

**Description:** Events must be processed in specific order but no guarantee.

**Why Bad:** Race conditions, inconsistent state.

**Detection:**
```bash
# Handlers assuming order
Grep: "->status\(\)" --glob "**/EventHandler/**/*.php"
Grep: "if.*status.*===" --glob "**/EventHandler/**/*.php"
```

**Bad:**
```php
final readonly class ShipOrderOnPaymentCompleted
{
    public function __invoke(PaymentCompleted $event): void
    {
        $order = $this->orders->findById($event->orderId);

        // Assumes order exists and is in correct state
        // But OrderPlaced might not be processed yet!
        if ($order->status() !== OrderStatus::Confirmed) {
            throw new \RuntimeException('Order not ready');
        }

        $order->ship();
    }
}
```

**Good:**
```php
final readonly class ShipOrderOnPaymentCompleted
{
    public function __invoke(PaymentCompleted $event): void
    {
        $order = $this->orders->findById($event->orderId);

        if ($order === null) {
            // Requeue for later processing
            throw new RetryableException('Order not found yet');
        }

        if (!$order->canBeShipped()) {
            // Store pending action
            $this->pendingActions->save(new PendingShipment($event->orderId));
            return;
        }

        $order->ship();
    }
}
```

### 10. Shared Message Broker Queues

**Description:** Multiple services share the same queue.

**Why Bad:** Message stealing, unclear ownership, scaling issues.

**Detection:**
```bash
# Check queue bindings across services
Grep: "queue_declare.*orders" --glob "**/config/**/*.yaml"
```

**Bad:**
```yaml
# order-service/config/messenger.yaml
queues:
    events: {binding_keys: ['order.*', 'payment.*']}  # Shared!

# payment-service/config/messenger.yaml
queues:
    events: {binding_keys: ['order.*', 'payment.*']}  # Same queue!
```

**Good:**
```yaml
# order-service/config/messenger.yaml
queues:
    order_service_events:
        binding_keys: ['order.*', 'payment.completed', 'payment.failed']

# payment-service/config/messenger.yaml
queues:
    payment_service_events:
        binding_keys: ['order.placed', 'payment.*']
```

## Severity Matrix

| Antipattern | Severity | Impact | Fix Effort |
|-------------|----------|--------|------------|
| Synchronous calls in handlers | Critical | Coupling | Medium |
| Missing idempotency | Critical | Data corruption | Medium |
| Event data coupling | Critical | Coupling | High |
| Missing DLQ | Critical | Data loss | Low |
| Fire and forget | Warning | Data loss | Medium |
| Events in controllers | Warning | Architecture | Medium |
| Blocking handlers | Warning | Performance | Medium |
| Missing versioning | Warning | Evolution | Medium |
| Temporal coupling | Warning | Consistency | High |
| Shared queues | Warning | Scaling | Low |

## Detection Summary

```bash
# Quick audit script

echo "=== Synchronous Calls in Handlers ==="
Grep: "HttpClient|Guzzle|curl_" --glob "**/EventHandler/**/*.php"

echo "=== Missing Idempotency ==="
Grep: "public function __invoke" --glob "**/EventHandler/**/*.php" -A 10 | grep -v "exists\|processed"

echo "=== Events in Controllers ==="
Grep: "new.*Event\(" --glob "**/Controller/**/*.php"

echo "=== Missing DLQ Configuration ==="
Grep: "queue_declare" --glob "**/*.php" | grep -v "dead-letter"

echo "=== Blocking Operations ==="
Grep: "foreach.*->save|while.*->persist" --glob "**/EventHandler/**/*.php"

echo "=== Missing Event Versioning ==="
Grep: "class.*Event" --glob "**/Event/**/*.php" -A 5 | grep -v "VERSION"
```
