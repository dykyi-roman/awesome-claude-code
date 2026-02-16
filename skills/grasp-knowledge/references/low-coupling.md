# Low Coupling Pattern

## Definition

Assign responsibilities so that coupling remains low. Coupling is a measure of how strongly one element is connected to, has knowledge of, or relies upon other elements.

## When to Apply

- Designing class interactions
- Choosing between design alternatives
- Reducing change impact

## Key Indicators

### Violation Signs

| Indicator | Detection | Severity |
|-----------|-----------|----------|
| Many dependencies | >7 constructor args | CRITICAL |
| Concrete type hints | No interfaces | WARNING |
| Cascading changes | One change affects many | WARNING |
| Circular dependencies | A→B→A | CRITICAL |

### Compliance Signs

- Few dependencies (≤5)
- Interface-based design
- Changes are localized
- Easy to test in isolation

## Types of Coupling

| Type | Description | Severity |
|------|-------------|----------|
| Content | Access internal data directly | CRITICAL |
| Common | Share global data | CRITICAL |
| Control | Pass control flags | WARNING |
| Stamp | Pass complex structures | INFO |
| Data | Pass only needed data | GOOD |
| Message | Communicate via messages | GOOD |

## Patterns

### Interface-Based Coupling

```php
<?php

declare(strict_types=1);

// HIGH COUPLING: Depends on concrete classes
final class OrderService
{
    public function __construct(
        private DoctrineOrderRepository $repository,
        private SymfonyMailer $mailer,
        private StripePaymentGateway $payment,
        private RedisCache $cache,
    ) {}
}

// LOW COUPLING: Depends on abstractions
final readonly class OrderService
{
    public function __construct(
        private OrderRepository $repository,
        private Mailer $mailer,
        private PaymentGateway $payment,
        private Cache $cache,
    ) {}
}

// Interfaces define contracts
interface OrderRepository
{
    public function find(OrderId $id): ?Order;
    public function save(Order $order): void;
}

interface Mailer
{
    public function send(Email $email): void;
}

interface PaymentGateway
{
    public function charge(PaymentRequest $request): PaymentResult;
}
```

### Reduce Dependencies

```php
<?php

declare(strict_types=1);

// HIGH COUPLING: Too many dependencies
final class OrderProcessor
{
    public function __construct(
        private OrderRepository $orders,
        private CustomerRepository $customers,
        private ProductRepository $products,
        private InventoryService $inventory,
        private PricingService $pricing,
        private TaxService $tax,
        private ShippingService $shipping,
        private PaymentGateway $payment,
        private NotificationService $notifications,
        private AuditService $audit,
    ) {}
}

// LOW COUPLING: Split responsibilities
final readonly class ProcessOrderHandler
{
    public function __construct(
        private OrderRepository $orders,
        private OrderPricingService $pricing,
        private PaymentGateway $payment,
    ) {}

    public function __invoke(ProcessOrderCommand $command): ProcessResult
    {
        $order = $this->orders->get($command->orderId);
        $total = $this->pricing->calculate($order);
        $payment = $this->payment->charge($order->paymentMethod, $total);

        $order->markAsPaid($payment->transactionId);
        $this->orders->save($order);

        return new ProcessResult($order->id, $payment);
    }
}

// Separate handler for notifications
final readonly class SendOrderConfirmationHandler
{
    public function __construct(
        private OrderRepository $orders,
        private NotificationService $notifications,
    ) {}

    public function __invoke(OrderPaid $event): void
    {
        $order = $this->orders->get($event->orderId);
        $this->notifications->send(new OrderConfirmation($order));
    }
}
```

### Event-Based Decoupling

```php
<?php

declare(strict_types=1);

// HIGH COUPLING: Direct calls to multiple services
final class OrderService
{
    public function place(Order $order): void
    {
        $this->orders->save($order);
        $this->inventory->reserve($order);      // Coupled
        $this->mailer->sendConfirmation($order); // Coupled
        $this->analytics->track($order);         // Coupled
    }
}

// LOW COUPLING: Event-based
final readonly class PlaceOrderHandler
{
    public function __construct(
        private OrderRepository $orders,
        private EventDispatcher $events,
    ) {}

    public function __invoke(PlaceOrderCommand $command): OrderId
    {
        $order = Order::place(
            $this->orders->nextIdentity(),
            $command->customerId,
            $command->items,
        );

        $this->orders->save($order);
        $this->events->dispatch(...$order->releaseEvents());

        return $order->id;
    }
}

// Decoupled listeners
final readonly class ReserveInventoryOnOrderPlaced
{
    public function __invoke(OrderPlaced $event): void
    {
        // Handle inventory
    }
}

final readonly class SendConfirmationOnOrderPlaced
{
    public function __invoke(OrderPlaced $event): void
    {
        // Send email
    }
}
```

### Facade for Subsystem

```php
<?php

declare(strict_types=1);

// Multiple services needed for complex operation
interface ShippingFacade
{
    public function calculateRate(Shipment $shipment): Money;
    public function createLabel(Shipment $shipment): ShippingLabel;
    public function trackPackage(TrackingNumber $number): TrackingInfo;
}

final readonly class ShippingFacadeImpl implements ShippingFacade
{
    public function __construct(
        private CarrierRegistry $carriers,
        private RateCalculator $calculator,
        private LabelGenerator $labelGenerator,
        private TrackingService $tracking,
    ) {}

    public function calculateRate(Shipment $shipment): Money
    {
        $carrier = $this->carriers->get($shipment->carrier);
        return $this->calculator->calculate($carrier, $shipment);
    }

    public function createLabel(Shipment $shipment): ShippingLabel
    {
        return $this->labelGenerator->generate($shipment);
    }

    public function trackPackage(TrackingNumber $number): TrackingInfo
    {
        return $this->tracking->track($number);
    }
}

// Client only depends on facade
final readonly class ShipOrderHandler
{
    public function __construct(
        private OrderRepository $orders,
        private ShippingFacade $shipping, // Single dependency
    ) {}

    public function __invoke(ShipOrderCommand $command): void
    {
        $order = $this->orders->get($command->orderId);
        $label = $this->shipping->createLabel($order->shipment);
        $order->ship($label->trackingNumber);
        $this->orders->save($order);
    }
}
```

### Data Transfer Objects

```php
<?php

declare(strict_types=1);

// HIGH COUPLING: Passing entire entity
interface ReportGenerator
{
    public function generate(Order $order): Report;
    // Coupled to Order class structure
}

// LOW COUPLING: Pass only needed data
interface ReportGenerator
{
    public function generate(ReportData $data): Report;
}

final readonly class ReportData
{
    public function __construct(
        public string $orderNumber,
        public string $customerName,
        public array $lineItems,
        public Money $total,
    ) {}

    public static function fromOrder(Order $order): self
    {
        return new self(
            $order->number->value,
            $order->customer->fullName(),
            array_map(
                fn(OrderLine $line) => [
                    'product' => $line->productName,
                    'quantity' => $line->quantity->value,
                    'price' => $line->price->formatted(),
                ],
                $order->lines,
            ),
            $order->total(),
        );
    }
}
```

## DDD Application

### Bounded Context Isolation

```php
<?php

declare(strict_types=1);

// Orders context shouldn't depend on Shipping internals
namespace Orders\Application;

interface ShippingAdapter
{
    public function calculateShipping(OrderId $orderId): Money;
    public function requestShipment(OrderId $orderId): TrackingNumber;
}

// Implementation in Infrastructure
namespace Orders\Infrastructure\Shipping;

final readonly class ShippingContextAdapter implements ShippingAdapter
{
    public function __construct(
        private ShippingApiClient $client,
    ) {}

    public function calculateShipping(OrderId $orderId): Money
    {
        $result = $this->client->getQuote($orderId->value);
        return Money::fromCents($result['amount'], $result['currency']);
    }
}
```

### Anti-Corruption Layer

```php
<?php

declare(strict_types=1);

// Protect domain from external system coupling
interface LegacyOrderAdapter
{
    public function importOrder(string $legacyOrderId): Order;
    public function exportOrder(Order $order): void;
}

final readonly class LegacyErpAdapter implements LegacyOrderAdapter
{
    public function __construct(
        private ErpClient $erp,
        private OrderTranslator $translator,
    ) {}

    public function importOrder(string $legacyOrderId): Order
    {
        $legacyData = $this->erp->getOrder($legacyOrderId);
        return $this->translator->toOrder($legacyData);
    }

    public function exportOrder(Order $order): void
    {
        $legacyData = $this->translator->toLegacy($order);
        $this->erp->createOrder($legacyData);
    }
}
```

## Metrics

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| Afferent coupling (Ca) | ≤10 | 11-20 | >20 |
| Efferent coupling (Ce) | ≤7 | 8-12 | >12 |
| Instability (Ce/(Ca+Ce)) | 0.3-0.7 | 0.1-0.3 or 0.7-0.9 | <0.1 or >0.9 |
| Circular dependencies | 0 | 0 | >0 |
