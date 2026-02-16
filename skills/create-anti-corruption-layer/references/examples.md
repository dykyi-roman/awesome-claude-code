# Anti-Corruption Layer Examples

## Payment Gateway ACL (Stripe)

### Domain Port

**File:** `src/Domain/Payment/Port/PaymentGatewayPortInterface.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Payment\Port;

use Domain\Payment\Entity\Payment;
use Domain\Payment\ValueObject\PaymentId;
use Domain\Payment\ValueObject\Money;

interface PaymentGatewayPortInterface
{
    public function charge(Payment $payment): PaymentId;

    public function refund(PaymentId $paymentId, Money $amount): void;

    public function getStatus(PaymentId $paymentId): PaymentStatus;
}
```

---

### External DTO (Stripe format)

**File:** `src/Infrastructure/Payment/ACL/Stripe/DTO/StripeChargeDTO.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Payment\ACL\Stripe\DTO;

final readonly class StripeChargeDTO
{
    public function __construct(
        public ?string $id,
        public int $amount,
        public string $currency,
        public string $customerId,
        public string $status,
        public ?string $failureCode,
        public ?string $failureMessage,
        public array $metadata,
    ) {}

    public static function fromArray(array $data): self
    {
        return new self(
            id: $data['id'] ?? null,
            amount: $data['amount'],
            currency: $data['currency'],
            customerId: $data['customer'],
            status: $data['status'],
            failureCode: $data['failure_code'] ?? null,
            failureMessage: $data['failure_message'] ?? null,
            metadata: $data['metadata'] ?? [],
        );
    }

    public static function forCharge(
        int $amountInCents,
        string $currency,
        string $customerId,
        array $metadata = []
    ): self {
        return new self(
            id: null,
            amount: $amountInCents,
            currency: strtolower($currency),
            customerId: $customerId,
            status: 'pending',
            failureCode: null,
            failureMessage: null,
            metadata: $metadata,
        );
    }

    public function toArray(): array
    {
        return array_filter([
            'amount' => $this->amount,
            'currency' => $this->currency,
            'customer' => $this->customerId,
            'metadata' => $this->metadata,
        ]);
    }
}
```

---

### Translator

**File:** `src/Infrastructure/Payment/ACL/Stripe/StripeTranslator.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Payment\ACL\Stripe;

use Domain\Payment\Entity\Payment;
use Domain\Payment\ValueObject\Money;
use Domain\Payment\ValueObject\PaymentId;
use Domain\Payment\ValueObject\PaymentStatus;
use Domain\Payment\ValueObject\CustomerId;
use Infrastructure\Payment\ACL\Stripe\DTO\StripeChargeDTO;

final readonly class StripeTranslator
{
    public function toStripeCharge(Payment $payment): StripeChargeDTO
    {
        return StripeChargeDTO::forCharge(
            amountInCents: $this->moneyToCents($payment->amount()),
            currency: $payment->amount()->currency()->value,
            customerId: $this->toStripeCustomerId($payment->customerId()),
            metadata: [
                'payment_id' => $payment->id()->toString(),
                'order_id' => $payment->orderId()?->toString(),
            ],
        );
    }

    public function toPaymentId(StripeChargeDTO $dto): PaymentId
    {
        return PaymentId::fromString($dto->id);
    }

    public function toPaymentStatus(StripeChargeDTO $dto): PaymentStatus
    {
        return match ($dto->status) {
            'succeeded' => PaymentStatus::Completed,
            'pending', 'processing' => PaymentStatus::Pending,
            'failed' => PaymentStatus::Failed,
            'canceled' => PaymentStatus::Cancelled,
            default => PaymentStatus::Unknown,
        };
    }

    public function toMoney(int $cents, string $currency): Money
    {
        return new Money(
            amount: $cents / 100,
            currency: Currency::from(strtoupper($currency))
        );
    }

    private function moneyToCents(Money $money): int
    {
        return (int) ($money->amount() * 100);
    }

    private function toStripeCustomerId(CustomerId $customerId): string
    {
        return 'cus_' . $customerId->toString();
    }
}
```

---

### Facade

**File:** `src/Infrastructure/Payment/ACL/Stripe/StripeFacade.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Payment\ACL\Stripe;

use Infrastructure\Payment\ACL\Stripe\DTO\StripeChargeDTO;
use Infrastructure\Payment\ACL\Stripe\DTO\StripeRefundDTO;
use Infrastructure\Payment\ACL\Stripe\Exception\StripeConnectionException;
use Stripe\StripeClient;
use Stripe\Exception\ApiErrorException;

final readonly class StripeFacade
{
    public function __construct(
        private StripeClient $client,
    ) {}

    /**
     * @throws StripeConnectionException
     */
    public function createCharge(StripeChargeDTO $dto): StripeChargeDTO
    {
        try {
            $charge = $this->client->charges->create($dto->toArray());

            return StripeChargeDTO::fromArray($charge->toArray());
        } catch (ApiErrorException $e) {
            throw new StripeConnectionException(
                "Stripe charge failed: {$e->getMessage()}",
                $e->getCode(),
                $e
            );
        }
    }

    /**
     * @throws StripeConnectionException
     */
    public function getCharge(string $chargeId): StripeChargeDTO
    {
        try {
            $charge = $this->client->charges->retrieve($chargeId);

            return StripeChargeDTO::fromArray($charge->toArray());
        } catch (ApiErrorException $e) {
            throw new StripeConnectionException(
                "Failed to retrieve charge: {$e->getMessage()}",
                $e->getCode(),
                $e
            );
        }
    }

    /**
     * @throws StripeConnectionException
     */
    public function createRefund(string $chargeId, int $amountInCents): StripeRefundDTO
    {
        try {
            $refund = $this->client->refunds->create([
                'charge' => $chargeId,
                'amount' => $amountInCents,
            ]);

            return StripeRefundDTO::fromArray($refund->toArray());
        } catch (ApiErrorException $e) {
            throw new StripeConnectionException(
                "Stripe refund failed: {$e->getMessage()}",
                $e->getCode(),
                $e
            );
        }
    }
}
```

---

### Adapter

**File:** `src/Infrastructure/Payment/ACL/Stripe/StripeAdapter.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Payment\ACL\Stripe;

use Domain\Payment\Entity\Payment;
use Domain\Payment\Port\PaymentGatewayPortInterface;
use Domain\Payment\ValueObject\Money;
use Domain\Payment\ValueObject\PaymentId;
use Domain\Payment\ValueObject\PaymentStatus;
use Domain\Payment\Exception\PaymentException;
use Infrastructure\Payment\ACL\Stripe\Exception\StripeConnectionException;

final readonly class StripeAdapter implements PaymentGatewayPortInterface
{
    public function __construct(
        private StripeFacade $facade,
        private StripeTranslator $translator,
    ) {}

    public function charge(Payment $payment): PaymentId
    {
        $stripeCharge = $this->translator->toStripeCharge($payment);

        try {
            $result = $this->facade->createCharge($stripeCharge);

            return $this->translator->toPaymentId($result);
        } catch (StripeConnectionException $e) {
            throw new PaymentException(
                "Payment charge failed: {$e->getMessage()}",
                previous: $e
            );
        }
    }

    public function refund(PaymentId $paymentId, Money $amount): void
    {
        $amountInCents = (int) ($amount->amount() * 100);

        try {
            $this->facade->createRefund($paymentId->toString(), $amountInCents);
        } catch (StripeConnectionException $e) {
            throw new PaymentException(
                "Payment refund failed: {$e->getMessage()}",
                previous: $e
            );
        }
    }

    public function getStatus(PaymentId $paymentId): PaymentStatus
    {
        try {
            $charge = $this->facade->getCharge($paymentId->toString());

            return $this->translator->toPaymentStatus($charge);
        } catch (StripeConnectionException $e) {
            throw new PaymentException(
                "Failed to get payment status: {$e->getMessage()}",
                previous: $e
            );
        }
    }
}
```

---

## Unit Tests

### TranslatorTest

**File:** `tests/Unit/Infrastructure/Payment/ACL/Stripe/StripeTranslatorTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Infrastructure\Payment\ACL\Stripe;

use Infrastructure\Payment\ACL\Stripe\StripeTranslator;
use Infrastructure\Payment\ACL\Stripe\DTO\StripeChargeDTO;
use Domain\Payment\Entity\Payment;
use Domain\Payment\ValueObject\PaymentId;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(StripeTranslator::class)]
final class StripeTranslatorTest extends TestCase
{
    private StripeTranslator $translator;

    protected function setUp(): void
    {
        $this->translator = new StripeTranslator();
    }

    public function testTranslatesToStripeCharge(): void
    {
        $payment = $this->createPayment(amount: 100.00);

        $dto = $this->translator->toStripeCharge($payment);

        self::assertSame(10000, $dto->amount);
        self::assertSame('usd', $dto->currency);
    }

    public function testTranslatesToPaymentStatus(): void
    {
        $dto = new StripeChargeDTO(
            id: 'ch_123',
            amount: 10000,
            currency: 'usd',
            customerId: 'cus_123',
            status: 'succeeded',
            failureCode: null,
            failureMessage: null,
            metadata: [],
        );

        $status = $this->translator->toPaymentStatus($dto);

        self::assertSame(PaymentStatus::Completed, $status);
    }

    public function testHandlesFailedStatus(): void
    {
        $dto = new StripeChargeDTO(
            id: 'ch_123',
            amount: 10000,
            currency: 'usd',
            customerId: 'cus_123',
            status: 'failed',
            failureCode: 'card_declined',
            failureMessage: 'Card declined',
            metadata: [],
        );

        $status = $this->translator->toPaymentStatus($dto);

        self::assertSame(PaymentStatus::Failed, $status);
    }

    private function createPayment(float $amount): Payment
    {
        return new Payment(
            id: PaymentId::generate(),
            amount: Money::usd($amount),
            customerId: CustomerId::generate()
        );
    }
}
```

---

### AdapterTest

**File:** `tests/Unit/Infrastructure/Payment/ACL/Stripe/StripeAdapterTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Infrastructure\Payment\ACL\Stripe;

use Infrastructure\Payment\ACL\Stripe\StripeAdapter;
use Infrastructure\Payment\ACL\Stripe\StripeFacade;
use Infrastructure\Payment\ACL\Stripe\StripeTranslator;
use Infrastructure\Payment\ACL\Stripe\DTO\StripeChargeDTO;
use Domain\Payment\Entity\Payment;
use Domain\Payment\ValueObject\PaymentId;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(StripeAdapter::class)]
final class StripeAdapterTest extends TestCase
{
    private StripeFacade $facade;
    private StripeTranslator $translator;
    private StripeAdapter $adapter;

    protected function setUp(): void
    {
        $this->facade = $this->createMock(StripeFacade::class);
        $this->translator = new StripeTranslator();
        $this->adapter = new StripeAdapter($this->facade, $this->translator);
    }

    public function testChargesPayment(): void
    {
        $payment = $this->createPayment();

        $resultDto = new StripeChargeDTO(
            id: 'ch_stripe_123',
            amount: 10000,
            currency: 'usd',
            customerId: 'cus_123',
            status: 'succeeded',
            failureCode: null,
            failureMessage: null,
            metadata: [],
        );

        $this->facade
            ->expects(self::once())
            ->method('createCharge')
            ->willReturn($resultDto);

        $paymentId = $this->adapter->charge($payment);

        self::assertSame('ch_stripe_123', $paymentId->toString());
    }

    public function testGetsPaymentStatus(): void
    {
        $dto = new StripeChargeDTO(
            id: 'ch_123',
            amount: 10000,
            currency: 'usd',
            customerId: 'cus_123',
            status: 'succeeded',
            failureCode: null,
            failureMessage: null,
            metadata: [],
        );

        $this->facade
            ->expects(self::once())
            ->method('getCharge')
            ->with('ch_123')
            ->willReturn($dto);

        $status = $this->adapter->getStatus(PaymentId::fromString('ch_123'));

        self::assertSame(PaymentStatus::Completed, $status);
    }

    private function createPayment(): Payment
    {
        return new Payment(
            id: PaymentId::generate(),
            amount: Money::usd(100.00),
            customerId: CustomerId::generate()
        );
    }
}
```

---

## DI Configuration

```yaml
# services.yaml
Domain\Payment\Port\PaymentGatewayPortInterface:
    alias: Infrastructure\Payment\ACL\Stripe\StripeAdapter

Infrastructure\Payment\ACL\Stripe\StripeFacade:
    arguments:
        $client: '@stripe.client'

Infrastructure\Payment\ACL\Stripe\StripeAdapter:
    arguments:
        $facade: '@Infrastructure\Payment\ACL\Stripe\StripeFacade'
        $translator: '@Infrastructure\Payment\ACL\Stripe\StripeTranslator'
```
