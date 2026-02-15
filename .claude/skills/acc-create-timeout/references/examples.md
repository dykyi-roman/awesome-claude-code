# Timeout Pattern Usage Examples

Real-world examples for Timeout pattern implementation.

---

## Example 1: External API Call with Timeout

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Payment;

use Domain\Shared\Timeout\TimeoutConfig;
use Domain\Shared\Timeout\TimeoutException;
use Domain\Shared\Timeout\TimeoutInterface;
use Psr\Http\Client\ClientInterface;
use Psr\Http\Message\RequestInterface;
use Psr\Http\Message\ResponseInterface;
use Psr\Log\LoggerInterface;

final readonly class ResilientHttpClient
{
    public function __construct(
        private ClientInterface $httpClient,
        private TimeoutInterface $timeout,
        private LoggerInterface $logger,
    ) {}

    public function send(RequestInterface $request): ResponseInterface
    {
        $config = TimeoutConfig::of(seconds: 5.0, operationName: 'http-request')
            ->withFallback(fn() => $this->createTimeoutResponse())
            ->withRetry(true);

        try {
            return $this->timeout->execute(
                operation: fn() => $this->httpClient->sendRequest($request),
                config: $config,
            );
        } catch (TimeoutException $e) {
            $this->logger->error('HTTP request timed out', $e->toArray());
            throw $e;
        }
    }

    private function createTimeoutResponse(): ResponseInterface
    {
        return new Response(
            status: 504,
            headers: ['X-Timeout' => 'true'],
            body: json_encode(['error' => 'Gateway timeout']),
        );
    }
}
```

---

## Example 2: Database Query Timeout

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Database;

use Domain\Shared\Timeout\TimeoutConfig;
use Domain\Shared\Timeout\TimeoutInterface;
use Psr\Log\LoggerInterface;

final readonly class QueryExecutor
{
    public function __construct(
        private \PDO $pdo,
        private TimeoutInterface $timeout,
        private LoggerInterface $logger,
    ) {}

    public function executeQuery(string $sql, array $params = []): array
    {
        $config = $this->getTimeoutConfig($sql);

        return $this->timeout->execute(
            operation: function () use ($sql, $params): array {
                $stmt = $this->pdo->prepare($sql);
                $stmt->execute($params);
                return $stmt->fetchAll(\PDO::FETCH_ASSOC);
            },
            config: $config,
        );
    }

    private function getTimeoutConfig(string $sql): TimeoutConfig
    {
        if (str_contains(strtoupper($sql), 'JOIN')) {
            return TimeoutConfig::slow()->withOperationName('complex-query');
        }

        if (str_starts_with(strtoupper(trim($sql)), 'SELECT')) {
            return TimeoutConfig::standard()->withOperationName('select-query');
        }

        return TimeoutConfig::fast()->withOperationName('simple-query');
    }
}
```

---

## Example 3: Composition with Circuit Breaker

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Integration;

use Domain\Shared\Timeout\TimeoutConfig;
use Domain\Shared\Timeout\TimeoutInterface;
use Infrastructure\Resilience\CircuitBreaker\CircuitBreaker;
use Psr\Log\LoggerInterface;

final readonly class ResilientApiClient
{
    public function __construct(
        private TimeoutInterface $timeout,
        private CircuitBreaker $circuitBreaker,
        private LoggerInterface $logger,
    ) {}

    public function call(string $endpoint, array $data): array
    {
        return $this->circuitBreaker->execute(
            operation: fn() => $this->executeWithTimeout($endpoint, $data),
            fallback: fn() => $this->getFallbackResponse($endpoint),
        );
    }

    private function executeWithTimeout(string $endpoint, array $data): array
    {
        $config = TimeoutConfig::of(seconds: 3.0, operationName: "api-call-{$endpoint}");

        return $this->timeout->execute(
            operation: fn() => $this->performRequest($endpoint, $data),
            config: $config,
        );
    }

    private function performRequest(string $endpoint, array $data): array
    {
        $response = file_get_contents(
            "https://api.example.com/{$endpoint}",
            false,
            stream_context_create([
                'http' => [
                    'method' => 'POST',
                    'header' => 'Content-Type: application/json',
                    'content' => json_encode($data),
                ],
            ])
        );

        return json_decode($response, true);
    }

    private function getFallbackResponse(string $endpoint): array
    {
        $this->logger->warning('Using fallback response', ['endpoint' => $endpoint]);
        return ['status' => 'fallback', 'endpoint' => $endpoint];
    }
}
```

---

## Example 4: Stream Timeout

```php
<?php

declare(strict_types=1);

namespace Infrastructure\File;

use Domain\Shared\Timeout\TimeoutConfig;
use Infrastructure\Resilience\Timeout\StreamTimeoutExecutor;
use Psr\Log\LoggerInterface;

final readonly class RemoteFileReader
{
    public function __construct(
        private StreamTimeoutExecutor $streamTimeout,
        private LoggerInterface $logger,
    ) {}

    public function readFile(string $url): string
    {
        $stream = fopen($url, 'r');
        if (!is_resource($stream)) {
            throw new \RuntimeException("Failed to open stream: {$url}");
        }

        try {
            $config = TimeoutConfig::of(seconds: 10.0, operationName: 'file-download')
                ->withFallback(fn() => '');

            return $this->streamTimeout->executeOnStream(
                stream: $stream,
                operation: fn($s) => stream_get_contents($s),
                config: $config,
            );
        } finally {
            if (is_resource($stream)) {
                fclose($stream);
            }
        }
    }
}
```

---

## Example 5: Queue Consumer with Timeout

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Queue;

use Domain\Shared\Timeout\TimeoutConfig;
use Domain\Shared\Timeout\TimeoutException;
use Domain\Shared\Timeout\TimeoutInterface;
use Psr\Log\LoggerInterface;

final readonly class MessageConsumer
{
    public function __construct(
        private TimeoutInterface $timeout,
        private LoggerInterface $logger,
        private DeadLetterQueue $deadLetter,
    ) {}

    public function consume(Message $message, callable $handler): void
    {
        $config = TimeoutConfig::of(
            seconds: $message->getTimeoutSeconds(),
            operationName: "message-{$message->getId()}",
        )->withRetry(false);

        try {
            $this->timeout->execute(
                operation: fn() => $handler($message),
                config: $config,
            );
        } catch (TimeoutException $e) {
            $this->logger->error('Message processing timed out', array_merge(
                $e->toArray(),
                ['message_id' => $message->getId()]
            ));

            $this->deadLetter->send($message, $e);
        }
    }
}
```

---

## Example 6: Monitoring and Logging

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Monitoring;

use Domain\Shared\Timeout\TimeoutConfig;
use Domain\Shared\Timeout\TimeoutException;
use Domain\Shared\Timeout\TimeoutInterface;
use Psr\Log\LoggerInterface;

final readonly class MonitoredTimeoutExecutor implements TimeoutInterface
{
    public function __construct(
        private TimeoutInterface $timeout,
        private LoggerInterface $logger,
        private MetricsCollector $metrics,
    ) {}

    public function execute(callable $operation, TimeoutConfig $config): mixed
    {
        $startTime = microtime(true);

        try {
            $result = $this->timeout->execute($operation, $config);

            $duration = microtime(true) - $startTime;
            $this->recordSuccess($config->operationName, $duration);

            return $result;
        } catch (TimeoutException $e) {
            $this->recordTimeout($config->operationName, $e);
            throw $e;
        }
    }

    private function recordSuccess(string $operation, float $duration): void
    {
        $this->logger->info('Operation completed', [
            'operation' => $operation,
            'duration' => $duration,
        ]);

        $this->metrics->increment("timeout.success.{$operation}");
        $this->metrics->timing("timeout.duration.{$operation}", $duration);
    }

    private function recordTimeout(string $operation, TimeoutException $e): void
    {
        $this->logger->error('Operation timed out', array_merge(
            $e->toArray(),
            ['tags' => ['timeout']]
        ));

        $this->metrics->increment("timeout.exceeded.{$operation}");
        $this->metrics->gauge("timeout.elapsed.{$operation}", $e->elapsedSeconds);
    }
}
```

---

## Unit Tests

### TimeoutConfigTest.php

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\Shared\Timeout;

use Domain\Shared\Timeout\TimeoutConfig;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(TimeoutConfig::class)]
final class TimeoutConfigTest extends TestCase
{
    public function testFastPreset(): void
    {
        $config = TimeoutConfig::fast();

        self::assertSame(3.0, $config->durationSeconds);
        self::assertSame('fast-operation', $config->operationName);
    }

    public function testStandardPreset(): void
    {
        $config = TimeoutConfig::standard();

        self::assertSame(10.0, $config->durationSeconds);
        self::assertSame('standard-operation', $config->operationName);
    }

    public function testSlowPreset(): void
    {
        $config = TimeoutConfig::slow();

        self::assertSame(30.0, $config->durationSeconds);
        self::assertSame('slow-operation', $config->operationName);
    }

    public function testCustomTimeout(): void
    {
        $config = TimeoutConfig::of(seconds: 5.5, operationName: 'custom-op');

        self::assertSame(5.5, $config->durationSeconds);
        self::assertSame('custom-op', $config->operationName);
    }

    public function testWithFallback(): void
    {
        $fallback = fn() => 'fallback-result';
        $config = TimeoutConfig::fast()->withFallback($fallback);

        self::assertNotNull($config->fallback);
        self::assertSame('fallback-result', ($config->fallback)());
    }

    public function testWithOperationName(): void
    {
        $config = TimeoutConfig::fast()->withOperationName('new-name');

        self::assertSame('new-name', $config->operationName);
        self::assertSame(3.0, $config->durationSeconds);
    }

    public function testWithRetry(): void
    {
        $config = TimeoutConfig::fast()->withRetry(true);

        self::assertTrue($config->shouldRetry);
    }

    public function testRejectsNegativeDuration(): void
    {
        $this->expectException(\InvalidArgumentException::class);
        $this->expectExceptionMessage('Timeout duration must be positive');

        new TimeoutConfig(durationSeconds: -1.0);
    }

    public function testRejectsZeroDuration(): void
    {
        $this->expectException(\InvalidArgumentException::class);

        new TimeoutConfig(durationSeconds: 0.0);
    }
}
```

---

### SignalTimeoutExecutorTest.php

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Infrastructure\Resilience\Timeout;

use Domain\Shared\Timeout\TimeoutConfig;
use Domain\Shared\Timeout\TimeoutException;
use Infrastructure\Resilience\Timeout\SignalTimeoutExecutor;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;
use Psr\Log\NullLogger;

#[Group('unit')]
#[CoversClass(SignalTimeoutExecutor::class)]
final class SignalTimeoutExecutorTest extends TestCase
{
    private SignalTimeoutExecutor $executor;

    protected function setUp(): void
    {
        $this->executor = new SignalTimeoutExecutor(new NullLogger());

        if (!SignalTimeoutExecutor::isSupported()) {
            self::markTestSkipped('pcntl extension not available');
        }
    }

    public function testExecuteWithinTimeout(): void
    {
        $config = TimeoutConfig::of(seconds: 2.0, operationName: 'fast-operation');

        $result = $this->executor->execute(
            operation: fn() => 'success',
            config: $config,
        );

        self::assertSame('success', $result);
    }

    public function testThrowsTimeoutExceptionWhenExceeded(): void
    {
        $config = TimeoutConfig::of(seconds: 1.0, operationName: 'slow-operation');

        $this->expectException(TimeoutException::class);
        $this->expectExceptionMessage('Operation "slow-operation" timed out');

        $this->executor->execute(
            operation: fn() => sleep(3),
            config: $config,
        );
    }

    public function testExecutesFallbackOnTimeout(): void
    {
        $config = TimeoutConfig::of(seconds: 1.0, operationName: 'failing-op')
            ->withFallback(fn() => 'fallback-result');

        $result = $this->executor->execute(
            operation: fn() => sleep(3),
            config: $config,
        );

        self::assertSame('fallback-result', $result);
    }
}
```

---

### TimeoutExceptionTest.php

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\Shared\Timeout;

use Domain\Shared\Timeout\TimeoutException;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(TimeoutException::class)]
final class TimeoutExceptionTest extends TestCase
{
    public function testConstructorSetsProperties(): void
    {
        $exception = new TimeoutException(
            elapsedSeconds: 5.2,
            timeoutSeconds: 3.0,
            operationName: 'api-call',
        );

        self::assertSame(5.2, $exception->elapsedSeconds);
        self::assertSame(3.0, $exception->timeoutSeconds);
        self::assertSame('api-call', $exception->operationName);
    }

    public function testMessageFormat(): void
    {
        $exception = new TimeoutException(
            elapsedSeconds: 5.2,
            timeoutSeconds: 3.0,
            operationName: 'api-call',
        );

        self::assertStringContainsString('api-call', $exception->getMessage());
        self::assertStringContainsString('5.20', $exception->getMessage());
        self::assertStringContainsString('3.00', $exception->getMessage());
    }

    public function testToArray(): void
    {
        $exception = new TimeoutException(
            elapsedSeconds: 5.2,
            timeoutSeconds: 3.0,
            operationName: 'api-call',
        );

        $array = $exception->toArray();

        self::assertSame('api-call', $array['operation']);
        self::assertSame(5.2, $array['elapsed_seconds']);
        self::assertSame(3.0, $array['timeout_seconds']);
        self::assertStringContainsString('timed out', $array['message']);
    }

    public function testWithPreviousException(): void
    {
        $previous = new \RuntimeException('Original error');
        $exception = new TimeoutException(
            elapsedSeconds: 2.0,
            timeoutSeconds: 1.0,
            operationName: 'test',
            previous: $previous,
        );

        self::assertSame($previous, $exception->getPrevious());
    }
}
```

---

## Summary

All examples demonstrate:
- Signal-based timeout for CLI operations
- Stream-based timeout for I/O operations
- Fallback strategies for graceful degradation
- Composition with other resilience patterns
- Proper logging and monitoring
- Complete test coverage with PHPUnit attributes
