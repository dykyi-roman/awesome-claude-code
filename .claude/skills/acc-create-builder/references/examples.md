# Builder Pattern Examples

## Order Builder

**File:** `src/Domain/Order/Builder/OrderBuilderInterface.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Order\Builder;

use Domain\Order\Entity\Order;
use Domain\Order\ValueObject\CustomerId;
use Domain\Order\ValueObject\Address;
use Domain\Order\ValueObject\OrderItem;

interface OrderBuilderInterface
{
    public function forCustomer(CustomerId $customerId): self;

    public function withShippingAddress(Address $address): self;

    public function withBillingAddress(Address $address): self;

    public function addItem(OrderItem $item): self;

    public function withNote(string $note): self;

    public function withDiscountCode(string $code): self;

    public function build(): Order;

    public function reset(): self;
}
```

**File:** `src/Domain/Order/Builder/OrderBuilder.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Order\Builder;

use Domain\Order\Entity\Order;
use Domain\Order\ValueObject\Address;
use Domain\Order\ValueObject\CustomerId;
use Domain\Order\ValueObject\OrderId;
use Domain\Order\ValueObject\OrderItem;

final class OrderBuilder implements OrderBuilderInterface
{
    private ?CustomerId $customerId = null;
    private ?Address $shippingAddress = null;
    private ?Address $billingAddress = null;
    /** @var array<OrderItem> */
    private array $items = [];
    private ?string $note = null;
    private ?string $discountCode = null;

    public function forCustomer(CustomerId $customerId): self
    {
        $this->customerId = $customerId;
        return $this;
    }

    public function withShippingAddress(Address $address): self
    {
        $this->shippingAddress = $address;
        return $this;
    }

    public function withBillingAddress(Address $address): self
    {
        $this->billingAddress = $address;
        return $this;
    }

    public function addItem(OrderItem $item): self
    {
        $this->items[] = $item;
        return $this;
    }

    public function withNote(string $note): self
    {
        $this->note = $note;
        return $this;
    }

    public function withDiscountCode(string $code): self
    {
        $this->discountCode = $code;
        return $this;
    }

    public function build(): Order
    {
        $errors = $this->validate();

        if ($errors !== []) {
            throw new BuilderValidationException($errors);
        }

        $billingAddress = $this->billingAddress ?? $this->shippingAddress;

        return new Order(
            id: OrderId::generate(),
            customerId: $this->customerId,
            shippingAddress: $this->shippingAddress,
            billingAddress: $billingAddress,
            items: $this->items,
            note: $this->note,
            discountCode: $this->discountCode,
            createdAt: new \DateTimeImmutable()
        );
    }

    public function reset(): self
    {
        $this->customerId = null;
        $this->shippingAddress = null;
        $this->billingAddress = null;
        $this->items = [];
        $this->note = null;
        $this->discountCode = null;
        return $this;
    }

    /**
     * @return array<string>
     */
    private function validate(): array
    {
        $errors = [];

        if ($this->customerId === null) {
            $errors[] = 'Customer ID is required';
        }

        if ($this->shippingAddress === null) {
            $errors[] = 'Shipping address is required';
        }

        if ($this->items === []) {
            $errors[] = 'At least one item is required';
        }

        return $errors;
    }
}
```

---

## Email Builder

**File:** `src/Domain/Notification/Builder/EmailBuilder.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Notification\Builder;

use Domain\Notification\ValueObject\Email;
use Domain\Notification\ValueObject\EmailMessage;

final class EmailBuilder
{
    private ?string $to = null;
    private ?string $from = null;
    private ?string $subject = null;
    private ?string $body = null;
    private ?string $htmlBody = null;
    private array $cc = [];
    private array $bcc = [];
    private array $attachments = [];
    private array $headers = [];

    public function to(string $email): self
    {
        $this->to = $email;
        return $this;
    }

    public function from(string $email): self
    {
        $this->from = $email;
        return $this;
    }

    public function subject(string $subject): self
    {
        $this->subject = $subject;
        return $this;
    }

    public function body(string $body): self
    {
        $this->body = $body;
        return $this;
    }

    public function htmlBody(string $html): self
    {
        $this->htmlBody = $html;
        return $this;
    }

    public function cc(string ...$emails): self
    {
        $this->cc = array_merge($this->cc, $emails);
        return $this;
    }

    public function bcc(string ...$emails): self
    {
        $this->bcc = array_merge($this->bcc, $emails);
        return $this;
    }

    public function attach(string $path, ?string $name = null): self
    {
        $this->attachments[] = ['path' => $path, 'name' => $name ?? basename($path)];
        return $this;
    }

    public function header(string $name, string $value): self
    {
        $this->headers[$name] = $value;
        return $this;
    }

    public function build(): EmailMessage
    {
        $this->validate();

        return new EmailMessage(
            to: Email::fromString($this->to),
            from: Email::fromString($this->from),
            subject: $this->subject,
            body: $this->body ?? '',
            htmlBody: $this->htmlBody,
            cc: array_map(fn($e) => Email::fromString($e), $this->cc),
            bcc: array_map(fn($e) => Email::fromString($e), $this->bcc),
            attachments: $this->attachments,
            headers: $this->headers
        );
    }

    private function validate(): void
    {
        $errors = [];

        if ($this->to === null) {
            $errors[] = 'Recipient (to) is required';
        }

        if ($this->from === null) {
            $errors[] = 'Sender (from) is required';
        }

        if ($this->subject === null) {
            $errors[] = 'Subject is required';
        }

        if ($this->body === null && $this->htmlBody === null) {
            $errors[] = 'Either body or htmlBody is required';
        }

        if ($errors !== []) {
            throw new BuilderValidationException($errors);
        }
    }
}
```

---

## Director Example

**File:** `src/Domain/Order/Builder/OrderDirector.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Order\Builder;

use Domain\Order\Entity\Order;
use Domain\Order\ValueObject\CustomerId;

final readonly class OrderDirector
{
    public function __construct(
        private OrderBuilderInterface $builder
    ) {}

    public function buildMinimalOrder(
        CustomerId $customerId,
        Address $address,
        OrderItem $item
    ): Order {
        return $this->builder
            ->reset()
            ->forCustomer($customerId)
            ->withShippingAddress($address)
            ->addItem($item)
            ->build();
    }

    public function buildGiftOrder(
        CustomerId $customerId,
        Address $shippingAddress,
        Address $billingAddress,
        array $items,
        string $giftMessage
    ): Order {
        $builder = $this->builder
            ->reset()
            ->forCustomer($customerId)
            ->withShippingAddress($shippingAddress)
            ->withBillingAddress($billingAddress)
            ->withNote('GIFT: ' . $giftMessage);

        foreach ($items as $item) {
            $builder->addItem($item);
        }

        return $builder->build();
    }

    public function buildBulkOrder(
        CustomerId $customerId,
        Address $address,
        array $items,
        string $discountCode
    ): Order {
        $builder = $this->builder
            ->reset()
            ->forCustomer($customerId)
            ->withShippingAddress($address)
            ->withDiscountCode($discountCode);

        foreach ($items as $item) {
            $builder->addItem($item);
        }

        return $builder->build();
    }
}
```

---

## Unit Tests

### Order Builder Test

**File:** `tests/Unit/Domain/Order/Builder/OrderBuilderTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\Order\Builder;

use Domain\Order\Builder\BuilderValidationException;
use Domain\Order\Builder\OrderBuilder;
use Domain\Order\Entity\Order;
use Domain\Order\ValueObject\Address;
use Domain\Order\ValueObject\CustomerId;
use Domain\Order\ValueObject\OrderItem;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(OrderBuilder::class)]
final class OrderBuilderTest extends TestCase
{
    private OrderBuilder $builder;

    protected function setUp(): void
    {
        $this->builder = new OrderBuilder();
    }

    public function testBuildsCompleteOrder(): void
    {
        $order = $this->builder
            ->forCustomer(CustomerId::generate())
            ->withShippingAddress($this->createAddress())
            ->addItem($this->createItem())
            ->build();

        self::assertInstanceOf(Order::class, $order);
    }

    public function testBuildsOrderWithAllOptions(): void
    {
        $customerId = CustomerId::generate();
        $shippingAddress = $this->createAddress();
        $billingAddress = $this->createAddress('Billing');

        $order = $this->builder
            ->forCustomer($customerId)
            ->withShippingAddress($shippingAddress)
            ->withBillingAddress($billingAddress)
            ->addItem($this->createItem())
            ->addItem($this->createItem())
            ->withNote('Please deliver after 5pm')
            ->withDiscountCode('SAVE10')
            ->build();

        self::assertSame($customerId, $order->customerId());
        self::assertCount(2, $order->items());
    }

    public function testUsesShippingAsBillingWhenNotProvided(): void
    {
        $shippingAddress = $this->createAddress();

        $order = $this->builder
            ->forCustomer(CustomerId::generate())
            ->withShippingAddress($shippingAddress)
            ->addItem($this->createItem())
            ->build();

        self::assertSame($shippingAddress, $order->billingAddress());
    }

    public function testThrowsOnMissingCustomer(): void
    {
        $this->expectException(BuilderValidationException::class);

        $this->builder
            ->withShippingAddress($this->createAddress())
            ->addItem($this->createItem())
            ->build();
    }

    public function testThrowsOnMissingAddress(): void
    {
        $this->expectException(BuilderValidationException::class);

        $this->builder
            ->forCustomer(CustomerId::generate())
            ->addItem($this->createItem())
            ->build();
    }

    public function testThrowsOnEmptyItems(): void
    {
        $this->expectException(BuilderValidationException::class);

        $this->builder
            ->forCustomer(CustomerId::generate())
            ->withShippingAddress($this->createAddress())
            ->build();
    }

    public function testResetClearsState(): void
    {
        $this->builder
            ->forCustomer(CustomerId::generate())
            ->withShippingAddress($this->createAddress())
            ->reset();

        $this->expectException(BuilderValidationException::class);

        $this->builder->build();
    }

    public function testFluentInterface(): void
    {
        $result = $this->builder->forCustomer(CustomerId::generate());

        self::assertSame($this->builder, $result);
    }

    private function createAddress(string $street = 'Main St'): Address
    {
        return new Address(
            street: $street,
            city: 'Test City',
            postalCode: '12345',
            country: 'US'
        );
    }

    private function createItem(): OrderItem
    {
        return new OrderItem(
            productId: ProductId::generate(),
            name: 'Test Product',
            price: Money::USD(1000),
            quantity: 1
        );
    }
}
```

### Email Builder Test

**File:** `tests/Unit/Domain/Notification/Builder/EmailBuilderTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\Notification\Builder;

use Domain\Notification\Builder\BuilderValidationException;
use Domain\Notification\Builder\EmailBuilder;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(EmailBuilder::class)]
final class EmailBuilderTest extends TestCase
{
    private EmailBuilder $builder;

    protected function setUp(): void
    {
        $this->builder = new EmailBuilder();
    }

    public function testBuildsMinimalEmail(): void
    {
        $email = $this->builder
            ->to('recipient@example.com')
            ->from('sender@example.com')
            ->subject('Test Subject')
            ->body('Test Body')
            ->build();

        self::assertSame('recipient@example.com', $email->to()->toString());
        self::assertSame('Test Subject', $email->subject());
    }

    public function testBuildsEmailWithAllOptions(): void
    {
        $email = $this->builder
            ->to('recipient@example.com')
            ->from('sender@example.com')
            ->subject('Test Subject')
            ->body('Plain text')
            ->htmlBody('<h1>HTML</h1>')
            ->cc('cc1@example.com', 'cc2@example.com')
            ->bcc('bcc@example.com')
            ->attach('/path/to/file.pdf')
            ->header('X-Priority', '1')
            ->build();

        self::assertCount(2, $email->cc());
        self::assertCount(1, $email->bcc());
        self::assertCount(1, $email->attachments());
    }

    public function testThrowsOnMissingRecipient(): void
    {
        $this->expectException(BuilderValidationException::class);

        $this->builder
            ->from('sender@example.com')
            ->subject('Test')
            ->body('Body')
            ->build();
    }

    public function testThrowsOnMissingBody(): void
    {
        $this->expectException(BuilderValidationException::class);

        $this->builder
            ->to('recipient@example.com')
            ->from('sender@example.com')
            ->subject('Test')
            ->build();
    }

    public function testAcceptsHtmlBodyWithoutPlainText(): void
    {
        $email = $this->builder
            ->to('recipient@example.com')
            ->from('sender@example.com')
            ->subject('Test')
            ->htmlBody('<h1>HTML Only</h1>')
            ->build();

        self::assertNotNull($email->htmlBody());
    }
}
```
