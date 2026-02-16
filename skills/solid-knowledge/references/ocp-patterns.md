# Open/Closed Principle (OCP) Patterns

## Definition

Software entities should be open for extension but closed for modification. Add new functionality by adding new code, not changing existing code.

## Key Indicators

### Violation Signs

| Indicator | Detection | Severity |
|-----------|-----------|----------|
| Switch on instanceof | Code search | CRITICAL |
| Type-based conditionals | Code search | CRITICAL |
| Hardcoded type maps | Array analysis | WARNING |
| Frequent class modifications | Git history | WARNING |
| "else if" chains on type | Code search | WARNING |

### Compliance Signs

- New features = new classes
- Plugin/strategy architecture
- Interface-based polymorphism
- Dependency injection of implementations

## Refactoring Patterns

### Strategy Pattern

```php
<?php

declare(strict_types=1);

// BEFORE: Modification required for new types
final class ShippingCalculator
{
    public function calculate(Order $order): Money
    {
        return match ($order->shippingMethod) {
            'standard' => $this->calculateStandard($order),
            'express' => $this->calculateExpress($order),
            'overnight' => $this->calculateOvernight($order),
            // Must modify for new methods!
        };
    }
}

// AFTER: Open for extension
interface ShippingStrategy
{
    public function supports(ShippingMethod $method): bool;
    public function calculate(Order $order): Money;
}

final readonly class StandardShipping implements ShippingStrategy
{
    public function supports(ShippingMethod $method): bool
    {
        return $method === ShippingMethod::Standard;
    }

    public function calculate(Order $order): Money
    {
        return Money::fromCents($order->weight->grams * 10);
    }
}

final readonly class ExpressShipping implements ShippingStrategy
{
    public function supports(ShippingMethod $method): bool
    {
        return $method === ShippingMethod::Express;
    }

    public function calculate(Order $order): Money
    {
        return Money::fromCents($order->weight->grams * 25);
    }
}

final readonly class ShippingCalculator
{
    /** @param iterable<ShippingStrategy> $strategies */
    public function __construct(
        private iterable $strategies,
    ) {}

    public function calculate(Order $order): Money
    {
        foreach ($this->strategies as $strategy) {
            if ($strategy->supports($order->shippingMethod)) {
                return $strategy->calculate($order);
            }
        }
        throw new UnsupportedShippingMethodException($order->shippingMethod);
    }
}
```

### Decorator Pattern

```php
<?php

declare(strict_types=1);

// Base interface
interface Notifier
{
    public function send(Notification $notification): void;
}

// Core implementation
final readonly class EmailNotifier implements Notifier
{
    public function send(Notification $notification): void
    {
        // Send email
    }
}

// Decorator for extension
final readonly class LoggingNotifier implements Notifier
{
    public function __construct(
        private Notifier $inner,
        private LoggerInterface $logger,
    ) {}

    public function send(Notification $notification): void
    {
        $this->logger->info('Sending notification', ['id' => $notification->id]);
        $this->inner->send($notification);
        $this->logger->info('Notification sent', ['id' => $notification->id]);
    }
}

final readonly class RetryingNotifier implements Notifier
{
    public function __construct(
        private Notifier $inner,
        private int $maxAttempts = 3,
    ) {}

    public function send(Notification $notification): void
    {
        $attempts = 0;
        while ($attempts < $this->maxAttempts) {
            try {
                $this->inner->send($notification);
                return;
            } catch (NotificationException $e) {
                $attempts++;
                if ($attempts >= $this->maxAttempts) {
                    throw $e;
                }
            }
        }
    }
}

// Compose decorators
$notifier = new RetryingNotifier(
    new LoggingNotifier(
        new EmailNotifier(),
        $logger,
    ),
    maxAttempts: 3,
);
```

### Plugin Architecture

```php
<?php

declare(strict_types=1);

// Extension point interface
interface PaymentGateway
{
    public function getName(): string;
    public function process(Payment $payment): PaymentResult;
    public function supportsRefund(): bool;
    public function refund(Payment $payment): RefundResult;
}

// Registry for plugins
final class PaymentGatewayRegistry
{
    /** @var array<string, PaymentGateway> */
    private array $gateways = [];

    public function register(PaymentGateway $gateway): void
    {
        $this->gateways[$gateway->getName()] = $gateway;
    }

    public function get(string $name): PaymentGateway
    {
        return $this->gateways[$name]
            ?? throw new UnknownGatewayException($name);
    }

    /** @return iterable<PaymentGateway> */
    public function all(): iterable
    {
        return $this->gateways;
    }
}

// Plugins can be added without modifying core
final readonly class StripeGateway implements PaymentGateway
{
    public function getName(): string
    {
        return 'stripe';
    }
    // ...
}

final readonly class PayPalGateway implements PaymentGateway
{
    public function getName(): string
    {
        return 'paypal';
    }
    // ...
}
```

### Template Method

```php
<?php

declare(strict_types=1);

// Base class with template
abstract class ReportGenerator
{
    final public function generate(ReportData $data): Report
    {
        $this->validate($data);
        $content = $this->buildContent($data);
        $formatted = $this->format($content);

        return new Report($formatted);
    }

    protected function validate(ReportData $data): void
    {
        // Default validation - can be overridden
    }

    abstract protected function buildContent(ReportData $data): string;
    abstract protected function format(string $content): string;
}

// Extensions
final class PdfReportGenerator extends ReportGenerator
{
    protected function buildContent(ReportData $data): string
    {
        return $this->pdfBuilder->build($data);
    }

    protected function format(string $content): string
    {
        return $this->pdfFormatter->format($content);
    }
}

final class CsvReportGenerator extends ReportGenerator
{
    protected function buildContent(ReportData $data): string
    {
        return $this->csvBuilder->build($data);
    }

    protected function format(string $content): string
    {
        return $content; // CSV needs no formatting
    }
}
```

## DDD Application

### Domain Events for Extension

```php
<?php

declare(strict_types=1);

// Core domain raises events
final class Order
{
    /** @var DomainEvent[] */
    private array $events = [];

    public function place(): void
    {
        $this->status = OrderStatus::Placed;
        $this->events[] = new OrderPlaced($this->id, $this->customerId);
    }
}

// New behavior via event handlers (no modification)
final readonly class SendOrderConfirmationHandler
{
    public function __invoke(OrderPlaced $event): void
    {
        $this->mailer->send(new OrderConfirmation($event->orderId));
    }
}

final readonly class UpdateInventoryHandler
{
    public function __invoke(OrderPlaced $event): void
    {
        $this->inventory->reserve($event->orderId);
    }
}

// Add new handlers without modifying Order class
final readonly class NotifyWarehouseHandler
{
    public function __invoke(OrderPlaced $event): void
    {
        $this->warehouse->prepare($event->orderId);
    }
}
```

### Specification Pattern

```php
<?php

declare(strict_types=1);

// Composable specifications
interface Specification
{
    public function isSatisfiedBy(mixed $candidate): bool;
}

abstract readonly class CompositeSpecification implements Specification
{
    public function and(Specification $other): Specification
    {
        return new AndSpecification($this, $other);
    }

    public function or(Specification $other): Specification
    {
        return new OrSpecification($this, $other);
    }

    public function not(): Specification
    {
        return new NotSpecification($this);
    }
}

// Extend with new specifications without modifying existing
final readonly class PremiumCustomerSpecification extends CompositeSpecification
{
    public function isSatisfiedBy(mixed $candidate): bool
    {
        return $candidate instanceof Customer
            && $candidate->tier === CustomerTier::Premium;
    }
}

final readonly class HighValueOrderSpecification extends CompositeSpecification
{
    public function __construct(
        private Money $threshold,
    ) {}

    public function isSatisfiedBy(mixed $candidate): bool
    {
        return $candidate instanceof Order
            && $candidate->total->isGreaterThan($this->threshold);
    }
}
```

## Configuration-Based Extension

### Service Tags (Symfony)

```php
<?php

// services.yaml
// services:
//   _instanceof:
//     App\Shipping\ShippingStrategy:
//       tags: ['app.shipping_strategy']
//
//   App\Shipping\ShippingCalculator:
//     arguments:
//       $strategies: !tagged_iterator app.shipping_strategy

// New shipping methods auto-discovered
final readonly class DroneShipping implements ShippingStrategy
{
    // Automatically registered as shipping strategy
}
```

## Metrics

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| Switch statements | 0 | 1-2 | >2 |
| instanceof checks | 0 | 1-3 | >3 |
| Modification frequency | Low | Medium | High |
| Plugin count | Many | Few | None |
