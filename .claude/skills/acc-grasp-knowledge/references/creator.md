# Creator Pattern

## Definition

Assign class B the responsibility to create instances of class A if one of these is true:
1. B contains or compositely aggregates A
2. B records A
3. B closely uses A
4. B has the initializing data for A

## When to Apply

- Deciding where to instantiate objects
- Complex object creation logic
- Aggregate root creating child entities

## Key Indicators

### Violation Signs

| Indicator | Detection | Severity |
|-----------|-----------|----------|
| Random creation | `new` in unexpected places | WARNING |
| No ownership | Objects created everywhere | WARNING |
| Missing factories | Complex creation inline | INFO |

### Compliance Signs

- Container creates contained objects
- Factories for complex creation
- Aggregates create their entities

## Patterns

### Aggregate Creates Children

```php
<?php

declare(strict_types=1);

// Order contains OrderLines, so Order creates them
final class Order
{
    private OrderId $id;
    /** @var OrderLine[] */
    private array $lines = [];
    /** @var DomainEvent[] */
    private array $events = [];

    public function addLine(Product $product, Quantity $quantity): void
    {
        // Order creates OrderLine (contains it)
        $line = new OrderLine(
            OrderLineId::generate(),
            $product->id,
            $product->name,
            $product->price,
            $quantity,
        );

        $this->lines[] = $line;
        $this->events[] = new OrderLineAdded($this->id, $line->id);
    }

    public function removeLine(OrderLineId $lineId): void
    {
        $this->lines = array_filter(
            $this->lines,
            fn(OrderLine $line) => !$line->id->equals($lineId),
        );
        $this->events[] = new OrderLineRemoved($this->id, $lineId);
    }
}
```

### Factory for Complex Creation

```php
<?php

declare(strict_types=1);

// When creation is complex, use Factory
final readonly class OrderFactory
{
    public function __construct(
        private IdGenerator $idGenerator,
        private Clock $clock,
        private CustomerRepository $customers,
        private ProductRepository $products,
    ) {}

    public function createFromCart(CustomerId $customerId, Cart $cart): Order
    {
        $customer = $this->customers->get($customerId);

        $order = new Order(
            $this->idGenerator->generate(),
            $customer->id,
            $customer->shippingAddress,
            $this->clock->now(),
        );

        foreach ($cart->items() as $item) {
            $product = $this->products->get($item->productId);
            $order->addLine($product, $item->quantity);
        }

        return $order;
    }

    public function createFromCommand(CreateOrderCommand $command): Order
    {
        $order = new Order(
            $this->idGenerator->generate(),
            $command->customerId,
            Address::fromArray($command->shippingAddress),
            $this->clock->now(),
        );

        foreach ($command->items as $item) {
            $product = $this->products->get(new ProductId($item['productId']));
            $order->addLine($product, new Quantity($item['quantity']));
        }

        return $order;
    }
}
```

### Builder for Step-by-Step Creation

```php
<?php

declare(strict_types=1);

final class OrderBuilder
{
    private ?CustomerId $customerId = null;
    private ?Address $shippingAddress = null;
    private array $lines = [];
    private ?Discount $discount = null;

    public function forCustomer(CustomerId $customerId): self
    {
        $this->customerId = $customerId;
        return $this;
    }

    public function shippingTo(Address $address): self
    {
        $this->shippingAddress = $address;
        return $this;
    }

    public function withLine(Product $product, Quantity $quantity): self
    {
        $this->lines[] = ['product' => $product, 'quantity' => $quantity];
        return $this;
    }

    public function withDiscount(Discount $discount): self
    {
        $this->discount = $discount;
        return $this;
    }

    public function build(): Order
    {
        $this->validate();

        $order = new Order(
            OrderId::generate(),
            $this->customerId,
            $this->shippingAddress,
        );

        foreach ($this->lines as $line) {
            $order->addLine($line['product'], $line['quantity']);
        }

        if ($this->discount !== null) {
            $order->applyDiscount($this->discount);
        }

        return $order;
    }

    private function validate(): void
    {
        if ($this->customerId === null) {
            throw new InvalidArgumentException('Customer is required');
        }
        if ($this->shippingAddress === null) {
            throw new InvalidArgumentException('Shipping address is required');
        }
        if (empty($this->lines)) {
            throw new InvalidArgumentException('At least one line is required');
        }
    }
}

// Usage
$order = (new OrderBuilder())
    ->forCustomer($customerId)
    ->shippingTo($address)
    ->withLine($product1, new Quantity(2))
    ->withLine($product2, new Quantity(1))
    ->withDiscount(Discount::percentage(10))
    ->build();
```

### Static Factory Methods

```php
<?php

declare(strict_types=1);

// Value Object with factory methods
final readonly class Money
{
    private function __construct(
        public int $cents,
        public Currency $currency,
    ) {}

    public static function zero(Currency $currency = null): self
    {
        return new self(0, $currency ?? Currency::USD());
    }

    public static function fromCents(int $cents, Currency $currency = null): self
    {
        return new self($cents, $currency ?? Currency::USD());
    }

    public static function fromDecimal(float $amount, Currency $currency = null): self
    {
        return new self(
            (int) round($amount * 100),
            $currency ?? Currency::USD(),
        );
    }
}

// Entity with factory method for creation
final class User
{
    private function __construct(
        private UserId $id,
        private Email $email,
        private Password $password,
        private UserStatus $status,
        private DateTimeImmutable $createdAt,
    ) {}

    public static function register(
        UserId $id,
        Email $email,
        Password $password,
        DateTimeImmutable $now,
    ): self {
        return new self(
            $id,
            $email,
            $password,
            UserStatus::Pending,
            $now,
        );
    }
}
```

## DDD Application

### Repository Creates IDs

```php
<?php

declare(strict_types=1);

interface OrderRepository
{
    // Repository provides next identity
    public function nextIdentity(): OrderId;
    public function save(Order $order): void;
    public function find(OrderId $id): ?Order;
}

final readonly class DoctrineOrderRepository implements OrderRepository
{
    public function nextIdentity(): OrderId
    {
        return new OrderId(Uuid::uuid4()->toString());
    }

    // ...
}
```

### Aggregate Creates Domain Events

```php
<?php

declare(strict_types=1);

final class Order
{
    /** @var DomainEvent[] */
    private array $events = [];

    public static function place(
        OrderId $id,
        CustomerId $customerId,
        array $items,
    ): self {
        $order = new self($id, $customerId);

        foreach ($items as $item) {
            $order->addLine($item['product'], $item['quantity']);
        }

        // Order creates its own events
        $order->events[] = new OrderPlaced($id, $customerId);

        return $order;
    }

    public function releaseEvents(): array
    {
        $events = $this->events;
        $this->events = [];
        return $events;
    }
}
```

## Anti-patterns

### Random Creation

```php
<?php

// ANTIPATTERN: Creating in unexpected places
final class EmailService
{
    public function sendOrderConfirmation(OrderData $data): void
    {
        // EmailService shouldn't create Orders!
        $order = new Order($data->id, $data->customerId);
        // ...
    }
}
```

### Service Locator for Creation

```php
<?php

// ANTIPATTERN: Using container for object creation
final class OrderHandler
{
    public function handle(array $data): Order
    {
        // Don't use container to create domain objects
        return $this->container->get(OrderFactory::class)->create($data);
    }
}

// FIX: Inject factory directly
final readonly class OrderHandler
{
    public function __construct(
        private OrderFactory $factory,
    ) {}

    public function handle(array $data): Order
    {
        return $this->factory->create($data);
    }
}
```

## Metrics

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| Creation locations | 1-2 per class | 3-4 | >4 |
| Factory complexity | <50 LOC | 50-100 | >100 |
| Builder steps | ≤7 | 8-10 | >10 |
