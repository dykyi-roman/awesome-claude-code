# Chain of Responsibility Pattern Examples

## Validation Chain

### NotEmptyValidationHandler

**File:** `src/Domain/Validation/Handler/NotEmptyValidationHandler.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Validation\Handler;

use Domain\Validation\ValueObject\ValidationRequest;
use Domain\Validation\ValueObject\ValidationResult;

final class NotEmptyValidationHandler extends AbstractValidationHandler
{
    public function __construct(
        private readonly string $field
    ) {}

    protected function doValidate(ValidationRequest $request): ValidationResult
    {
        $value = $request->get($this->field);

        if ($value === null || $value === '') {
            return ValidationResult::invalid(
                $this->field,
                sprintf('%s cannot be empty', $this->field)
            );
        }

        return ValidationResult::valid();
    }
}
```

---

### EmailValidationHandler

**File:** `src/Domain/Validation/Handler/EmailValidationHandler.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Validation\Handler;

use Domain\Validation\ValueObject\ValidationRequest;
use Domain\Validation\ValueObject\ValidationResult;

final class EmailValidationHandler extends AbstractValidationHandler
{
    public function __construct(
        private readonly string $field
    ) {}

    protected function doValidate(ValidationRequest $request): ValidationResult
    {
        $value = $request->get($this->field);

        if ($value === null) {
            return ValidationResult::valid();
        }

        if (!filter_var($value, FILTER_VALIDATE_EMAIL)) {
            return ValidationResult::invalid(
                $this->field,
                'Invalid email format'
            );
        }

        return ValidationResult::valid();
    }
}
```

---

### MinLengthValidationHandler

**File:** `src/Domain/Validation/Handler/MinLengthValidationHandler.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Validation\Handler;

use Domain\Validation\ValueObject\ValidationRequest;
use Domain\Validation\ValueObject\ValidationResult;

final class MinLengthValidationHandler extends AbstractValidationHandler
{
    public function __construct(
        private readonly string $field,
        private readonly int $minLength
    ) {}

    protected function doValidate(ValidationRequest $request): ValidationResult
    {
        $value = $request->get($this->field);

        if ($value === null) {
            return ValidationResult::valid();
        }

        if (mb_strlen($value) < $this->minLength) {
            return ValidationResult::invalid(
                $this->field,
                sprintf('%s must be at least %d characters', $this->field, $this->minLength)
            );
        }

        return ValidationResult::valid();
    }
}
```

---

## Discount Chain

### DiscountHandlerInterface

**File:** `src/Domain/Pricing/Handler/DiscountHandlerInterface.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Pricing\Handler;

use Domain\Pricing\ValueObject\DiscountRequest;
use Domain\Pricing\ValueObject\DiscountResult;

interface DiscountHandlerInterface
{
    public function setNext(self $handler): self;

    public function apply(DiscountRequest $request): DiscountResult;
}
```

---

### AbstractDiscountHandler

**File:** `src/Domain/Pricing/Handler/AbstractDiscountHandler.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Pricing\Handler;

use Domain\Pricing\ValueObject\DiscountRequest;
use Domain\Pricing\ValueObject\DiscountResult;

abstract class AbstractDiscountHandler implements DiscountHandlerInterface
{
    private ?DiscountHandlerInterface $next = null;

    public function setNext(DiscountHandlerInterface $handler): DiscountHandlerInterface
    {
        $this->next = $handler;
        return $handler;
    }

    public function apply(DiscountRequest $request): DiscountResult
    {
        $result = $this->tryApply($request);

        if ($result !== null) {
            return $result;
        }

        if ($this->next !== null) {
            return $this->next->apply($request);
        }

        return DiscountResult::noDiscount($request->originalPrice());
    }

    abstract protected function tryApply(DiscountRequest $request): ?DiscountResult;
}
```

---

### VipDiscountHandler

**File:** `src/Domain/Pricing/Handler/VipDiscountHandler.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Pricing\Handler;

use Domain\Pricing\ValueObject\DiscountRequest;
use Domain\Pricing\ValueObject\DiscountResult;

final class VipDiscountHandler extends AbstractDiscountHandler
{
    private const VIP_DISCOUNT_PERCENT = 20;

    protected function tryApply(DiscountRequest $request): ?DiscountResult
    {
        if (!$request->customer()->isVip()) {
            return null;
        }

        $discountAmount = $request->originalPrice()->multiply(self::VIP_DISCOUNT_PERCENT / 100);

        return DiscountResult::applied(
            originalPrice: $request->originalPrice(),
            discount: $discountAmount,
            reason: 'VIP customer discount'
        );
    }
}
```

---

### PromoCodeDiscountHandler

**File:** `src/Domain/Pricing/Handler/PromoCodeDiscountHandler.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Pricing\Handler;

use Domain\Pricing\ValueObject\DiscountRequest;
use Domain\Pricing\ValueObject\DiscountResult;

final class PromoCodeDiscountHandler extends AbstractDiscountHandler
{
    public function __construct(
        private readonly PromoCodeRepository $promoCodes
    ) {}

    protected function tryApply(DiscountRequest $request): ?DiscountResult
    {
        $code = $request->promoCode();

        if ($code === null) {
            return null;
        }

        $promo = $this->promoCodes->findByCode($code);

        if ($promo === null || !$promo->isValid()) {
            return null;
        }

        $discountAmount = $promo->calculateDiscount($request->originalPrice());

        return DiscountResult::applied(
            originalPrice: $request->originalPrice(),
            discount: $discountAmount,
            reason: sprintf('Promo code: %s', $code)
        );
    }
}
```

---

### BulkDiscountHandler

**File:** `src/Domain/Pricing/Handler/BulkDiscountHandler.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Pricing\Handler;

use Domain\Pricing\ValueObject\DiscountRequest;
use Domain\Pricing\ValueObject\DiscountResult;

final class BulkDiscountHandler extends AbstractDiscountHandler
{
    private const BULK_THRESHOLD = 10;
    private const BULK_DISCOUNT_PERCENT = 10;

    protected function tryApply(DiscountRequest $request): ?DiscountResult
    {
        if ($request->quantity() < self::BULK_THRESHOLD) {
            return null;
        }

        $discountAmount = $request->originalPrice()->multiply(self::BULK_DISCOUNT_PERCENT / 100);

        return DiscountResult::applied(
            originalPrice: $request->originalPrice(),
            discount: $discountAmount,
            reason: sprintf('Bulk discount (%d+ items)', self::BULK_THRESHOLD)
        );
    }
}
```

---

## Unit Tests

### NotEmptyValidationHandlerTest

**File:** `tests/Unit/Domain/Validation/Handler/NotEmptyValidationHandlerTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\Validation\Handler;

use Domain\Validation\Handler\NotEmptyValidationHandler;
use Domain\Validation\ValueObject\ValidationRequest;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(NotEmptyValidationHandler::class)]
final class NotEmptyValidationHandlerTest extends TestCase
{
    public function testPassesWhenFieldHasValue(): void
    {
        $handler = new NotEmptyValidationHandler('email');
        $request = new ValidationRequest(['email' => 'test@example.com']);

        $result = $handler->validate($request);

        self::assertTrue($result->isValid());
    }

    public function testFailsWhenFieldIsEmpty(): void
    {
        $handler = new NotEmptyValidationHandler('email');
        $request = new ValidationRequest(['email' => '']);

        $result = $handler->validate($request);

        self::assertFalse($result->isValid());
        self::assertSame('email', $result->getField());
    }

    public function testFailsWhenFieldIsNull(): void
    {
        $handler = new NotEmptyValidationHandler('email');
        $request = new ValidationRequest(['email' => null]);

        $result = $handler->validate($request);

        self::assertFalse($result->isValid());
    }

    public function testFailsWhenFieldIsMissing(): void
    {
        $handler = new NotEmptyValidationHandler('email');
        $request = new ValidationRequest([]);

        $result = $handler->validate($request);

        self::assertFalse($result->isValid());
    }
}
```

---

### ValidationChainTest

**File:** `tests/Unit/Domain/Validation/Handler/ValidationChainTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\Validation\Handler;

use Domain\Validation\Handler\EmailValidationHandler;
use Domain\Validation\Handler\MinLengthValidationHandler;
use Domain\Validation\Handler\NotEmptyValidationHandler;
use Domain\Validation\Handler\ValidationChainBuilder;
use Domain\Validation\ValueObject\ValidationRequest;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(ValidationChainBuilder::class)]
final class ValidationChainTest extends TestCase
{
    public function testChainProcessesAllHandlers(): void
    {
        $chain = (new ValidationChainBuilder())
            ->add(new NotEmptyValidationHandler('email'))
            ->add(new EmailValidationHandler('email'))
            ->build();

        $validRequest = new ValidationRequest(['email' => 'test@example.com']);

        $result = $chain->validate($validRequest);

        self::assertTrue($result->isValid());
    }

    public function testChainStopsOnFirstError(): void
    {
        $chain = (new ValidationChainBuilder())
            ->add(new NotEmptyValidationHandler('email'))
            ->add(new EmailValidationHandler('email'))
            ->build();

        $invalidRequest = new ValidationRequest(['email' => '']);

        $result = $chain->validate($invalidRequest);

        self::assertFalse($result->isValid());
        self::assertStringContainsString('cannot be empty', $result->getMessage());
    }

    public function testMultipleFieldValidation(): void
    {
        $chain = (new ValidationChainBuilder())
            ->add(new NotEmptyValidationHandler('name'))
            ->add(new MinLengthValidationHandler('name', 2))
            ->add(new NotEmptyValidationHandler('email'))
            ->add(new EmailValidationHandler('email'))
            ->build();

        $request = new ValidationRequest([
            'name' => 'John',
            'email' => 'john@example.com',
        ]);

        $result = $chain->validate($request);

        self::assertTrue($result->isValid());
    }
}
```

---

### DiscountChainTest

**File:** `tests/Unit/Domain/Pricing/Handler/DiscountChainTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\Pricing\Handler;

use Domain\Pricing\Handler\BulkDiscountHandler;
use Domain\Pricing\Handler\VipDiscountHandler;
use Domain\Pricing\ValueObject\DiscountRequest;
use Domain\Pricing\ValueObject\Money;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(VipDiscountHandler::class)]
#[CoversClass(BulkDiscountHandler::class)]
final class DiscountChainTest extends TestCase
{
    public function testVipDiscountTakesPrecedence(): void
    {
        $vipHandler = new VipDiscountHandler();
        $bulkHandler = new BulkDiscountHandler();

        $vipHandler->setNext($bulkHandler);

        $request = new DiscountRequest(
            originalPrice: Money::cents(10000),
            customer: Customer::vip(),
            quantity: 20
        );

        $result = $vipHandler->apply($request);

        self::assertTrue($result->hasDiscount());
        self::assertStringContainsString('VIP', $result->reason());
    }

    public function testFallsBackToBulkDiscount(): void
    {
        $vipHandler = new VipDiscountHandler();
        $bulkHandler = new BulkDiscountHandler();

        $vipHandler->setNext($bulkHandler);

        $request = new DiscountRequest(
            originalPrice: Money::cents(10000),
            customer: Customer::regular(),
            quantity: 15
        );

        $result = $vipHandler->apply($request);

        self::assertTrue($result->hasDiscount());
        self::assertStringContainsString('Bulk', $result->reason());
    }

    public function testNoDiscountWhenNoConditionMet(): void
    {
        $vipHandler = new VipDiscountHandler();
        $bulkHandler = new BulkDiscountHandler();

        $vipHandler->setNext($bulkHandler);

        $request = new DiscountRequest(
            originalPrice: Money::cents(10000),
            customer: Customer::regular(),
            quantity: 2
        );

        $result = $vipHandler->apply($request);

        self::assertFalse($result->hasDiscount());
    }
}
```
