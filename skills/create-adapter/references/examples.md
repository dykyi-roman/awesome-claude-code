# Adapter Pattern Examples

## PayPal Payment Gateway Adapter

**File:** `src/Infrastructure/Payment/Adapter/PayPalPaymentGatewayAdapter.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Payment\Adapter;

use Domain\Payment\Exception\PaymentException;
use Domain\Payment\PaymentGatewayInterface;
use Domain\Payment\PaymentStatus;
use Domain\Payment\ValueObject\Amount;
use Domain\Payment\ValueObject\PaymentToken;
use Domain\Payment\ValueObject\TransactionId;
use PayPalCheckoutSdk\Core\PayPalHttpClient;
use PayPalCheckoutSdk\Orders\OrdersCaptureRequest;
use PayPalCheckoutSdk\Orders\OrdersCreateRequest;
use PayPalCheckoutSdk\Orders\OrdersGetRequest;
use PayPalCheckoutSdk\Payments\CapturesRefundRequest;

final readonly class PayPalPaymentGatewayAdapter implements PaymentGatewayInterface
{
    public function __construct(
        private PayPalHttpClient $client
    ) {}

    public function charge(Amount $amount, PaymentToken $token): TransactionId
    {
        try {
            $request = new OrdersCreateRequest();
            $request->prefer('return=representation');
            $request->body = [
                'intent' => 'CAPTURE',
                'purchase_units' => [[
                    'amount' => [
                        'currency_code' => $amount->currency()->code(),
                        'value' => $amount->toString(),
                    ],
                ]],
                'payment_source' => [
                    'token' => [
                        'id' => $token->value(),
                        'type' => 'BILLING_AGREEMENT',
                    ],
                ],
            ];

            $response = $this->client->execute($request);

            $captureRequest = new OrdersCaptureRequest($response->result->id);
            $captureResponse = $this->client->execute($captureRequest);

            return new TransactionId($captureResponse->result->id);
        } catch (\Exception $e) {
            throw new PaymentException(
                message: 'PayPal charge failed: ' . $e->getMessage(),
                previous: $e
            );
        }
    }

    public function refund(TransactionId $transactionId, Amount $amount): void
    {
        try {
            $request = new CapturesRefundRequest($transactionId->value());
            $request->body = [
                'amount' => [
                    'value' => $amount->toString(),
                    'currency_code' => $amount->currency()->code(),
                ],
            ];

            $this->client->execute($request);
        } catch (\Exception $e) {
            throw new PaymentException(
                message: 'PayPal refund failed: ' . $e->getMessage(),
                previous: $e
            );
        }
    }

    public function getStatus(TransactionId $transactionId): PaymentStatus
    {
        try {
            $request = new OrdersGetRequest($transactionId->value());
            $response = $this->client->execute($request);

            return match ($response->result->status) {
                'COMPLETED' => PaymentStatus::Completed,
                'APPROVED' => PaymentStatus::Pending,
                'VOIDED', 'CANCELLED' => PaymentStatus::Failed,
                default => PaymentStatus::Unknown,
            };
        } catch (\Exception $e) {
            throw new PaymentException(
                message: 'Failed to retrieve PayPal status: ' . $e->getMessage(),
                previous: $e
            );
        }
    }
}
```

---

## Legacy User Repository Adapter

**File:** `src/Infrastructure/User/Adapter/LegacyUserRepositoryAdapter.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\User\Adapter;

use Domain\User\Entity\User;
use Domain\User\Exception\UserNotFoundException;
use Domain\User\Repository\UserRepositoryInterface;
use Domain\User\ValueObject\Email;
use Domain\User\ValueObject\UserId;
use Legacy\Database\UserModel;

final readonly class LegacyUserRepositoryAdapter implements UserRepositoryInterface
{
    public function __construct(
        private UserModel $legacyModel
    ) {}

    public function findById(UserId $id): User
    {
        $legacyUser = $this->legacyModel->find($id->toInt());

        if ($legacyUser === null) {
            throw new UserNotFoundException($id);
        }

        return $this->convertToDomain($legacyUser);
    }

    public function findByEmail(Email $email): ?User
    {
        $legacyUser = $this->legacyModel->findByEmail($email->value());

        if ($legacyUser === null) {
            return null;
        }

        return $this->convertToDomain($legacyUser);
    }

    public function save(User $user): void
    {
        $data = [
            'email' => $user->email()->value(),
            'name' => $user->name(),
            'created_at' => $user->createdAt()->format('Y-m-d H:i:s'),
        ];

        if ($user->id()->isEmpty()) {
            $this->legacyModel->insert($data);
        } else {
            $this->legacyModel->update($user->id()->toInt(), $data);
        }
    }

    public function delete(UserId $id): void
    {
        $this->legacyModel->delete($id->toInt());
    }

    private function convertToDomain(array $legacyUser): User
    {
        return new User(
            id: new UserId($legacyUser['id']),
            email: new Email($legacyUser['email']),
            name: $legacyUser['name'],
            createdAt: new \DateTimeImmutable($legacyUser['created_at'])
        );
    }
}
```

---

## Slack Messenger Adapter

**File:** `src/Infrastructure/Notification/Adapter/SlackMessengerAdapter.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Notification\Adapter;

use Domain\Notification\Exception\NotificationException;
use Domain\Notification\MessengerInterface;
use Domain\Notification\ValueObject\Channel;
use Domain\Notification\ValueObject\Message;
use GuzzleHttp\ClientInterface;
use GuzzleHttp\Exception\GuzzleException;

final readonly class SlackMessengerAdapter implements MessengerInterface
{
    public function __construct(
        private ClientInterface $httpClient,
        private string $webhookUrl
    ) {}

    public function send(Channel $channel, Message $message): void
    {
        try {
            $payload = [
                'channel' => $channel->value(),
                'text' => $message->text(),
                'username' => $message->sender(),
                'icon_emoji' => ':robot_face:',
            ];

            if ($message->hasAttachments()) {
                $payload['attachments'] = $this->convertAttachments($message);
            }

            $this->httpClient->request('POST', $this->webhookUrl, [
                'json' => $payload,
            ]);
        } catch (GuzzleException $e) {
            throw new NotificationException(
                message: 'Failed to send Slack message: ' . $e->getMessage(),
                previous: $e
            );
        }
    }

    private function convertAttachments(Message $message): array
    {
        $attachments = [];

        foreach ($message->attachments() as $attachment) {
            $attachments[] = [
                'title' => $attachment->title(),
                'text' => $attachment->content(),
                'color' => $this->mapPriorityToColor($attachment->priority()),
            ];
        }

        return $attachments;
    }

    private function mapPriorityToColor(string $priority): string
    {
        return match ($priority) {
            'high' => 'danger',
            'medium' => 'warning',
            'low' => 'good',
            default => '#cccccc',
        };
    }
}
```

---

## Redis Cache Adapter

**File:** `src/Infrastructure/Cache/Adapter/RedisCacheAdapter.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Cache\Adapter;

use Domain\Cache\CacheInterface;
use Domain\Cache\Exception\CacheException;
use Redis;

final readonly class RedisCacheAdapter implements CacheInterface
{
    private const DEFAULT_TTL = 3600;

    public function __construct(
        private Redis $redis
    ) {}

    public function get(string $key): mixed
    {
        $value = $this->redis->get($key);

        if ($value === false) {
            return null;
        }

        return unserialize($value);
    }

    public function set(string $key, mixed $value, ?int $ttl = null): void
    {
        $serialized = serialize($value);
        $ttl = $ttl ?? self::DEFAULT_TTL;

        $result = $this->redis->setex($key, $ttl, $serialized);

        if ($result === false) {
            throw new CacheException("Failed to set cache key: {$key}");
        }
    }

    public function delete(string $key): void
    {
        $this->redis->del($key);
    }

    public function has(string $key): bool
    {
        return $this->redis->exists($key) > 0;
    }

    public function clear(): void
    {
        $this->redis->flushDB();
    }
}
```

---

## Unit Tests

### StripePaymentGatewayAdapterTest

**File:** `tests/Unit/Infrastructure/Payment/Adapter/StripePaymentGatewayAdapterTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Infrastructure\Payment\Adapter;

use Domain\Payment\Exception\PaymentException;
use Domain\Payment\PaymentStatus;
use Domain\Payment\ValueObject\Amount;
use Domain\Payment\ValueObject\Currency;
use Domain\Payment\ValueObject\PaymentToken;
use Domain\Payment\ValueObject\TransactionId;
use Infrastructure\Payment\Adapter\StripePaymentGatewayAdapter;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;
use Stripe\Charge;
use Stripe\Service\ChargeService;
use Stripe\Service\RefundService;
use Stripe\StripeClient;

#[Group('unit')]
#[CoversClass(StripePaymentGatewayAdapter::class)]
final class StripePaymentGatewayAdapterTest extends TestCase
{
    public function testChargeSuccessfully(): void
    {
        $stripeClient = $this->createMock(StripeClient::class);
        $chargeService = $this->createMock(ChargeService::class);

        $charge = new Charge('ch_test_123');
        $charge->id = 'ch_test_123';

        $chargeService->expects($this->once())
            ->method('create')
            ->with([
                'amount' => 10000,
                'currency' => 'USD',
                'source' => 'tok_visa',
            ])
            ->willReturn($charge);

        $stripeClient->charges = $chargeService;

        $adapter = new StripePaymentGatewayAdapter($stripeClient);

        $amount = new Amount(100.00, new Currency('USD'));
        $token = new PaymentToken('tok_visa');

        $transactionId = $adapter->charge($amount, $token);

        self::assertInstanceOf(TransactionId::class, $transactionId);
        self::assertSame('ch_test_123', $transactionId->value());
    }

    public function testChargeThrowsExceptionOnFailure(): void
    {
        $stripeClient = $this->createMock(StripeClient::class);
        $chargeService = $this->createMock(ChargeService::class);

        $chargeService->expects($this->once())
            ->method('create')
            ->willThrowException(new \Stripe\Exception\CardException('Card declined'));

        $stripeClient->charges = $chargeService;

        $adapter = new StripePaymentGatewayAdapter($stripeClient);

        $amount = new Amount(100.00, new Currency('USD'));
        $token = new PaymentToken('tok_visa');

        $this->expectException(PaymentException::class);
        $this->expectExceptionMessage('Payment charge failed');

        $adapter->charge($amount, $token);
    }

    public function testRefundSuccessfully(): void
    {
        $stripeClient = $this->createMock(StripeClient::class);
        $refundService = $this->createMock(RefundService::class);

        $refundService->expects($this->once())
            ->method('create')
            ->with([
                'charge' => 'ch_test_123',
                'amount' => 5000,
            ]);

        $stripeClient->refunds = $refundService;

        $adapter = new StripePaymentGatewayAdapter($stripeClient);

        $transactionId = new TransactionId('ch_test_123');
        $amount = new Amount(50.00, new Currency('USD'));

        $adapter->refund($transactionId, $amount);

        $this->expectNotToPerformAssertions();
    }

    public function testGetStatusReturnsCompleted(): void
    {
        $stripeClient = $this->createMock(StripeClient::class);
        $chargeService = $this->createMock(ChargeService::class);

        $charge = new Charge('ch_test_123');
        $charge->status = 'succeeded';

        $chargeService->expects($this->once())
            ->method('retrieve')
            ->with('ch_test_123')
            ->willReturn($charge);

        $stripeClient->charges = $chargeService;

        $adapter = new StripePaymentGatewayAdapter($stripeClient);

        $transactionId = new TransactionId('ch_test_123');

        $status = $adapter->getStatus($transactionId);

        self::assertSame(PaymentStatus::Completed, $status);
    }
}
```

---

### LegacyUserRepositoryAdapterTest

**File:** `tests/Unit/Infrastructure/User/Adapter/LegacyUserRepositoryAdapterTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Infrastructure\User\Adapter;

use Domain\User\Entity\User;
use Domain\User\Exception\UserNotFoundException;
use Domain\User\ValueObject\Email;
use Domain\User\ValueObject\UserId;
use Infrastructure\User\Adapter\LegacyUserRepositoryAdapter;
use Legacy\Database\UserModel;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(LegacyUserRepositoryAdapter::class)]
final class LegacyUserRepositoryAdapterTest extends TestCase
{
    public function testFindByIdReturnsUser(): void
    {
        $legacyModel = $this->createMock(UserModel::class);

        $legacyData = [
            'id' => 1,
            'email' => 'user@example.com',
            'name' => 'John Doe',
            'created_at' => '2025-01-01 10:00:00',
        ];

        $legacyModel->expects($this->once())
            ->method('find')
            ->with(1)
            ->willReturn($legacyData);

        $adapter = new LegacyUserRepositoryAdapter($legacyModel);

        $user = $adapter->findById(new UserId(1));

        self::assertInstanceOf(User::class, $user);
        self::assertSame('user@example.com', $user->email()->value());
        self::assertSame('John Doe', $user->name());
    }

    public function testFindByIdThrowsNotFoundException(): void
    {
        $legacyModel = $this->createMock(UserModel::class);

        $legacyModel->expects($this->once())
            ->method('find')
            ->with(999)
            ->willReturn(null);

        $adapter = new LegacyUserRepositoryAdapter($legacyModel);

        $this->expectException(UserNotFoundException::class);

        $adapter->findById(new UserId(999));
    }

    public function testSaveInsertsNewUser(): void
    {
        $legacyModel = $this->createMock(UserModel::class);

        $user = new User(
            id: UserId::empty(),
            email: new Email('new@example.com'),
            name: 'Jane Smith',
            createdAt: new \DateTimeImmutable('2025-01-15 15:00:00')
        );

        $legacyModel->expects($this->once())
            ->method('insert')
            ->with([
                'email' => 'new@example.com',
                'name' => 'Jane Smith',
                'created_at' => '2025-01-15 15:00:00',
            ]);

        $adapter = new LegacyUserRepositoryAdapter($legacyModel);

        $adapter->save($user);

        $this->expectNotToPerformAssertions();
    }

    public function testSaveUpdatesExistingUser(): void
    {
        $legacyModel = $this->createMock(UserModel::class);

        $user = new User(
            id: new UserId(5),
            email: new Email('existing@example.com'),
            name: 'Updated Name',
            createdAt: new \DateTimeImmutable('2025-01-10 12:00:00')
        );

        $legacyModel->expects($this->once())
            ->method('update')
            ->with(5, [
                'email' => 'existing@example.com',
                'name' => 'Updated Name',
                'created_at' => '2025-01-10 12:00:00',
            ]);

        $adapter = new LegacyUserRepositoryAdapter($legacyModel);

        $adapter->save($user);

        $this->expectNotToPerformAssertions();
    }
}
```
