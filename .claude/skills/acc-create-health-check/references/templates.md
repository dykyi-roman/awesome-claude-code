# Health Check Pattern Templates

## HealthCheckInterface

**File:** `src/Domain/Shared/Health/HealthCheckInterface.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\Health;

interface HealthCheckInterface
{
    public function name(): string;

    public function check(): HealthCheckResult;
}
```

---

## HealthStatus Enum

**File:** `src/Domain/Shared/Health/HealthStatus.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\Health;

enum HealthStatus: string
{
    case Healthy = 'healthy';
    case Degraded = 'degraded';
    case Unhealthy = 'unhealthy';

    public function isOperational(): bool
    {
        return $this !== self::Unhealthy;
    }

    public function merge(self $other): self
    {
        $priority = [
            self::Unhealthy->value => 2,
            self::Degraded->value => 1,
            self::Healthy->value => 0,
        ];

        return match (true) {
            $priority[$this->value] >= $priority[$other->value] => $this,
            default => $other,
        };
    }
}
```

---

## HealthCheckResult

**File:** `src/Domain/Shared/Health/HealthCheckResult.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\Health;

final readonly class HealthCheckResult
{
    /**
     * @param array<string, mixed> $details
     */
    public function __construct(
        public string $name,
        public HealthStatus $status,
        public float $durationMs,
        public array $details = [],
    ) {}

    public static function healthy(string $name, float $durationMs): self
    {
        return new self(
            name: $name,
            status: HealthStatus::Healthy,
            durationMs: $durationMs,
        );
    }

    public static function unhealthy(string $name, float $durationMs, string $error): self
    {
        return new self(
            name: $name,
            status: HealthStatus::Unhealthy,
            durationMs: $durationMs,
            details: ['error' => $error],
        );
    }

    public static function degraded(string $name, float $durationMs, string $reason): self
    {
        return new self(
            name: $name,
            status: HealthStatus::Degraded,
            durationMs: $durationMs,
            details: ['reason' => $reason],
        );
    }

    /**
     * @return array{name: string, status: string, duration_ms: float, details: array<string, mixed>}
     */
    public function toArray(): array
    {
        return [
            'name' => $this->name,
            'status' => $this->status->value,
            'duration_ms' => $this->durationMs,
            'details' => $this->details,
        ];
    }
}
```

---

## DatabaseHealthCheck

**File:** `src/Infrastructure/Health/DatabaseHealthCheck.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Health;

use Domain\Shared\Health\HealthCheckInterface;
use Domain\Shared\Health\HealthCheckResult;

final readonly class DatabaseHealthCheck implements HealthCheckInterface
{
    public function __construct(
        private \PDO $pdo,
    ) {}

    public function name(): string
    {
        return 'database';
    }

    public function check(): HealthCheckResult
    {
        $start = microtime(true);

        try {
            $this->pdo->query('SELECT 1');
            $durationMs = (microtime(true) - $start) * 1000;

            return HealthCheckResult::healthy($this->name(), $durationMs);
        } catch (\Throwable $e) {
            $durationMs = (microtime(true) - $start) * 1000;

            return HealthCheckResult::unhealthy($this->name(), $durationMs, $e->getMessage());
        }
    }
}
```

---

## RedisHealthCheck

**File:** `src/Infrastructure/Health/RedisHealthCheck.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Health;

use Domain\Shared\Health\HealthCheckInterface;
use Domain\Shared\Health\HealthCheckResult;

final readonly class RedisHealthCheck implements HealthCheckInterface
{
    public function __construct(
        private \Redis $redis,
    ) {}

    public function name(): string
    {
        return 'redis';
    }

    public function check(): HealthCheckResult
    {
        $start = microtime(true);

        try {
            $this->redis->ping();
            $durationMs = (microtime(true) - $start) * 1000;

            return HealthCheckResult::healthy($this->name(), $durationMs);
        } catch (\Throwable $e) {
            $durationMs = (microtime(true) - $start) * 1000;

            return HealthCheckResult::unhealthy($this->name(), $durationMs, $e->getMessage());
        }
    }
}
```

---

## RabbitMqHealthCheck

**File:** `src/Infrastructure/Health/RabbitMqHealthCheck.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Health;

use Domain\Shared\Health\HealthCheckInterface;
use Domain\Shared\Health\HealthCheckResult;
use PhpAmqpLib\Connection\AMQPStreamConnection;

final readonly class RabbitMqHealthCheck implements HealthCheckInterface
{
    public function __construct(
        private AMQPStreamConnection $connection,
    ) {}

    public function name(): string
    {
        return 'rabbitmq';
    }

    public function check(): HealthCheckResult
    {
        $start = microtime(true);

        try {
            if ($this->connection->isConnected()) {
                $durationMs = (microtime(true) - $start) * 1000;

                return HealthCheckResult::healthy($this->name(), $durationMs);
            }

            $durationMs = (microtime(true) - $start) * 1000;

            return HealthCheckResult::unhealthy($this->name(), $durationMs, 'Not connected');
        } catch (\Throwable $e) {
            $durationMs = (microtime(true) - $start) * 1000;

            return HealthCheckResult::unhealthy($this->name(), $durationMs, $e->getMessage());
        }
    }
}
```

---

## HealthCheckRunner

**File:** `src/Infrastructure/Health/HealthCheckRunner.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Health;

use Domain\Shared\Health\HealthCheckInterface;
use Domain\Shared\Health\HealthCheckResult;
use Domain\Shared\Health\HealthStatus;

final readonly class HealthCheckRunner
{
    /**
     * @param iterable<HealthCheckInterface> $checks
     */
    public function __construct(
        private iterable $checks,
        private int $timeoutSeconds = 5,
    ) {}

    /**
     * @return array{status: HealthStatus, checks: array<string, HealthCheckResult>}
     */
    public function run(): array
    {
        $overallStatus = HealthStatus::Healthy;
        $results = [];

        foreach ($this->checks as $check) {
            try {
                $result = $check->check();
            } catch (\Throwable $e) {
                $result = HealthCheckResult::unhealthy(
                    $check->name(),
                    0.0,
                    $e->getMessage(),
                );
            }

            $results[$check->name()] = $result;
            $overallStatus = $overallStatus->merge($result->status);
        }

        return [
            'status' => $overallStatus,
            'checks' => $results,
        ];
    }
}
```

---

## HealthCheckAction

**File:** `src/Presentation/Api/Action/HealthCheckAction.php`

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\Action;

use Domain\Shared\Health\HealthStatus;
use Infrastructure\Health\HealthCheckRunner;
use Psr\Http\Message\ResponseFactoryInterface;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Message\StreamFactoryInterface;
use Psr\Http\Server\RequestHandlerInterface;

final readonly class HealthCheckAction implements RequestHandlerInterface
{
    public function __construct(
        private HealthCheckRunner $runner,
        private ResponseFactoryInterface $responseFactory,
        private StreamFactoryInterface $streamFactory,
    ) {}

    public function handle(ServerRequestInterface $request): ResponseInterface
    {
        $result = $this->runner->run();

        /** @var HealthStatus $status */
        $status = $result['status'];
        $checks = $result['checks'];

        $body = [
            'status' => $status->value,
            'checks' => array_map(
                static fn($check) => $check->toArray(),
                $checks,
            ),
        ];

        $statusCode = $status === HealthStatus::Unhealthy ? 503 : 200;

        $stream = $this->streamFactory->createStream(
            json_encode($body, JSON_THROW_ON_ERROR | JSON_UNESCAPED_SLASHES),
        );

        return $this->responseFactory->createResponse($statusCode)
            ->withHeader('Content-Type', 'application/json')
            ->withBody($stream);
    }
}
```
