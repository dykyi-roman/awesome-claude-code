# Idempotency Patterns Reference

## Idempotency Key Generation

### UUIDv4 (Client-Generated)

The client generates a unique key per operation attempt and sends it via HTTP header. The server uses this key to detect duplicate requests.

```php
<?php

declare(strict_types=1);

namespace Domain\ValueObject;

final readonly class IdempotencyKey
{
    private function __construct(
        private string $value,
    ) {}

    public static function generate(): self
    {
        return new self(uuid_create(UUID_TYPE_RANDOM));
    }

    public static function fromString(string $value): self
    {
        if (!uuid_is_valid($value)) {
            throw new InvalidIdempotencyKeyException($value);
        }

        return new self($value);
    }

    public function toString(): string
    {
        return $this->value;
    }
}
```

### Composite Key Pattern

For operations where context matters, compose the key from meaningful parts:

| Pattern | Format | Example |
|---------|--------|---------|
| **Simple** | `UUIDv4` | `550e8400-e29b-41d4-a716-446655440000` |
| **Scoped** | `{client}:{operation}:{ref}` | `app-1:create-order:inv-2024-001` |
| **Hashed** | `SHA256({method}:{path}:{body})` | `a3f2c8...` |
| **Temporal** | `{user}:{action}:{date}` | `user-42:daily-report:2024-01-15` |

## Deduplication Store

### Redis-Based Deduplication

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Idempotency;

final readonly class RedisDeduplicationStore implements DeduplicationStoreInterface
{
    private const string KEY_PREFIX = 'idemp:';

    public function __construct(
        private \Redis $redis,
        private int $ttlSeconds = 86400,
    ) {}

    public function exists(string $key): bool
    {
        return $this->redis->exists(self::KEY_PREFIX . $key) > 0;
    }

    public function store(string $key, string $serializedResponse): void
    {
        $this->redis->setex(
            self::KEY_PREFIX . $key,
            $this->ttlSeconds,
            $serializedResponse,
        );
    }

    public function retrieve(string $key): ?string
    {
        $result = $this->redis->get(self::KEY_PREFIX . $key);

        return $result === false ? null : $result;
    }

    public function markInProgress(string $key, int $lockTtl = 30): bool
    {
        return $this->redis->set(
            self::KEY_PREFIX . $key . ':lock',
            'processing',
            ['NX', 'EX' => $lockTtl],
        ) === true;
    }

    public function clearInProgress(string $key): void
    {
        $this->redis->del(self::KEY_PREFIX . $key . ':lock');
    }
}
```

### Database-Based Deduplication

For durability when Redis is not suitable:

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Idempotency;

final readonly class DatabaseDeduplicationStore implements DeduplicationStoreInterface
{
    public function __construct(
        private \PDO $pdo,
    ) {}

    public function exists(string $key): bool
    {
        $stmt = $this->pdo->prepare(
            'SELECT 1 FROM idempotency_keys WHERE key_value = :key AND expires_at > NOW()',
        );
        $stmt->execute([':key' => $key]);

        return $stmt->fetchColumn() !== false;
    }

    public function store(string $key, string $serializedResponse): void
    {
        $stmt = $this->pdo->prepare(
            'INSERT INTO idempotency_keys (key_value, response_data, created_at, expires_at)
             VALUES (:key, :response, NOW(), DATE_ADD(NOW(), INTERVAL 24 HOUR))
             ON DUPLICATE KEY UPDATE response_data = :response2, expires_at = DATE_ADD(NOW(), INTERVAL 24 HOUR)',
        );
        $stmt->execute([
            ':key' => $key,
            ':response' => $serializedResponse,
            ':response2' => $serializedResponse,
        ]);
    }

    public function retrieve(string $key): ?string
    {
        $stmt = $this->pdo->prepare(
            'SELECT response_data FROM idempotency_keys WHERE key_value = :key AND expires_at > NOW()',
        );
        $stmt->execute([':key' => $key]);

        $result = $stmt->fetchColumn();

        return $result === false ? null : $result;
    }
}
```

## PSR-15 Middleware Implementation

### Full Idempotency Middleware

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Http\Middleware;

use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\MiddlewareInterface;
use Psr\Http\Server\RequestHandlerInterface;
use Psr\Log\LoggerInterface;

final readonly class IdempotencyMiddleware implements MiddlewareInterface
{
    private const string HEADER_NAME = 'Idempotency-Key';
    private const array IDEMPOTENT_METHODS = ['GET', 'HEAD', 'OPTIONS', 'DELETE', 'PUT'];

    public function __construct(
        private DeduplicationStoreInterface $store,
        private LoggerInterface $logger,
    ) {}

    public function process(
        ServerRequestInterface $request,
        RequestHandlerInterface $handler,
    ): ResponseInterface {
        if (in_array($request->getMethod(), self::IDEMPOTENT_METHODS, true)) {
            return $handler->handle($request);
        }

        $key = $request->getHeaderLine(self::HEADER_NAME);
        if ($key === '') {
            return $handler->handle($request);
        }

        $cached = $this->store->retrieve($key);
        if ($cached !== null) {
            $this->logger->info('Idempotency hit', ['key' => $key]);

            return unserialize($cached, ['allowed_classes' => true]);
        }

        if (!$this->store->markInProgress($key)) {
            $this->logger->warning('Concurrent idempotent request', ['key' => $key]);

            throw new ConcurrentRequestException($key);
        }

        try {
            $response = $handler->handle($request);
            $this->store->store($key, serialize($response));

            return $response;
        } finally {
            $this->store->clearInProgress($key);
        }
    }
}
```

## Delivery Guarantees

### At-Least-Once with Idempotency

| Step | Description | Failure Mode |
|------|-------------|--------------|
| 1. Produce message | Send to queue with idempotency key | Retry send |
| 2. Consume message | Worker picks up message | Message requeued if no ACK |
| 3. Check dedup store | Was this key processed before? | If yes, skip and ACK |
| 4. Process message | Execute business logic | On failure, message requeued |
| 5. Store result | Save to dedup store | On failure, reprocess is safe |
| 6. ACK message | Acknowledge to broker | If missed, requeue triggers step 3 |

### Exactly-Once Delivery (Transactional Outbox)

True exactly-once is achieved by combining idempotency with transactional outbox:

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Messaging;

use Doctrine\ORM\EntityManagerInterface;

final readonly class TransactionalOutboxPublisher
{
    public function __construct(
        private EntityManagerInterface $entityManager,
    ) {}

    public function publishInTransaction(string $idempotencyKey, callable $businessLogic, array $events): void
    {
        $this->entityManager->wrapInTransaction(function () use ($idempotencyKey, $businessLogic, $events): void {
            $businessLogic();

            foreach ($events as $event) {
                $outboxEntry = new OutboxMessage(
                    idempotencyKey: $idempotencyKey,
                    eventType: $event::class,
                    payload: serialize($event),
                    createdAt: new \DateTimeImmutable(),
                );
                $this->entityManager->persist($outboxEntry);
            }
        });
    }
}
```

## Idempotent HTTP Methods

| Method | Idempotent? | Safe? | Notes |
|--------|-------------|-------|-------|
| GET | Yes | Yes | Must not change state |
| HEAD | Yes | Yes | Same as GET without body |
| PUT | Yes | No | Full resource replacement |
| DELETE | Yes | No | Deleting already-deleted is OK |
| OPTIONS | Yes | Yes | Metadata only |
| POST | **No** | No | Requires idempotency key |
| PATCH | **No** | No | Partial update may not be idempotent |

## Non-Idempotent Operation Patterns

### Payment Processing

```php
<?php

declare(strict_types=1);

namespace Application\UseCase;

use Psr\Log\LoggerInterface;

final readonly class ProcessPaymentUseCase
{
    public function __construct(
        private PaymentGatewayInterface $gateway,
        private DeduplicationStoreInterface $dedup,
        private LoggerInterface $logger,
    ) {}

    public function execute(string $idempotencyKey, string $orderId, int $amountCents): PaymentResult
    {
        $cached = $this->dedup->retrieve($idempotencyKey);
        if ($cached !== null) {
            $this->logger->info('Duplicate payment prevented', [
                'idempotency_key' => $idempotencyKey,
                'order_id' => $orderId,
            ]);

            return unserialize($cached, ['allowed_classes' => true]);
        }

        $result = $this->gateway->charge($orderId, $amountCents, $idempotencyKey);

        $this->dedup->store($idempotencyKey, serialize($result));

        return $result;
    }
}
```

### Email Sending

```php
<?php

declare(strict_types=1);

namespace Application\UseCase;

final readonly class SendNotificationUseCase
{
    public function __construct(
        private MailerInterface $mailer,
        private DeduplicationStoreInterface $dedup,
    ) {}

    public function execute(string $idempotencyKey, string $recipientEmail, string $templateId, array $context): void
    {
        if ($this->dedup->exists($idempotencyKey)) {
            return;
        }

        $this->mailer->send($recipientEmail, $templateId, $context);

        $this->dedup->store($idempotencyKey, json_encode([
            'sent_at' => (new \DateTimeImmutable())->format(\DateTimeInterface::ATOM),
            'recipient' => $recipientEmail,
        ]));
    }
}
```

## Idempotency Anti-Patterns

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| No TTL on stored keys | Unbounded storage growth | Always set expiration |
| Idempotency key in body | May not survive proxies | Use HTTP header |
| Server-generated key | Client cannot safely retry | Client generates key |
| Global dedup store | Single point of failure | Scoped per operation type |
| No in-progress lock | Concurrent duplicates | SETNX before processing |
| Storing only success | Failed retries re-execute | Store all terminal states |
