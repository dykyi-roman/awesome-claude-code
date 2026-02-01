# Polymorphism Pattern

## Definition

When related alternatives or behaviors vary by type, assign responsibility for the behavior to the types using polymorphic operations instead of conditionals.

## When to Apply

- Multiple types require different behavior
- Type-based conditionals (switch/if-else)
- Behavior varies by classification
- Need to add new types without modification

## Key Indicators

### Violation Signs

| Indicator | Detection | Severity |
|-----------|-----------|----------|
| Type switch | `match($type)` | CRITICAL |
| instanceof chains | `if instanceof` | CRITICAL |
| Type-based conditionals | `if ($type === 'X')` | WARNING |
| Parallel class hierarchies | Similar switches | WARNING |

### Compliance Signs

- No type checking conditionals
- Common interface for variants
- New types don't require modification
- Strategy/Plugin architecture

## Patterns

### Replace Type Switch

```php
<?php

declare(strict_types=1);

// BEFORE: Type-based conditional
final class NotificationService
{
    public function send(Notification $notification): void
    {
        match ($notification->type) {
            'email' => $this->sendEmail($notification),
            'sms' => $this->sendSms($notification),
            'push' => $this->sendPush($notification),
            'slack' => $this->sendSlack($notification),
            // Must modify for new types
        };
    }

    private function sendEmail(Notification $notification): void { /* ... */ }
    private function sendSms(Notification $notification): void { /* ... */ }
    private function sendPush(Notification $notification): void { /* ... */ }
    private function sendSlack(Notification $notification): void { /* ... */ }
}

// AFTER: Polymorphic behavior
interface NotificationChannel
{
    public function supports(Notification $notification): bool;
    public function send(Notification $notification): void;
}

final readonly class EmailChannel implements NotificationChannel
{
    public function __construct(
        private Mailer $mailer,
    ) {}

    public function supports(Notification $notification): bool
    {
        return $notification->channel === 'email';
    }

    public function send(Notification $notification): void
    {
        $this->mailer->send(
            $notification->recipient->email,
            $notification->subject,
            $notification->body,
        );
    }
}

final readonly class SmsChannel implements NotificationChannel
{
    public function __construct(
        private SmsGateway $gateway,
    ) {}

    public function supports(Notification $notification): bool
    {
        return $notification->channel === 'sms';
    }

    public function send(Notification $notification): void
    {
        $this->gateway->send(
            $notification->recipient->phone,
            $notification->body,
        );
    }
}

final readonly class NotificationService
{
    /** @param iterable<NotificationChannel> $channels */
    public function __construct(
        private iterable $channels,
    ) {}

    public function send(Notification $notification): void
    {
        foreach ($this->channels as $channel) {
            if ($channel->supports($notification)) {
                $channel->send($notification);
                return;
            }
        }
        throw new UnsupportedChannelException($notification->channel);
    }
}
```

### Strategy Pattern

```php
<?php

declare(strict_types=1);

// Polymorphic strategies for algorithms
interface DiscountStrategy
{
    public function calculate(Order $order): Money;
}

final readonly class PercentageDiscount implements DiscountStrategy
{
    public function __construct(
        private Percentage $percentage,
    ) {}

    public function calculate(Order $order): Money
    {
        return $order->subtotal()->multiply($this->percentage->value / 100);
    }
}

final readonly class FixedAmountDiscount implements DiscountStrategy
{
    public function __construct(
        private Money $amount,
    ) {}

    public function calculate(Order $order): Money
    {
        $subtotal = $order->subtotal();
        return $this->amount->isGreaterThan($subtotal)
            ? $subtotal
            : $this->amount;
    }
}

final readonly class BuyOneGetOneDiscount implements DiscountStrategy
{
    public function calculate(Order $order): Money
    {
        $eligibleItems = $order->eligibleForBogo();
        $discount = Money::zero();

        foreach ($eligibleItems as $item) {
            $freeItems = (int) floor($item->quantity->value / 2);
            $discount = $discount->add($item->price->multiply($freeItems));
        }

        return $discount;
    }
}

// Context uses strategy polymorphically
final readonly class PricingService
{
    public function calculateTotal(Order $order, ?DiscountStrategy $discount): Money
    {
        $subtotal = $order->subtotal();

        if ($discount === null) {
            return $subtotal;
        }

        return $subtotal->subtract($discount->calculate($order));
    }
}
```

### State Pattern

```php
<?php

declare(strict_types=1);

// Polymorphic state behavior
interface OrderState
{
    public function canAddItems(): bool;
    public function canPay(): bool;
    public function canShip(): bool;
    public function canCancel(): bool;
}

final readonly class DraftState implements OrderState
{
    public function canAddItems(): bool { return true; }
    public function canPay(): bool { return true; }
    public function canShip(): bool { return false; }
    public function canCancel(): bool { return true; }
}

final readonly class PaidState implements OrderState
{
    public function canAddItems(): bool { return false; }
    public function canPay(): bool { return false; }
    public function canShip(): bool { return true; }
    public function canCancel(): bool { return true; }
}

final readonly class ShippedState implements OrderState
{
    public function canAddItems(): bool { return false; }
    public function canPay(): bool { return false; }
    public function canShip(): bool { return false; }
    public function canCancel(): bool { return false; }
}

final class Order
{
    private OrderState $state;

    public function __construct()
    {
        $this->state = new DraftState();
    }

    public function addLine(OrderLine $line): void
    {
        if (!$this->state->canAddItems()) {
            throw new CannotModifyOrderException();
        }
        $this->lines[] = $line;
    }

    public function pay(PaymentDetails $payment): void
    {
        if (!$this->state->canPay()) {
            throw new CannotPayOrderException();
        }
        $this->processPayment($payment);
        $this->state = new PaidState();
    }

    public function ship(): void
    {
        if (!$this->state->canShip()) {
            throw new CannotShipOrderException();
        }
        $this->state = new ShippedState();
    }
}
```

### Plugin Architecture

```php
<?php

declare(strict_types=1);

// Extensible plugin system
interface PaymentGateway
{
    public function getName(): string;
    public function isAvailable(): bool;
    public function charge(PaymentRequest $request): PaymentResult;
    public function refund(TransactionId $id, Money $amount): RefundResult;
}

final readonly class StripeGateway implements PaymentGateway
{
    public function getName(): string { return 'stripe'; }
    public function isAvailable(): bool { return true; }
    public function charge(PaymentRequest $request): PaymentResult { /* ... */ }
    public function refund(TransactionId $id, Money $amount): RefundResult { /* ... */ }
}

final readonly class PayPalGateway implements PaymentGateway
{
    public function getName(): string { return 'paypal'; }
    public function isAvailable(): bool { return true; }
    public function charge(PaymentRequest $request): PaymentResult { /* ... */ }
    public function refund(TransactionId $id, Money $amount): RefundResult { /* ... */ }
}

// Registry for polymorphic access
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
        if (!isset($this->gateways[$name])) {
            throw new UnknownGatewayException($name);
        }
        return $this->gateways[$name];
    }

    /** @return iterable<PaymentGateway> */
    public function available(): iterable
    {
        return array_filter(
            $this->gateways,
            fn(PaymentGateway $g) => $g->isAvailable(),
        );
    }
}
```

### Visitor Pattern

```php
<?php

declare(strict_types=1);

// Double dispatch for type-specific operations
interface DocumentVisitor
{
    public function visitPdf(PdfDocument $doc): mixed;
    public function visitWord(WordDocument $doc): mixed;
    public function visitExcel(ExcelDocument $doc): mixed;
}

interface Document
{
    public function accept(DocumentVisitor $visitor): mixed;
}

final readonly class PdfDocument implements Document
{
    public function accept(DocumentVisitor $visitor): mixed
    {
        return $visitor->visitPdf($this);
    }
}

final readonly class WordDocument implements Document
{
    public function accept(DocumentVisitor $visitor): mixed
    {
        return $visitor->visitWord($this);
    }
}

// Different operations as visitors
final readonly class ExportVisitor implements DocumentVisitor
{
    public function visitPdf(PdfDocument $doc): string
    {
        return $this->pdfExporter->export($doc);
    }

    public function visitWord(WordDocument $doc): string
    {
        return $this->wordExporter->export($doc);
    }

    public function visitExcel(ExcelDocument $doc): string
    {
        return $this->excelExporter->export($doc);
    }
}
```

## DDD Application

### Value Object Polymorphism

```php
<?php

declare(strict_types=1);

// Different address types with common behavior
interface Address
{
    public function formatted(): string;
    public function country(): Country;
}

final readonly class UsAddress implements Address
{
    public function __construct(
        private string $street,
        private string $city,
        private UsState $state,
        private ZipCode $zipCode,
    ) {}

    public function formatted(): string
    {
        return sprintf(
            "%s\n%s, %s %s",
            $this->street,
            $this->city,
            $this->state->code,
            $this->zipCode->value,
        );
    }

    public function country(): Country
    {
        return Country::US();
    }
}

final readonly class UkAddress implements Address
{
    public function __construct(
        private string $street,
        private string $city,
        private string $county,
        private PostCode $postCode,
    ) {}

    public function formatted(): string
    {
        return sprintf(
            "%s\n%s\n%s\n%s",
            $this->street,
            $this->city,
            $this->county,
            $this->postCode->value,
        );
    }

    public function country(): Country
    {
        return Country::UK();
    }
}
```

## Metrics

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| Type switches | 0 | 1-2 | >2 |
| instanceof checks | 0 | 1-3 | >3 |
| Strategy implementations | Many | Few | None |
| Adding new type | No changes | Few changes | Many changes |
