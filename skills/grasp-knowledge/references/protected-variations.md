# Protected Variations Pattern

## Definition

Identify points of predicted variation or instability and assign responsibilities to create a stable interface around them.

## When to Apply

- External systems may change
- Business rules are volatile
- Multiple implementations needed
- Technology choices may evolve

## Key Indicators

### Variation Points

| Category | Examples |
|----------|----------|
| External | APIs, databases, payment gateways |
| Business | Tax rules, pricing, discounts |
| Technology | Storage, messaging, caching |
| Platform | OS, frameworks, libraries |

### Protection Mechanisms

| Mechanism | Use Case |
|-----------|----------|
| Interface | Hide implementation details |
| Adapter | Isolate external systems |
| Factory | Hide creation complexity |
| Strategy | Encapsulate algorithms |
| Decorator | Add behavior transparently |

## Patterns

### Interface Abstraction

```php
<?php

declare(strict_types=1);

// Variation: Tax calculation rules change frequently
interface TaxCalculator
{
    public function calculate(Order $order): TaxResult;
}

// Current implementation
final readonly class DefaultTaxCalculator implements TaxCalculator
{
    public function calculate(Order $order): TaxResult
    {
        $taxRate = $this->getTaxRate($order->shippingAddress);
        $taxAmount = $order->subtotal()->multiply($taxRate);

        return new TaxResult($taxAmount, $taxRate);
    }

    private function getTaxRate(Address $address): float
    {
        return match ($address->country->code) {
            'US' => 0.0825,
            'DE' => 0.19,
            'UK' => 0.20,
            default => 0.0,
        };
    }
}

// New implementation (no changes to clients)
final readonly class TaxServiceCalculator implements TaxCalculator
{
    public function __construct(
        private TaxServiceClient $taxService,
    ) {}

    public function calculate(Order $order): TaxResult
    {
        $response = $this->taxService->calculateTax(
            $order->subtotal()->cents,
            $order->shippingAddress->toArray(),
        );

        return new TaxResult(
            Money::fromCents($response->taxAmount),
            $response->taxRate,
        );
    }
}
```

### External System Protection

```php
<?php

declare(strict_types=1);

// Variation: Payment gateway may change (Stripe → Braintree)
interface PaymentGateway
{
    public function charge(PaymentRequest $request): PaymentResult;
    public function refund(TransactionId $id, Money $amount): RefundResult;
    public function getTransaction(TransactionId $id): TransactionDetails;
}

// Protected: Domain doesn't know about Stripe
final readonly class StripeGateway implements PaymentGateway
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
        ]);

        return new PaymentResult(
            new TransactionId($charge->id),
            $charge->status === 'succeeded',
        );
    }

    // ...
}

// Swap to Braintree without domain changes
final readonly class BraintreeGateway implements PaymentGateway
{
    public function __construct(
        private BraintreeClient $braintree,
    ) {}

    public function charge(PaymentRequest $request): PaymentResult
    {
        $result = $this->braintree->transaction()->sale([
            'amount' => $request->amount->formatted(),
            'paymentMethodNonce' => $request->token,
        ]);

        return new PaymentResult(
            new TransactionId($result->transaction->id),
            $result->success,
        );
    }

    // ...
}
```

### Storage Variation Protection

```php
<?php

declare(strict_types=1);

// Variation: Storage technology may change
interface FileStorage
{
    public function store(string $path, string $content): void;
    public function retrieve(string $path): string;
    public function delete(string $path): void;
    public function exists(string $path): bool;
}

final readonly class LocalFileStorage implements FileStorage
{
    public function __construct(
        private string $basePath,
    ) {}

    public function store(string $path, string $content): void
    {
        file_put_contents($this->fullPath($path), $content);
    }

    public function retrieve(string $path): string
    {
        return file_get_contents($this->fullPath($path));
    }

    private function fullPath(string $path): string
    {
        return $this->basePath . '/' . $path;
    }

    // ...
}

final readonly class S3FileStorage implements FileStorage
{
    public function __construct(
        private S3Client $s3,
        private string $bucket,
    ) {}

    public function store(string $path, string $content): void
    {
        $this->s3->putObject([
            'Bucket' => $this->bucket,
            'Key' => $path,
            'Body' => $content,
        ]);
    }

    public function retrieve(string $path): string
    {
        $result = $this->s3->getObject([
            'Bucket' => $this->bucket,
            'Key' => $path,
        ]);

        return (string) $result['Body'];
    }

    // ...
}
```

### Business Rule Protection

```php
<?php

declare(strict_types=1);

// Variation: Discount rules change frequently
interface DiscountPolicy
{
    public function calculate(Order $order): Discount;
}

final readonly class PercentageDiscountPolicy implements DiscountPolicy
{
    public function __construct(
        private Percentage $percentage,
    ) {}

    public function calculate(Order $order): Discount
    {
        return new Discount(
            $order->subtotal()->multiply($this->percentage->value / 100),
        );
    }
}

final readonly class TieredDiscountPolicy implements DiscountPolicy
{
    /** @param array<int, float> $tiers [threshold => percentage] */
    public function __construct(
        private array $tiers,
    ) {}

    public function calculate(Order $order): Discount
    {
        $subtotal = $order->subtotal();
        $percentage = 0.0;

        foreach ($this->tiers as $threshold => $tierPercentage) {
            if ($subtotal->cents >= $threshold) {
                $percentage = $tierPercentage;
            }
        }

        return new Discount($subtotal->multiply($percentage / 100));
    }
}

// Factory protects policy selection
final readonly class DiscountPolicyFactory
{
    public function __construct(
        private ConfigReader $config,
    ) {}

    public function create(Customer $customer): DiscountPolicy
    {
        if ($customer->isPremium()) {
            return new PercentageDiscountPolicy(
                new Percentage($this->config->get('discount.premium')),
            );
        }

        return new TieredDiscountPolicy(
            $this->config->get('discount.tiers'),
        );
    }
}
```

### Configuration Protection

```php
<?php

declare(strict_types=1);

// Variation: Configuration source may change
interface ConfigReader
{
    public function get(string $key, mixed $default = null): mixed;
    public function has(string $key): bool;
}

final readonly class EnvConfigReader implements ConfigReader
{
    public function get(string $key, mixed $default = null): mixed
    {
        return $_ENV[$key] ?? $default;
    }

    public function has(string $key): bool
    {
        return isset($_ENV[$key]);
    }
}

final readonly class VaultConfigReader implements ConfigReader
{
    public function __construct(
        private VaultClient $vault,
        private string $path,
    ) {}

    public function get(string $key, mixed $default = null): mixed
    {
        try {
            $secret = $this->vault->read($this->path);
            return $secret['data'][$key] ?? $default;
        } catch (VaultException) {
            return $default;
        }
    }

    public function has(string $key): bool
    {
        return $this->get($key) !== null;
    }
}
```

### Data Format Protection

```php
<?php

declare(strict_types=1);

// Variation: Data serialization format may change
interface Serializer
{
    public function serialize(mixed $data): string;
    public function deserialize(string $data, string $type): mixed;
}

final readonly class JsonSerializer implements Serializer
{
    public function serialize(mixed $data): string
    {
        return json_encode($data, JSON_THROW_ON_ERROR);
    }

    public function deserialize(string $data, string $type): mixed
    {
        $decoded = json_decode($data, true, 512, JSON_THROW_ON_ERROR);
        return $this->hydrate($decoded, $type);
    }
}

final readonly class MessagePackSerializer implements Serializer
{
    public function serialize(mixed $data): string
    {
        return msgpack_pack($data);
    }

    public function deserialize(string $data, string $type): mixed
    {
        $unpacked = msgpack_unpack($data);
        return $this->hydrate($unpacked, $type);
    }
}
```

## DDD Application

### Bounded Context Protection

```php
<?php

declare(strict_types=1);

// Variation: Other bounded contexts may change
namespace Orders\Infrastructure\Adapter;

interface InventoryService
{
    public function checkAvailability(ProductId $productId, Quantity $quantity): bool;
    public function reserve(OrderId $orderId, ProductId $productId, Quantity $quantity): void;
}

final readonly class InventoryContextAdapter implements InventoryService
{
    public function __construct(
        private InventoryApiClient $client,
    ) {}

    public function checkAvailability(ProductId $productId, Quantity $quantity): bool
    {
        $response = $this->client->getStock($productId->value);
        return $response['available'] >= $quantity->value;
    }

    public function reserve(OrderId $orderId, ProductId $productId, Quantity $quantity): void
    {
        $this->client->createReservation([
            'order_id' => $orderId->value,
            'product_id' => $productId->value,
            'quantity' => $quantity->value,
        ]);
    }
}
```

### Domain Event Protection

```php
<?php

declare(strict_types=1);

// Variation: Event handlers may change
interface EventDispatcher
{
    public function dispatch(DomainEvent ...$events): void;
}

// Sync implementation
final class SyncEventDispatcher implements EventDispatcher { /* ... */ }

// Async implementation
final class AsyncEventDispatcher implements EventDispatcher
{
    public function dispatch(DomainEvent ...$events): void
    {
        foreach ($events as $event) {
            $this->messageBus->dispatch(
                new EventEnvelope($event),
            );
        }
    }
}

// Domain is protected from dispatch mechanism
final readonly class OrderService
{
    public function __construct(
        private EventDispatcher $events, // Protected from variation
    ) {}
}
```

## Metrics

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| Variation points identified | All | Most | Few |
| Interface stability | High | Medium | Low |
| External dependencies | Wrapped | Partially | Direct |
| Change impact | Localized | Moderate | Widespread |
