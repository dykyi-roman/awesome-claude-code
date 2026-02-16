# Health Check Pattern Examples

## DI Container Wiring

**File:** `config/health.php`

```php
<?php

declare(strict_types=1);

use Domain\Shared\Health\HealthCheckInterface;
use Infrastructure\Health\DatabaseHealthCheck;
use Infrastructure\Health\HealthCheckRunner;
use Infrastructure\Health\RabbitMqHealthCheck;
use Infrastructure\Health\RedisHealthCheck;
use Psr\Container\ContainerInterface;

return [
    HealthCheckRunner::class => static function (ContainerInterface $container): HealthCheckRunner {
        /** @var iterable<HealthCheckInterface> $checks */
        $checks = [
            $container->get(DatabaseHealthCheck::class),
            $container->get(RedisHealthCheck::class),
            $container->get(RabbitMqHealthCheck::class),
        ];

        return new HealthCheckRunner(
            checks: $checks,
            timeoutSeconds: 5,
        );
    },

    DatabaseHealthCheck::class => static function (ContainerInterface $container): DatabaseHealthCheck {
        return new DatabaseHealthCheck(
            pdo: $container->get(\PDO::class),
        );
    },

    RedisHealthCheck::class => static function (ContainerInterface $container): RedisHealthCheck {
        return new RedisHealthCheck(
            redis: $container->get(\Redis::class),
        );
    },

    RabbitMqHealthCheck::class => static function (ContainerInterface $container): RabbitMqHealthCheck {
        return new RabbitMqHealthCheck(
            connection: $container->get(\PhpAmqpLib\Connection\AMQPStreamConnection::class),
        );
    },
];
```

---

## Custom ElasticsearchHealthCheck

**File:** `src/Infrastructure/Health/ElasticsearchHealthCheck.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Health;

use Domain\Shared\Health\HealthCheckInterface;
use Domain\Shared\Health\HealthCheckResult;
use Elastic\Elasticsearch\Client;

final readonly class ElasticsearchHealthCheck implements HealthCheckInterface
{
    public function __construct(
        private Client $client,
    ) {}

    public function name(): string
    {
        return 'elasticsearch';
    }

    public function check(): HealthCheckResult
    {
        $start = microtime(true);

        try {
            $response = $this->client->cluster()->health();
            $durationMs = (microtime(true) - $start) * 1000;

            $clusterStatus = $response['status'] ?? 'unknown';

            return match ($clusterStatus) {
                'green' => HealthCheckResult::healthy($this->name(), $durationMs),
                'yellow' => HealthCheckResult::degraded($this->name(), $durationMs, 'Cluster status is yellow'),
                default => HealthCheckResult::unhealthy($this->name(), $durationMs, "Cluster status: $clusterStatus"),
            };
        } catch (\Throwable $e) {
            $durationMs = (microtime(true) - $start) * 1000;

            return HealthCheckResult::unhealthy($this->name(), $durationMs, $e->getMessage());
        }
    }
}
```

---

## Unit Tests

### HealthCheckResultTest

**File:** `tests/Unit/Domain/Shared/Health/HealthCheckResultTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\Shared\Health;

use Domain\Shared\Health\HealthCheckResult;
use Domain\Shared\Health\HealthStatus;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(HealthCheckResult::class)]
final class HealthCheckResultTest extends TestCase
{
    public function testConstructsWithAllProperties(): void
    {
        $result = new HealthCheckResult(
            name: 'database',
            status: HealthStatus::Healthy,
            durationMs: 1.23,
            details: ['version' => '15.4'],
        );

        self::assertSame('database', $result->name);
        self::assertSame(HealthStatus::Healthy, $result->status);
        self::assertSame(1.23, $result->durationMs);
        self::assertSame(['version' => '15.4'], $result->details);
    }

    public function testHealthyFactoryMethod(): void
    {
        $result = HealthCheckResult::healthy('redis', 0.45);

        self::assertSame('redis', $result->name);
        self::assertSame(HealthStatus::Healthy, $result->status);
        self::assertSame(0.45, $result->durationMs);
        self::assertSame([], $result->details);
    }

    public function testUnhealthyFactoryMethod(): void
    {
        $result = HealthCheckResult::unhealthy('database', 5.0, 'Connection refused');

        self::assertSame('database', $result->name);
        self::assertSame(HealthStatus::Unhealthy, $result->status);
        self::assertSame(5.0, $result->durationMs);
        self::assertSame(['error' => 'Connection refused'], $result->details);
    }

    public function testDegradedFactoryMethod(): void
    {
        $result = HealthCheckResult::degraded('rabbitmq', 15.7, 'High latency detected');

        self::assertSame('rabbitmq', $result->name);
        self::assertSame(HealthStatus::Degraded, $result->status);
        self::assertSame(15.7, $result->durationMs);
        self::assertSame(['reason' => 'High latency detected'], $result->details);
    }

    public function testToArrayReturnsExpectedStructure(): void
    {
        $result = HealthCheckResult::unhealthy('database', 3.21, 'Timeout');

        $array = $result->toArray();

        self::assertSame([
            'name' => 'database',
            'status' => 'unhealthy',
            'duration_ms' => 3.21,
            'details' => ['error' => 'Timeout'],
        ], $array);
    }
}
```

---

### HealthCheckRunnerTest

**File:** `tests/Unit/Infrastructure/Health/HealthCheckRunnerTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Infrastructure\Health;

use Domain\Shared\Health\HealthCheckInterface;
use Domain\Shared\Health\HealthCheckResult;
use Domain\Shared\Health\HealthStatus;
use Infrastructure\Health\HealthCheckRunner;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(HealthCheckRunner::class)]
final class HealthCheckRunnerTest extends TestCase
{
    public function testAllHealthyReturnsOverallHealthy(): void
    {
        $checks = [
            $this->createCheck('database', HealthCheckResult::healthy('database', 1.0)),
            $this->createCheck('redis', HealthCheckResult::healthy('redis', 0.5)),
        ];

        $runner = new HealthCheckRunner($checks);
        $result = $runner->run();

        self::assertSame(HealthStatus::Healthy, $result['status']);
        self::assertCount(2, $result['checks']);
    }

    public function testOneUnhealthyReturnsOverallUnhealthy(): void
    {
        $checks = [
            $this->createCheck('database', HealthCheckResult::healthy('database', 1.0)),
            $this->createCheck('redis', HealthCheckResult::unhealthy('redis', 5.0, 'Connection refused')),
        ];

        $runner = new HealthCheckRunner($checks);
        $result = $runner->run();

        self::assertSame(HealthStatus::Unhealthy, $result['status']);
    }

    public function testOneDegradedReturnsOverallDegraded(): void
    {
        $checks = [
            $this->createCheck('database', HealthCheckResult::healthy('database', 1.0)),
            $this->createCheck('rabbitmq', HealthCheckResult::degraded('rabbitmq', 15.0, 'Slow')),
        ];

        $runner = new HealthCheckRunner($checks);
        $result = $runner->run();

        self::assertSame(HealthStatus::Degraded, $result['status']);
    }

    public function testExceptionInCheckReturnsUnhealthyResult(): void
    {
        $failingCheck = $this->createMock(HealthCheckInterface::class);
        $failingCheck->method('name')->willReturn('broken');
        $failingCheck->method('check')->willThrowException(new \RuntimeException('Connection lost'));

        $runner = new HealthCheckRunner([$failingCheck]);
        $result = $runner->run();

        self::assertSame(HealthStatus::Unhealthy, $result['status']);
        self::assertArrayHasKey('broken', $result['checks']);
        self::assertSame(HealthStatus::Unhealthy, $result['checks']['broken']->status);
    }

    private function createCheck(string $name, HealthCheckResult $checkResult): HealthCheckInterface
    {
        $check = $this->createMock(HealthCheckInterface::class);
        $check->method('name')->willReturn($name);
        $check->method('check')->willReturn($checkResult);

        return $check;
    }
}
```

---

### HealthCheckActionTest

**File:** `tests/Unit/Presentation/Api/Action/HealthCheckActionTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Presentation\Api\Action;

use Domain\Shared\Health\HealthCheckResult;
use Domain\Shared\Health\HealthStatus;
use Infrastructure\Health\HealthCheckRunner;
use Presentation\Api\Action\HealthCheckAction;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;
use Psr\Http\Message\ResponseFactoryInterface;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Message\StreamFactoryInterface;
use Psr\Http\Message\StreamInterface;

#[Group('unit')]
#[CoversClass(HealthCheckAction::class)]
final class HealthCheckActionTest extends TestCase
{
    public function testHealthyReturns200(): void
    {
        $runner = $this->createMock(HealthCheckRunner::class);
        $runner->method('run')->willReturn([
            'status' => HealthStatus::Healthy,
            'checks' => [
                'database' => HealthCheckResult::healthy('database', 1.0),
            ],
        ]);

        $action = $this->createAction($runner);
        $response = $action->handle($this->createMock(ServerRequestInterface::class));

        self::assertSame(200, $response->getStatusCode());
    }

    public function testUnhealthyReturns503(): void
    {
        $runner = $this->createMock(HealthCheckRunner::class);
        $runner->method('run')->willReturn([
            'status' => HealthStatus::Unhealthy,
            'checks' => [
                'database' => HealthCheckResult::unhealthy('database', 5.0, 'Down'),
            ],
        ]);

        $action = $this->createAction($runner);
        $response = $action->handle($this->createMock(ServerRequestInterface::class));

        self::assertSame(503, $response->getStatusCode());
    }

    public function testResponseIsJson(): void
    {
        $runner = $this->createMock(HealthCheckRunner::class);
        $runner->method('run')->willReturn([
            'status' => HealthStatus::Healthy,
            'checks' => [
                'redis' => HealthCheckResult::healthy('redis', 0.5),
            ],
        ]);

        $action = $this->createAction($runner);
        $response = $action->handle($this->createMock(ServerRequestInterface::class));

        self::assertSame(['application/json'], $response->getHeader('Content-Type'));

        $body = json_decode((string) $response->getBody(), true, 512, JSON_THROW_ON_ERROR);
        self::assertSame('healthy', $body['status']);
        self::assertArrayHasKey('redis', $body['checks']);
    }

    private function createAction(HealthCheckRunner $runner): HealthCheckAction
    {
        $stream = $this->createMock(StreamInterface::class);
        $stream->method('__toString')->willReturnCallback(
            static fn() => $stream->content ?? '',
        );

        $streamFactory = $this->createMock(StreamFactoryInterface::class);
        $streamFactory->method('createStream')->willReturnCallback(
            static function (string $content) use ($stream): StreamInterface {
                $stream->content = $content;
                $stream->method('__toString')->willReturn($content);
                return $stream;
            },
        );

        $response = $this->createMock(ResponseInterface::class);
        $response->method('withHeader')->willReturnSelf();
        $response->method('withBody')->willReturnSelf();
        $response->method('getStatusCode')->willReturn(200);
        $response->method('getBody')->willReturn($stream);
        $response->method('getHeader')->willReturn(['application/json']);

        $responseFactory = $this->createMock(ResponseFactoryInterface::class);
        $responseFactory->method('createResponse')->willReturnCallback(
            static function (int $statusCode) use ($response, $stream): ResponseInterface {
                $resp = new class($statusCode, $stream) implements ResponseInterface {
                    private array $headers = [];

                    public function __construct(
                        private readonly int $statusCode,
                        private StreamInterface $body,
                    ) {}

                    public function getStatusCode(): int { return $this->statusCode; }
                    public function getBody(): StreamInterface { return $this->body; }
                    public function withHeader(string $name, $value): static
                    {
                        $clone = clone $this;
                        $clone->headers[$name] = (array) $value;
                        return $clone;
                    }
                    public function withBody(StreamInterface $body): static
                    {
                        $clone = clone $this;
                        $clone->body = $body;
                        return $clone;
                    }
                    public function getHeader(string $name): array { return $this->headers[$name] ?? []; }
                    public function getProtocolVersion(): string { return '1.1'; }
                    public function withProtocolVersion(string $version): static { return $this; }
                    public function getHeaders(): array { return $this->headers; }
                    public function hasHeader(string $name): bool { return isset($this->headers[$name]); }
                    public function getHeaderLine(string $name): string { return implode(', ', $this->getHeader($name)); }
                    public function withAddedHeader(string $name, $value): static { return $this; }
                    public function withoutHeader(string $name): static { return $this; }
                    public function getReasonPhrase(): string { return ''; }
                    public function withStatus(int $code, string $reasonPhrase = ''): static { return $this; }
                };

                return $resp;
            },
        );

        return new HealthCheckAction(
            runner: $runner,
            responseFactory: $responseFactory,
            streamFactory: $streamFactory,
        );
    }
}
```
