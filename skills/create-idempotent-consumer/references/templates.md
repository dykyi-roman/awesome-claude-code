# Idempotent Consumer Templates

Complete PHP 8.4 templates for all Idempotent Consumer components.

---

## Domain Layer

### IdempotencyKey.php

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\Idempotency;

final readonly class IdempotencyKey implements \Stringable
{
    public function __construct(
        public string $messageId,
        public string $handlerName,
    ) {
        if ($messageId === '') {
            throw new \InvalidArgumentException('Message ID cannot be empty');
        }
        if ($handlerName === '') {
            throw new \InvalidArgumentException('Handler name cannot be empty');
        }
    }

    public static function fromMessage(string $messageId, string $handlerName): self
    {
        return new self($messageId, $handlerName);
    }

    public function toString(): string
    {
        return sprintf('%s:%s', $this->handlerName, $this->messageId);
    }

    public function __toString(): string
    {
        return $this->toString();
    }

    public function equals(self $other): bool
    {
        return $this->messageId === $other->messageId
            && $this->handlerName === $other->handlerName;
    }
}
```

### ProcessingStatus.php

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\Idempotency;

enum ProcessingStatus: string
{
    case Processed = 'processed';
    case Duplicate = 'duplicate';
    case Failed = 'failed';
}
```

### ProcessingResult.php

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\Idempotency;

final readonly class ProcessingResult
{
    private function __construct(
        public ProcessingStatus $status,
        public mixed $data = null,
        public ?string $error = null,
    ) {}

    public static function processed(mixed $data = null): self
    {
        return new self(ProcessingStatus::Processed, $data);
    }

    public static function duplicate(): self
    {
        return new self(ProcessingStatus::Duplicate);
    }

    public static function failed(string $error): self
    {
        return new self(ProcessingStatus::Failed, error: $error);
    }

    public function isProcessed(): bool
    {
        return $this->status === ProcessingStatus::Processed;
    }

    public function isDuplicate(): bool
    {
        return $this->status === ProcessingStatus::Duplicate;
    }

    public function isFailed(): bool
    {
        return $this->status === ProcessingStatus::Failed;
    }
}
```

---

## Application Layer

### IdempotencyStoreInterface.php

```php
<?php

declare(strict_types=1);

namespace Application\Shared\Idempotency;

use Domain\Shared\Idempotency\IdempotencyKey;

interface IdempotencyStoreInterface
{
    public function has(IdempotencyKey $key): bool;

    public function mark(IdempotencyKey $key, \DateTimeImmutable $expiresAt): void;

    public function remove(IdempotencyKey $key): void;
}
```

### IdempotentConsumerMiddleware.php

```php
<?php

declare(strict_types=1);

namespace Application\Shared\Idempotency;

use Domain\Shared\Idempotency\IdempotencyKey;
use Domain\Shared\Idempotency\ProcessingResult;

final readonly class IdempotentConsumerMiddleware
{
    public function __construct(
        private IdempotencyStoreInterface $store,
    ) {}

    public function process(
        IdempotencyKey $key,
        callable $handler,
        ?\DateTimeImmutable $ttl = null,
    ): ProcessingResult {
        if ($this->store->has($key)) {
            return ProcessingResult::duplicate();
        }

        try {
            $result = $handler();

            $expiresAt = $ttl ?? new \DateTimeImmutable('+7 days');
            $this->store->mark($key, $expiresAt);

            return ProcessingResult::processed($result);
        } catch (\Throwable $e) {
            return ProcessingResult::failed($e->getMessage());
        }
    }
}
```

---

## Infrastructure Layer

### DatabaseIdempotencyStore.php

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Idempotency;

use Application\Shared\Idempotency\IdempotencyStoreInterface;
use Domain\Shared\Idempotency\IdempotencyKey;

final readonly class DatabaseIdempotencyStore implements IdempotencyStoreInterface
{
    public function __construct(
        private \PDO $connection,
    ) {}

    public function has(IdempotencyKey $key): bool
    {
        $sql = <<<SQL
            SELECT 1 FROM idempotency_keys
            WHERE key = :key
            AND expires_at > NOW()
            LIMIT 1
        SQL;

        $stmt = $this->connection->prepare($sql);
        $stmt->execute(['key' => $key->toString()]);

        return $stmt->fetchColumn() !== false;
    }

    public function mark(IdempotencyKey $key, \DateTimeImmutable $expiresAt): void
    {
        $sql = <<<SQL
            INSERT INTO idempotency_keys (key, handler_name, processed_at, expires_at)
            VALUES (:key, :handler_name, :processed_at, :expires_at)
            ON CONFLICT (key) DO NOTHING
        SQL;

        $stmt = $this->connection->prepare($sql);
        $stmt->execute([
            'key' => $key->toString(),
            'handler_name' => $key->handlerName,
            'processed_at' => (new \DateTimeImmutable())->format('Y-m-d H:i:s.u'),
            'expires_at' => $expiresAt->format('Y-m-d H:i:s.u'),
        ]);
    }

    public function remove(IdempotencyKey $key): void
    {
        $sql = 'DELETE FROM idempotency_keys WHERE key = :key';

        $stmt = $this->connection->prepare($sql);
        $stmt->execute(['key' => $key->toString()]);
    }

    public function cleanup(\DateTimeImmutable $before): int
    {
        $sql = 'DELETE FROM idempotency_keys WHERE expires_at < :before';

        $stmt = $this->connection->prepare($sql);
        $stmt->execute(['before' => $before->format('Y-m-d H:i:s.u')]);

        return $stmt->rowCount();
    }
}
```

### RedisIdempotencyStore.php

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Idempotency;

use Application\Shared\Idempotency\IdempotencyStoreInterface;
use Domain\Shared\Idempotency\IdempotencyKey;

final readonly class RedisIdempotencyStore implements IdempotencyStoreInterface
{
    public function __construct(
        private \Redis $redis,
        private string $prefix = 'idempotency:',
    ) {}

    public function has(IdempotencyKey $key): bool
    {
        return $this->redis->exists($this->buildKey($key)) > 0;
    }

    public function mark(IdempotencyKey $key, \DateTimeImmutable $expiresAt): void
    {
        $redisKey = $this->buildKey($key);
        $ttlSeconds = $expiresAt->getTimestamp() - time();

        if ($ttlSeconds <= 0) {
            return;
        }

        $this->redis->setex(
            $redisKey,
            $ttlSeconds,
            json_encode([
                'handler_name' => $key->handlerName,
                'processed_at' => (new \DateTimeImmutable())->format('c'),
            ], JSON_THROW_ON_ERROR)
        );
    }

    public function remove(IdempotencyKey $key): void
    {
        $this->redis->del($this->buildKey($key));
    }

    private function buildKey(IdempotencyKey $key): string
    {
        return $this->prefix . $key->toString();
    }
}
```

### Database Migration

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Persistence\Migration;

use Doctrine\DBAL\Schema\Schema;
use Doctrine\Migrations\AbstractMigration;

final class Version20260214000001 extends AbstractMigration
{
    public function getDescription(): string
    {
        return 'Create idempotency_keys table for Idempotent Consumer pattern';
    }

    public function up(Schema $schema): void
    {
        $this->addSql(<<<SQL
            CREATE TABLE idempotency_keys (
                key VARCHAR(255) PRIMARY KEY,
                handler_name VARCHAR(255) NOT NULL,
                processed_at TIMESTAMP(6) NOT NULL,
                expires_at TIMESTAMP(6) NOT NULL
            )
        SQL);

        $this->addSql(
            'CREATE INDEX idx_idempotency_expires ON idempotency_keys (expires_at)'
        );
    }

    public function down(Schema $schema): void
    {
        $this->addSql('DROP TABLE idempotency_keys');
    }
}
```

---

## Console Command

### PurgeExpiredIdempotencyKeysCommand.php

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Console;

use Infrastructure\Idempotency\DatabaseIdempotencyStore;
use Symfony\Component\Console\Attribute\AsCommand;
use Symfony\Component\Console\Command\Command;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Output\OutputInterface;
use Symfony\Component\Console\Style\SymfonyStyle;

#[AsCommand(
    name: 'idempotency:purge-expired',
    description: 'Purge expired idempotency keys from the database',
)]
final class PurgeExpiredIdempotencyKeysCommand extends Command
{
    public function __construct(
        private readonly DatabaseIdempotencyStore $store,
    ) {
        parent::__construct();
    }

    protected function execute(InputInterface $input, OutputInterface $output): int
    {
        $io = new SymfonyStyle($input, $output);

        $before = new \DateTimeImmutable();
        $deleted = $this->store->cleanup($before);

        $io->success(sprintf('Purged %d expired idempotency key(s)', $deleted));

        return Command::SUCCESS;
    }
}
```

---

## Tests

### IdempotencyKeyTest.php

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\Shared\Idempotency;

use Domain\Shared\Idempotency\IdempotencyKey;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(IdempotencyKey::class)]
final class IdempotencyKeyTest extends TestCase
{
    public function testFromMessageCreatesKey(): void
    {
        $key = IdempotencyKey::fromMessage('msg-123', 'PaymentHandler');

        self::assertSame('msg-123', $key->messageId);
        self::assertSame('PaymentHandler', $key->handlerName);
    }

    public function testToStringFormatsKeyCorrectly(): void
    {
        $key = new IdempotencyKey('msg-123', 'PaymentHandler');

        self::assertSame('PaymentHandler:msg-123', $key->toString());
        self::assertSame('PaymentHandler:msg-123', (string) $key);
    }

    public function testEqualsReturnsTrueForSameValues(): void
    {
        $key1 = new IdempotencyKey('msg-123', 'PaymentHandler');
        $key2 = new IdempotencyKey('msg-123', 'PaymentHandler');

        self::assertTrue($key1->equals($key2));
    }

    public function testEqualsReturnsFalseForDifferentMessageId(): void
    {
        $key1 = new IdempotencyKey('msg-123', 'PaymentHandler');
        $key2 = new IdempotencyKey('msg-456', 'PaymentHandler');

        self::assertFalse($key1->equals($key2));
    }

    public function testEqualsReturnsFalseForDifferentHandler(): void
    {
        $key1 = new IdempotencyKey('msg-123', 'PaymentHandler');
        $key2 = new IdempotencyKey('msg-123', 'OrderHandler');

        self::assertFalse($key1->equals($key2));
    }

    public function testThrowsExceptionForEmptyMessageId(): void
    {
        $this->expectException(\InvalidArgumentException::class);
        $this->expectExceptionMessage('Message ID cannot be empty');

        new IdempotencyKey('', 'PaymentHandler');
    }

    public function testThrowsExceptionForEmptyHandlerName(): void
    {
        $this->expectException(\InvalidArgumentException::class);
        $this->expectExceptionMessage('Handler name cannot be empty');

        new IdempotencyKey('msg-123', '');
    }
}
```

### ProcessingResultTest.php

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\Shared\Idempotency;

use Domain\Shared\Idempotency\ProcessingResult;
use Domain\Shared\Idempotency\ProcessingStatus;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(ProcessingResult::class)]
final class ProcessingResultTest extends TestCase
{
    public function testProcessedCreatesResultWithData(): void
    {
        $result = ProcessingResult::processed(['orderId' => '123']);

        self::assertTrue($result->isProcessed());
        self::assertFalse($result->isDuplicate());
        self::assertFalse($result->isFailed());
        self::assertSame(ProcessingStatus::Processed, $result->status);
        self::assertSame(['orderId' => '123'], $result->data);
        self::assertNull($result->error);
    }

    public function testDuplicateCreatesResultWithoutData(): void
    {
        $result = ProcessingResult::duplicate();

        self::assertFalse($result->isProcessed());
        self::assertTrue($result->isDuplicate());
        self::assertFalse($result->isFailed());
        self::assertSame(ProcessingStatus::Duplicate, $result->status);
        self::assertNull($result->data);
        self::assertNull($result->error);
    }

    public function testFailedCreatesResultWithError(): void
    {
        $result = ProcessingResult::failed('Connection timeout');

        self::assertFalse($result->isProcessed());
        self::assertFalse($result->isDuplicate());
        self::assertTrue($result->isFailed());
        self::assertSame(ProcessingStatus::Failed, $result->status);
        self::assertNull($result->data);
        self::assertSame('Connection timeout', $result->error);
    }
}
```

### IdempotentConsumerMiddlewareTest.php

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Application\Shared\Idempotency;

use Application\Shared\Idempotency\IdempotencyStoreInterface;
use Application\Shared\Idempotency\IdempotentConsumerMiddleware;
use Domain\Shared\Idempotency\IdempotencyKey;
use Domain\Shared\Idempotency\ProcessingStatus;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(IdempotentConsumerMiddleware::class)]
final class IdempotentConsumerMiddlewareTest extends TestCase
{
    private IdempotencyStoreInterface $store;
    private IdempotentConsumerMiddleware $middleware;

    protected function setUp(): void
    {
        $this->store = $this->createMock(IdempotencyStoreInterface::class);
        $this->middleware = new IdempotentConsumerMiddleware($this->store);
    }

    public function testProcessesNewMessage(): void
    {
        $key = IdempotencyKey::fromMessage('msg-123', 'PaymentHandler');
        $expectedData = ['orderId' => '123'];

        $this->store
            ->expects($this->once())
            ->method('has')
            ->with($key)
            ->willReturn(false);

        $this->store
            ->expects($this->once())
            ->method('mark')
            ->with(
                $key,
                $this->callback(fn (\DateTimeImmutable $ttl) => $ttl > new \DateTimeImmutable())
            );

        $result = $this->middleware->process(
            $key,
            fn () => $expectedData
        );

        self::assertSame(ProcessingStatus::Processed, $result->status);
        self::assertSame($expectedData, $result->data);
    }

    public function testReturnsDuplicateForExistingKey(): void
    {
        $key = IdempotencyKey::fromMessage('msg-123', 'PaymentHandler');

        $this->store
            ->expects($this->once())
            ->method('has')
            ->with($key)
            ->willReturn(true);

        $this->store
            ->expects($this->never())
            ->method('mark');

        $result = $this->middleware->process(
            $key,
            fn () => ['orderId' => '123']
        );

        self::assertSame(ProcessingStatus::Duplicate, $result->status);
    }

    public function testReturnsFailedOnException(): void
    {
        $key = IdempotencyKey::fromMessage('msg-123', 'PaymentHandler');

        $this->store
            ->expects($this->once())
            ->method('has')
            ->with($key)
            ->willReturn(false);

        $this->store
            ->expects($this->never())
            ->method('mark');

        $result = $this->middleware->process(
            $key,
            function () {
                throw new \RuntimeException('Payment failed');
            }
        );

        self::assertSame(ProcessingStatus::Failed, $result->status);
        self::assertSame('Payment failed', $result->error);
    }

    public function testUsesCustomTtl(): void
    {
        $key = IdempotencyKey::fromMessage('msg-123', 'PaymentHandler');
        $customTtl = new \DateTimeImmutable('+30 days');

        $this->store
            ->expects($this->once())
            ->method('has')
            ->willReturn(false);

        $this->store
            ->expects($this->once())
            ->method('mark')
            ->with($key, $customTtl);

        $this->middleware->process(
            $key,
            fn () => ['orderId' => '123'],
            $customTtl
        );
    }
}
```

### DatabaseIdempotencyStoreTest.php

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Infrastructure\Idempotency;

use Domain\Shared\Idempotency\IdempotencyKey;
use Infrastructure\Idempotency\DatabaseIdempotencyStore;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(DatabaseIdempotencyStore::class)]
final class DatabaseIdempotencyStoreTest extends TestCase
{
    private \PDO $pdo;
    private DatabaseIdempotencyStore $store;

    protected function setUp(): void
    {
        $this->pdo = new \PDO('sqlite::memory:');
        $this->pdo->setAttribute(\PDO::ATTR_ERRMODE, \PDO::ERRMODE_EXCEPTION);

        $this->pdo->exec(<<<SQL
            CREATE TABLE idempotency_keys (
                key VARCHAR(255) PRIMARY KEY,
                handler_name VARCHAR(255) NOT NULL,
                processed_at TIMESTAMP NOT NULL,
                expires_at TIMESTAMP NOT NULL
            )
        SQL);

        $this->store = new DatabaseIdempotencyStore($this->pdo);
    }

    public function testHasReturnsFalseForNonExistentKey(): void
    {
        $key = IdempotencyKey::fromMessage('msg-123', 'PaymentHandler');

        self::assertFalse($this->store->has($key));
    }

    public function testMarkInsertsKey(): void
    {
        $key = IdempotencyKey::fromMessage('msg-123', 'PaymentHandler');
        $expiresAt = new \DateTimeImmutable('+7 days');

        $this->store->mark($key, $expiresAt);

        self::assertTrue($this->store->has($key));
    }

    public function testHasReturnsTrueForExistingKey(): void
    {
        $key = IdempotencyKey::fromMessage('msg-123', 'PaymentHandler');
        $expiresAt = new \DateTimeImmutable('+7 days');

        $this->store->mark($key, $expiresAt);

        self::assertTrue($this->store->has($key));
    }

    public function testRemoveDeletesKey(): void
    {
        $key = IdempotencyKey::fromMessage('msg-123', 'PaymentHandler');
        $expiresAt = new \DateTimeImmutable('+7 days');

        $this->store->mark($key, $expiresAt);
        $this->store->remove($key);

        self::assertFalse($this->store->has($key));
    }

    public function testCleanupRemovesExpiredKeys(): void
    {
        $key1 = IdempotencyKey::fromMessage('msg-123', 'PaymentHandler');
        $key2 = IdempotencyKey::fromMessage('msg-456', 'OrderHandler');

        $this->store->mark($key1, new \DateTimeImmutable('-1 day'));
        $this->store->mark($key2, new \DateTimeImmutable('+1 day'));

        $deleted = $this->store->cleanup(new \DateTimeImmutable());

        self::assertSame(1, $deleted);
        self::assertFalse($this->store->has($key1));
        self::assertTrue($this->store->has($key2));
    }
}
```
