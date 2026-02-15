# Unit Testing Patterns

Detailed patterns and examples for unit testing in PHP 8.4.

## Test Class Structure

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\{Layer}\{Module};

use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\DataProvider;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(TargetClass::class)]
final class TargetClassTest extends TestCase
{
    private TargetClass $sut; // System Under Test

    protected function setUp(): void
    {
        $this->sut = new TargetClass();
    }

    // Test methods...
}
```

## Naming Patterns

### Method Under Test

```php
// Testing: Order::confirm()
public function test_confirm_when_pending_changes_status(): void
public function test_confirm_when_already_confirmed_throws_exception(): void
public function test_confirm_records_domain_event(): void
```

### Value Object Validation

```php
// Testing: Email
public function test_creates_with_valid_email(): void
public function test_throws_for_empty_value(): void
public function test_throws_for_invalid_format(): void
public function test_equals_returns_true_for_same_value(): void
public function test_equals_returns_false_for_different_value(): void
```

## Data Providers

```php
#[DataProvider('validEmailsProvider')]
public function test_accepts_valid_email_formats(string $email): void
{
    $valueObject = new Email($email);

    self::assertSame($email, $valueObject->value);
}

public static function validEmailsProvider(): array
{
    return [
        'simple' => ['user@example.com'],
        'with subdomain' => ['user@mail.example.com'],
        'with plus' => ['user+tag@example.com'],
        'with dots' => ['first.last@example.com'],
    ];
}

#[DataProvider('invalidEmailsProvider')]
public function test_rejects_invalid_email_formats(string $email): void
{
    $this->expectException(InvalidArgumentException::class);

    new Email($email);
}

public static function invalidEmailsProvider(): array
{
    return [
        'empty' => [''],
        'no at symbol' => ['userexample.com'],
        'no domain' => ['user@'],
        'no local part' => ['@example.com'],
        'spaces' => ['user @example.com'],
    ];
}
```

## Assertion Patterns

### Value Object Assertions

```php
// Equality
self::assertTrue($email1->equals($email2));
self::assertFalse($email1->equals($email3));

// Value extraction
self::assertSame('expected', $vo->value);

// Type checking
self::assertInstanceOf(Email::class, $email);
```

### Entity Assertions

```php
// State assertions
self::assertTrue($order->isPending());
self::assertFalse($order->isConfirmed());

// Identity assertions
self::assertTrue($order->id()->equals($expectedId));

// Collection assertions
self::assertCount(3, $order->items());
```

### Exception Assertions

```php
// Expect specific exception
$this->expectException(DomainException::class);
$this->expectExceptionMessage('Cannot confirm cancelled order');

$order->confirm();

// Alternative with try-catch for multiple assertions
try {
    $order->confirm();
    self::fail('Expected DomainException');
} catch (DomainException $e) {
    self::assertStringContainsString('cancelled', $e->getMessage());
}
```

## Test Isolation

### Fresh Object per Test

```php
protected function setUp(): void
{
    $this->order = new Order(
        OrderId::generate(),
        CustomerId::generate()
    );
}
```

### Avoid Static State

```php
// BAD - shared state
private static array $cache = [];

// GOOD - instance state, reset in setUp
private array $cache = [];

protected function setUp(): void
{
    $this->cache = [];
}
```

## Mocking Guidelines

### When to Mock

```php
// Mock: external service interface
$emailSender = $this->createMock(EmailSenderInterface::class);
$emailSender->expects($this->once())
    ->method('send')
    ->with($this->isInstanceOf(Email::class));

// Don't mock: Value Object - use real
$email = new Email('user@example.com');

// Don't mock: Entity - use real
$order = new Order(OrderId::generate(), $customerId);
```

### Mock vs Stub

```php
// Stub - just return values
$repository = $this->createStub(UserRepositoryInterface::class);
$repository->method('findById')
    ->willReturn($user);

// Mock - verify interactions
$eventDispatcher = $this->createMock(EventDispatcherInterface::class);
$eventDispatcher->expects($this->once())
    ->method('dispatch')
    ->with($this->isInstanceOf(OrderConfirmedEvent::class));
```

## Test Helpers

### Builder for Complex Objects

```php
final class OrderBuilder
{
    private OrderId $id;
    private CustomerId $customerId;
    private array $items = [];
    private OrderStatus $status;

    public function __construct()
    {
        $this->id = OrderId::generate();
        $this->customerId = CustomerId::generate();
        $this->status = OrderStatus::Pending;
    }

    public static function anOrder(): self
    {
        return new self();
    }

    public function withId(OrderId $id): self
    {
        $this->id = $id;
        return $this;
    }

    public function withItem(Product $product, int $quantity = 1): self
    {
        $this->items[] = new OrderItem($product, $quantity);
        return $this;
    }

    public function confirmed(): self
    {
        $this->status = OrderStatus::Confirmed;
        return $this;
    }

    public function build(): Order
    {
        $order = new Order($this->id, $this->customerId);
        foreach ($this->items as $item) {
            $order->addItem($item);
        }
        if ($this->status === OrderStatus::Confirmed) {
            $order->confirm();
        }
        return $order;
    }
}

// Usage
$order = OrderBuilder::anOrder()
    ->withItem($book)
    ->withItem($pen)
    ->confirmed()
    ->build();
```

### Object Mother for Common Cases

```php
final class OrderMother
{
    public static function pending(): Order
    {
        return new Order(
            OrderId::generate(),
            CustomerMother::default()->id()
        );
    }

    public static function confirmed(): Order
    {
        $order = self::pending();
        $order->addItem(ProductMother::book());
        $order->confirm();
        return $order;
    }

    public static function withTotal(Money $total): Order
    {
        $order = self::pending();
        $order->addItem(new OrderItem(
            ProductMother::withPrice($total),
            1
        ));
        return $order;
    }
}
```

## Performance Tips

1. **Avoid I/O** — no file system, network, database in unit tests
2. **Use in-memory** — Fake repositories, in-memory event stores
3. **Minimize setUp** — only create what's needed
4. **Parallel execution** — ensure test isolation for `--parallel`
