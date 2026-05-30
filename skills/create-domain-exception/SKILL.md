---
name: create-domain-exception
description: Generates Domain Exception classes that signal business-rule violations. Domain exceptions use static factory methods to encode the violation reason, extend a base exception (often `\DomainException`), and live alongside the aggregate they describe. Each Exception class is named per the aggregate/concept (e.g. `OrderException`) and exposes named factories for each violation case.
---

# Domain Exception Generator

Generate Domain Exception classes — typed exceptions raised by the domain when a business rule is violated. Domain exceptions are part of the domain model: they name a business situation, not a technical fault.

## Domain Exception characteristics

- **Named per aggregate or concept**: `OrderException`, `PaymentException`, `EmailException` — one exception class per concept.
- **Static factory methods per case**: `OrderException::notFound($id)`, `OrderException::cannotConfirm($id)`. Each factory describes a specific business situation.
- **Extends a base exception class**: most commonly `\DomainException` (SPL), or a project-local `DomainException` base. NOT `\Exception` directly.
- **Message is domain language**: speaks the ubiquitous language ("Order cannot be confirmed in its current state"), not technical detail.
- **Stable contract**: callers may catch and branch on these — keep factory names stable across refactors.
- **No HTTP / framework details**: never set status codes, never reference framework classes. Translation to HTTP is a Presentation concern.

## When to use

| Scenario | Use a domain exception |
|----------|------------------------|
| Aggregate state forbids an operation (`Order::confirm()` on a cancelled order) | Yes |
| Required entity not found by domain ID | Yes |
| Value Object constructor receives invalid input | Yes (or `\InvalidArgumentException` depending on convention) |
| External service failed (timeout, 500) | No — use an Infrastructure exception |
| Validation of input format (email syntax, required fields) | No — use a Validator constraint / Application-layer exception |
| Authorization failure | No — that's an Application-layer concern |

## Placement

Lives with the domain code; folder placement varies by your project's architecture. A project-wide base `DomainException` typically lives in whatever shared / common domain folder your project uses for cross-context concepts.

## Templates

### Single-aggregate Domain Exception

```php
<?php

declare(strict_types=1);

namespace Exception;

final class OrderException extends \DomainException
{
    public static function notFound(OrderId $id): self
    {
        return new self(sprintf('Order "%s" not found.', $id));
    }

    public static function cannotConfirm(OrderId $id): self
    {
        return new self(sprintf('Order "%s" cannot be confirmed in its current state.', $id));
    }

    public static function alreadyShipped(OrderId $id): self
    {
        return new self(sprintf('Order "%s" has already been shipped.', $id));
    }

    public static function emptyOrder(): self
    {
        return new self('Order has no items.');
    }
}
```

### Value Object validation exception

```php
<?php

declare(strict_types=1);

namespace Exception;

final class EmailException extends \DomainException
{
    public static function invalidFormat(string $value): self
    {
        return new self(sprintf('"%s" is not a valid email address.', $value));
    }

    public static function tooLong(string $value, int $maxLength): self
    {
        return new self(sprintf(
            'Email "%s" exceeds maximum length of %d characters.',
            $value,
            $maxLength,
        ));
    }
}
```

### Base project DomainException (Shared)

```php
<?php

declare(strict_types=1);

namespace Exception;

/**
 * Marker base class for domain-level exceptions in this project.
 * Catchers can use this to distinguish domain violations from
 * infrastructure / framework exceptions.
 */
abstract class DomainException extends \DomainException
{
}
```

Then per-aggregate exceptions extend the project base:

```php
<?php

declare(strict_types=1);

namespace Exception;

final class OrderException extends DomainException
{
    public static function notFound(OrderId $id): self
    {
        return new self(sprintf('Order "%s" not found.', $id));
    }
}
```

### Exception with previous (wrap a lower-level cause)

```php
<?php

declare(strict_types=1);

namespace Exception;

final class PaymentException extends DomainException
{
    public static function gatewayUnreachable(\Throwable $previous): self
    {
        return new self(
            'Payment gateway is currently unreachable.',
            previous: $previous,
        );
    }
}
```

### Unit test pattern

```php
<?php

declare(strict_types=1);

use PHPUnit\Framework\TestCase;

final class OrderExceptionTest extends TestCase
{
    public function testNotFoundMessageIncludesId(): void
    {
        $exception = OrderException::notFound(new OrderId('ORD-123'));

        self::assertStringContainsString('ORD-123', $exception->getMessage());
    }

    public function testIsDomainException(): void
    {
        $exception = OrderException::cannotConfirm(new OrderId('ORD-123'));

        self::assertInstanceOf(\DomainException::class, $exception);
    }
}
```

## Throwing from an entity

```php
<?php

declare(strict_types=1);

namespace Entity;

final class Order
{
    public function confirm(): void
    {
        if (!$this->status->canTransitionTo(OrderStatus::Confirmed)) {
            throw OrderException::cannotConfirm($this->id);
        }
        if (empty($this->lines)) {
            throw OrderException::emptyOrder();
        }

        $this->status = OrderStatus::Confirmed;
    }
}
```

## Catching at the Application boundary

```php
<?php

declare(strict_types=1);

namespace UseCase\ConfirmOrder;

final readonly class ConfirmOrderUseCase
{
    public function __construct(
        private OrderRepositoryInterface $orders,
    ) {}

    public function execute(ConfirmOrderCommand $command): ConfirmOrderResult
    {
        $order = $this->orders->findById($command->orderId)
            ?? throw OrderException::notFound($command->orderId);

        try {
            $order->confirm();
        } catch (OrderException $e) {
            return ConfirmOrderResult::failure($e->getMessage());
        }

        $this->orders->save($order);

        return ConfirmOrderResult::success($order->id());
    }
}
```

## Generation steps

1. **Identify the concept** the exception covers. One class per aggregate / value-object, named `{Concept}Exception`.
2. **Enumerate violation cases** as static factory methods. Each method's name is the business situation, not the technical detail.
3. **Decide the base class** — most projects use a single project-local `DomainException` extending `\DomainException` so catchers can distinguish domain from infrastructure exceptions.
4. **Format messages in ubiquitous language**. Reference the business entity by name and ID where helpful.
5. **Generate unit tests** for each factory (basic instantiation + message content).

## Detection patterns

```bash
# Find domain exceptions
Glob: **/Exception/*Exception.php
Grep: "extends.*DomainException|extends \\\\DomainException" --glob "**/*.php"

# Exceptions without static factories (likely missing the pattern)
Grep: "public static function" --glob "**/Exception/*Exception.php"

# Exceptions thrown without context (no ID, no aggregate reference)
Grep: "throw new.*Exception\\(\\)" --glob "**/Entity/**/*.php"
```

## Antipatterns

| Antipattern | Why it's bad | Fix |
|-------------|--------------|-----|
| Generic `new \Exception('Order not found')` from entity | Hides domain meaning; can't be caught specifically | Define a `{Aggregate}Exception` with a named factory |
| HTTP status code inside the exception | Crosses layer boundary | Translate to HTTP in a subscriber / responder |
| Bare exception with no context | Logs are useless: "Order not found" — which order? | Include aggregate ID / value in message |
| Catching `\Throwable` and re-wrapping in a domain exception | Hides the real error | Re-throw or wrap with explicit cause via `previous:` |
| Static factories returning `\Exception` instead of `self` | Caller loses type info | Always return `self` |
| Per-method-call exception classes (`OrderNotFoundException`, `OrderCannotConfirmException`, ...) instead of one `OrderException` with factories | Class explosion | Group cases per aggregate |
