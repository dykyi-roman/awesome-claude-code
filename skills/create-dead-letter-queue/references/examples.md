# Dead Letter Queue Examples

## Message Broker Consumer Integration

### RabbitMQ Consumer with DLQ

**File:** `src/Infrastructure/Messaging/RabbitMq/OrderCreatedConsumer.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Messaging\RabbitMq;

use Application\Order\UseCase\ProcessOrderCreated\ProcessOrderCreatedHandler;
use Application\Shared\DeadLetter\DeadLetterHandler;
use PhpAmqpLib\Message\AMQPMessage;
use Psr\Log\LoggerInterface;

final readonly class OrderCreatedConsumer
{
    public function __construct(
        private ProcessOrderCreatedHandler $handler,
        private DeadLetterHandler $deadLetter,
        private LoggerInterface $logger
    ) {}

    public function consume(AMQPMessage $message): void
    {
        $body = $message->getBody();
        $routingKey = $message->getRoutingKey();
        $headers = $message->get('application_headers')?->getNativeData() ?? [];

        try {
            $this->handler->handle(json_decode($body, true, 512, JSON_THROW_ON_ERROR));
            $message->ack();
        } catch (\Throwable $e) {
            $this->logger->error('Message processing failed', [
                'routing_key' => $routingKey,
                'error' => $e->getMessage(),
            ]);

            $this->deadLetter->handle($body, $routingKey, $headers, $e);
            $message->ack();
        }
    }
}
```

---

## Console Commands

### Retry DLQ Messages Command

**File:** `src/Infrastructure/Console/RetryDeadLetterMessagesCommand.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Console;

use Application\Shared\DeadLetter\DlqProcessor;
use Symfony\Component\Console\Attribute\AsCommand;
use Symfony\Component\Console\Command\Command;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Input\InputOption;
use Symfony\Component\Console\Output\OutputInterface;

#[AsCommand(
    name: 'dlq:retry',
    description: 'Retry messages from Dead Letter Queue'
)]
final class RetryDeadLetterMessagesCommand extends Command
{
    public function __construct(
        private readonly DlqProcessor $processor,
        private readonly MessageHandlerRegistry $handlerRegistry
    ) {
        parent::__construct();
    }

    protected function configure(): void
    {
        $this
            ->addOption('batch-size', 'b', InputOption::VALUE_OPTIONAL, 'Batch size', 100)
            ->addOption('daemon', 'd', InputOption::VALUE_NONE, 'Run as daemon')
            ->addOption('interval', 'i', InputOption::VALUE_OPTIONAL, 'Daemon interval (ms)', 5000);
    }

    protected function execute(InputInterface $input, OutputInterface $output): int
    {
        $batchSize = (int) $input->getOption('batch-size');
        $isDaemon = (bool) $input->getOption('daemon');
        $interval = (int) $input->getOption('interval');

        do {
            $result = $this->processor->process(
                $this->handlerRegistry->resolve(...),
                $batchSize
            );

            $output->writeln(sprintf(
                '<info>Processed: %d, Succeeded: %d, Failed: %d, Skipped: %d</info>',
                $result->processed,
                $result->succeeded,
                $result->failed,
                $result->skipped
            ));

            if ($isDaemon) {
                usleep($interval * 1000);
            }
        } while ($isDaemon);

        return Command::SUCCESS;
    }
}
```

---

### Purge Resolved Messages Command

**File:** `src/Infrastructure/Console/PurgeDeadLetterMessagesCommand.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Console;

use Application\Shared\DeadLetter\DeadLetterStoreInterface;
use Symfony\Component\Console\Attribute\AsCommand;
use Symfony\Component\Console\Command\Command;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Input\InputOption;
use Symfony\Component\Console\Output\OutputInterface;

#[AsCommand(
    name: 'dlq:purge',
    description: 'Purge resolved messages from DLQ older than specified days'
)]
final class PurgeDeadLetterMessagesCommand extends Command
{
    public function __construct(
        private readonly DeadLetterStoreInterface $store
    ) {
        parent::__construct();
    }

    protected function configure(): void
    {
        $this->addOption('days', 'd', InputOption::VALUE_OPTIONAL, 'Purge messages older than N days', 30);
    }

    protected function execute(InputInterface $input, OutputInterface $output): int
    {
        $days = (int) $input->getOption('days');
        $before = (new \DateTimeImmutable())->modify(sprintf('-%d days', $days));

        $deleted = $this->store->purge($before);

        $output->writeln(sprintf('<info>Purged %d resolved messages older than %s</info>', $deleted, $before->format('Y-m-d')));

        return Command::SUCCESS;
    }
}
```

---

## Monitoring Endpoint

### DLQ Dashboard Action

**File:** `src/Presentation/Api/Admin/DlqStats/DlqStatsAction.php`

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\Admin\DlqStats;

use Application\Shared\DeadLetter\DeadLetterStoreInterface;
use Domain\Shared\DeadLetter\FailureType;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;

final readonly class DlqStatsAction
{
    public function __construct(
        private DeadLetterStoreInterface $store,
        private DlqStatsResponder $responder
    ) {}

    public function __invoke(ServerRequestInterface $request): ResponseInterface
    {
        $stats = [
            'transient' => $this->store->countByType(FailureType::Transient),
            'permanent' => $this->store->countByType(FailureType::Permanent),
            'unknown' => $this->store->countByType(FailureType::Unknown),
        ];

        return $this->responder->respond($stats);
    }
}
```

---

## DI Configuration

### Symfony Services

**File:** `config/services.yaml`

```yaml
services:
  Application\Shared\DeadLetter\DeadLetterStoreInterface:
    alias: Infrastructure\DeadLetter\DatabaseDeadLetterStore

  Application\Shared\DeadLetter\RetryStrategy:
    arguments:
      $maxAttempts: '%env(int:DLQ_MAX_RETRIES)%'
      $baseDelaySeconds: '%env(int:DLQ_BASE_DELAY_SECONDS)%'
      $multiplier: '%env(float:DLQ_BACKOFF_MULTIPLIER)%'

  Application\Shared\DeadLetter\FailureClassifier:
    arguments:
      $customMapping:
        App\Domain\Order\OrderNotFoundException: !php/const Domain\Shared\DeadLetter\FailureType::Permanent
        App\Domain\Payment\PaymentDeclinedException: !php/const Domain\Shared\DeadLetter\FailureType::Permanent

  Infrastructure\DeadLetter\DatabaseDeadLetterStore:
    arguments:
      $pdo: '@database_connection'
```

**File:** `.env`

```env
DLQ_MAX_RETRIES=5
DLQ_BASE_DELAY_SECONDS=60
DLQ_BACKOFF_MULTIPLIER=2.0
```

---

## Unit Tests

### DeadLetterMessageTest

**File:** `tests/Unit/Domain/Shared/DeadLetter/DeadLetterMessageTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\Shared\DeadLetter;

use Domain\Shared\DeadLetter\DeadLetterMessage;
use Domain\Shared\DeadLetter\FailureType;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(DeadLetterMessage::class)]
final class DeadLetterMessageTest extends TestCase
{
    public function testCreateFactoryMethod(): void
    {
        $message = DeadLetterMessage::create(
            originalBody: '{"order_id": "123"}',
            originalRoutingKey: 'order.created',
            originalHeaders: ['content-type' => 'application/json'],
            errorMessage: 'Database connection failed',
            errorTrace: 'Stack trace...',
            failureType: FailureType::Transient
        );

        self::assertNotEmpty($message->id);
        self::assertSame(1, $message->attemptCount);
        self::assertNull($message->nextRetryAt);
        self::assertNull($message->resolvedAt);
    }

    public function testIsRetryableReturnsTrueForTransient(): void
    {
        $message = new DeadLetterMessage(
            id: '123',
            originalBody: '{}',
            originalRoutingKey: 'test',
            originalHeaders: [],
            errorMessage: 'Error',
            errorTrace: 'Trace',
            failureType: FailureType::Transient,
            attemptCount: 2,
            failedAt: new \DateTimeImmutable(),
        );

        self::assertTrue($message->isRetryable(5));
    }

    public function testIsRetryableReturnsFalseForPermanent(): void
    {
        $message = new DeadLetterMessage(
            id: '123',
            originalBody: '{}',
            originalRoutingKey: 'test',
            originalHeaders: [],
            errorMessage: 'Error',
            errorTrace: 'Trace',
            failureType: FailureType::Permanent,
            attemptCount: 1,
            failedAt: new \DateTimeImmutable(),
        );

        self::assertFalse($message->isRetryable(5));
    }

    public function testIsRetryableReturnsFalseWhenMaxRetriesExceeded(): void
    {
        $message = new DeadLetterMessage(
            id: '123',
            originalBody: '{}',
            originalRoutingKey: 'test',
            originalHeaders: [],
            errorMessage: 'Error',
            errorTrace: 'Trace',
            failureType: FailureType::Transient,
            attemptCount: 5,
            failedAt: new \DateTimeImmutable(),
        );

        self::assertFalse($message->isRetryable(5));
    }

    public function testWithIncrementedAttempt(): void
    {
        $original = DeadLetterMessage::create(
            originalBody: '{}',
            originalRoutingKey: 'test',
            originalHeaders: [],
            errorMessage: 'Error',
            errorTrace: 'Trace',
            failureType: FailureType::Transient
        );

        $nextRetry = new \DateTimeImmutable('+1 hour');
        $incremented = $original->withIncrementedAttempt($nextRetry);

        self::assertSame(2, $incremented->attemptCount);
        self::assertSame($nextRetry, $incremented->nextRetryAt);
        self::assertSame(1, $original->attemptCount);
    }
}
```

---

### RetryStrategyTest

**File:** `tests/Unit/Application/Shared/DeadLetter/RetryStrategyTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Application\Shared\DeadLetter;

use Application\Shared\DeadLetter\RetryStrategy;
use Domain\Shared\DeadLetter\DeadLetterMessage;
use Domain\Shared\DeadLetter\FailureType;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(RetryStrategy::class)]
final class RetryStrategyTest extends TestCase
{
    public function testShouldRetryReturnsTrueWhenBelowMaxAttempts(): void
    {
        $strategy = new RetryStrategy(maxAttempts: 5);

        $message = new DeadLetterMessage(
            id: '123',
            originalBody: '{}',
            originalRoutingKey: 'test',
            originalHeaders: [],
            errorMessage: 'Error',
            errorTrace: 'Trace',
            failureType: FailureType::Transient,
            attemptCount: 3,
            failedAt: new \DateTimeImmutable(),
        );

        self::assertTrue($strategy->shouldRetry($message));
    }

    public function testShouldRetryReturnsFalseWhenMaxAttemptsReached(): void
    {
        $strategy = new RetryStrategy(maxAttempts: 5);

        $message = new DeadLetterMessage(
            id: '123',
            originalBody: '{}',
            originalRoutingKey: 'test',
            originalHeaders: [],
            errorMessage: 'Error',
            errorTrace: 'Trace',
            failureType: FailureType::Transient,
            attemptCount: 5,
            failedAt: new \DateTimeImmutable(),
        );

        self::assertFalse($strategy->shouldRetry($message));
    }

    public function testCalculateNextRetryAtExponentialBackoff(): void
    {
        $strategy = new RetryStrategy(
            maxAttempts: 5,
            baseDelaySeconds: 60,
            multiplier: 2.0
        );

        $message = new DeadLetterMessage(
            id: '123',
            originalBody: '{}',
            originalRoutingKey: 'test',
            originalHeaders: [],
            errorMessage: 'Error',
            errorTrace: 'Trace',
            failureType: FailureType::Transient,
            attemptCount: 2,
            failedAt: new \DateTimeImmutable(),
        );

        $now = new \DateTimeImmutable();
        $nextRetry = $strategy->calculateNextRetryAt($message);

        $diff = $nextRetry->getTimestamp() - $now->getTimestamp();

        self::assertGreaterThanOrEqual(90, $diff);
        self::assertLessThanOrEqual(150, $diff);
    }
}
```

---

### FailureClassifierTest

**File:** `tests/Unit/Application/Shared/DeadLetter/FailureClassifierTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Application\Shared\DeadLetter;

use Application\Shared\DeadLetter\FailureClassifier;
use Domain\Shared\DeadLetter\FailureType;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(FailureClassifier::class)]
final class FailureClassifierTest extends TestCase
{
    public function testClassifiesPDOExceptionAsTransient(): void
    {
        $classifier = new FailureClassifier();

        $type = $classifier->classify(new \PDOException('Connection lost'));

        self::assertSame(FailureType::Transient, $type);
    }

    public function testClassifiesInvalidArgumentExceptionAsPermanent(): void
    {
        $classifier = new FailureClassifier();

        $type = $classifier->classify(new \InvalidArgumentException('Invalid input'));

        self::assertSame(FailureType::Permanent, $type);
    }

    public function testClassifiesUnknownExceptionAsUnknown(): void
    {
        $classifier = new FailureClassifier();

        $type = $classifier->classify(new \Exception('Unknown error'));

        self::assertSame(FailureType::Unknown, $type);
    }

    public function testCustomMappingOverridesDefault(): void
    {
        $classifier = new FailureClassifier([
            \PDOException::class => FailureType::Permanent,
        ]);

        $type = $classifier->classify(new \PDOException('Custom handling'));

        self::assertSame(FailureType::Permanent, $type);
    }
}
```

---

### DlqProcessorTest

**File:** `tests/Unit/Application/Shared/DeadLetter/DlqProcessorTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Application\Shared\DeadLetter;

use Application\Shared\DeadLetter\DeadLetterStoreInterface;
use Application\Shared\DeadLetter\DlqProcessor;
use Application\Shared\DeadLetter\RetryStrategy;
use Domain\Shared\DeadLetter\DeadLetterMessage;
use Domain\Shared\DeadLetter\FailureType;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;
use Psr\Log\NullLogger;

#[Group('unit')]
#[CoversClass(DlqProcessor::class)]
final class DlqProcessorTest extends TestCase
{
    public function testProcessMarksResolvedOnSuccess(): void
    {
        $message = new DeadLetterMessage(
            id: '123',
            originalBody: '{"test": true}',
            originalRoutingKey: 'test.route',
            originalHeaders: [],
            errorMessage: 'Error',
            errorTrace: 'Trace',
            failureType: FailureType::Transient,
            attemptCount: 1,
            failedAt: new \DateTimeImmutable(),
        );

        $store = $this->createMock(DeadLetterStoreInterface::class);
        $store->method('findRetryable')->willReturn([$message]);
        $store->expects($this->once())->method('markResolved')->with('123');

        $strategy = $this->createMock(RetryStrategy::class);
        $strategy->method('shouldRetry')->willReturn(true);

        $processor = new DlqProcessor($store, $strategy, new NullLogger());

        $handler = function (string $body, string $routingKey, array $headers): void {
            // Success
        };

        $result = $processor->process($handler, 100);

        self::assertSame(1, $result->processed);
        self::assertSame(1, $result->succeeded);
        self::assertSame(0, $result->failed);
    }

    public function testProcessIncrementsRetryOnFailure(): void
    {
        $message = new DeadLetterMessage(
            id: '123',
            originalBody: '{}',
            originalRoutingKey: 'test',
            originalHeaders: [],
            errorMessage: 'Error',
            errorTrace: 'Trace',
            failureType: FailureType::Transient,
            attemptCount: 2,
            failedAt: new \DateTimeImmutable(),
        );

        $store = $this->createMock(DeadLetterStoreInterface::class);
        $store->method('findRetryable')->willReturn([$message]);
        $store->expects($this->once())->method('markRetried');

        $strategy = new RetryStrategy();

        $processor = new DlqProcessor($store, $strategy, new NullLogger());

        $handler = function (): void {
            throw new \RuntimeException('Still failing');
        };

        $result = $processor->process($handler, 100);

        self::assertSame(1, $result->processed);
        self::assertSame(0, $result->succeeded);
        self::assertSame(1, $result->failed);
    }
}
```
