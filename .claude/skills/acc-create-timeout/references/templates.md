# Timeout Pattern PHP Templates

Complete implementation templates for all Timeout pattern components.

---

## Domain Layer

### TimeoutConfig.php

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\Timeout;

final readonly class TimeoutConfig
{
    public function __construct(
        public float $durationSeconds,
        public ?\Closure $fallback = null,
        public bool $shouldRetry = false,
        public string $operationName = 'unknown',
    ) {
        if ($durationSeconds <= 0) {
            throw new \InvalidArgumentException('Timeout duration must be positive');
        }
    }

    public static function fast(): self
    {
        return new self(durationSeconds: 3.0, operationName: 'fast-operation');
    }

    public static function standard(): self
    {
        return new self(durationSeconds: 10.0, operationName: 'standard-operation');
    }

    public static function slow(): self
    {
        return new self(durationSeconds: 30.0, operationName: 'slow-operation');
    }

    public static function of(float $seconds, string $operationName = 'custom-operation'): self
    {
        return new self(durationSeconds: $seconds, operationName: $operationName);
    }

    public function withFallback(callable $fallback): self
    {
        return new self(
            durationSeconds: $this->durationSeconds,
            fallback: $fallback(...),
            shouldRetry: $this->shouldRetry,
            operationName: $this->operationName,
        );
    }

    public function withOperationName(string $operationName): self
    {
        return new self(
            durationSeconds: $this->durationSeconds,
            fallback: $this->fallback,
            shouldRetry: $this->shouldRetry,
            operationName: $operationName,
        );
    }

    public function withRetry(bool $shouldRetry = true): self
    {
        return new self(
            durationSeconds: $this->durationSeconds,
            fallback: $this->fallback,
            shouldRetry: $shouldRetry,
            operationName: $this->operationName,
        );
    }
}
```

---

### TimeoutInterface.php

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\Timeout;

interface TimeoutInterface
{
    /**
     * Execute operation with timeout.
     *
     * @template T
     * @param callable(): T $operation
     * @return T
     * @throws TimeoutException
     */
    public function execute(callable $operation, TimeoutConfig $config): mixed;
}
```

---

### TimeoutException.php

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\Timeout;

final class TimeoutException extends \RuntimeException
{
    public function __construct(
        public readonly float $elapsedSeconds,
        public readonly float $timeoutSeconds,
        public readonly string $operationName,
        ?\Throwable $previous = null,
    ) {
        parent::__construct(
            sprintf(
                'Operation "%s" timed out after %.2fs (limit: %.2fs)',
                $operationName,
                $elapsedSeconds,
                $timeoutSeconds
            ),
            0,
            $previous,
        );
    }

    public function toArray(): array
    {
        return [
            'operation' => $this->operationName,
            'elapsed_seconds' => $this->elapsedSeconds,
            'timeout_seconds' => $this->timeoutSeconds,
            'message' => $this->getMessage(),
        ];
    }
}
```

---

## Infrastructure Layer

### SignalTimeoutExecutor.php

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Resilience\Timeout;

use Domain\Shared\Timeout\TimeoutConfig;
use Domain\Shared\Timeout\TimeoutException;
use Domain\Shared\Timeout\TimeoutInterface;
use Psr\Log\LoggerInterface;

final readonly class SignalTimeoutExecutor implements TimeoutInterface
{
    public function __construct(
        private LoggerInterface $logger,
    ) {}

    public function execute(callable $operation, TimeoutConfig $config): mixed
    {
        if (!self::isSupported()) {
            $this->logger->warning('pcntl extension not available, timeout will not be enforced');
            return $operation();
        }

        $startTime = microtime(true);
        $previousHandler = null;
        $timedOut = false;

        $handler = function () use (&$timedOut): void {
            $timedOut = true;
        };

        try {
            $previousHandler = pcntl_signal(SIGALRM, $handler);
            pcntl_alarm((int) ceil($config->durationSeconds));

            $result = $operation();

            if ($timedOut) {
                throw new TimeoutException(
                    elapsedSeconds: microtime(true) - $startTime,
                    timeoutSeconds: $config->durationSeconds,
                    operationName: $config->operationName,
                );
            }

            return $result;
        } catch (\Throwable $e) {
            $elapsed = microtime(true) - $startTime;

            if ($timedOut || $elapsed >= $config->durationSeconds) {
                $this->logger->warning('Operation timed out', [
                    'operation' => $config->operationName,
                    'elapsed' => $elapsed,
                    'timeout' => $config->durationSeconds,
                ]);

                if ($config->fallback !== null) {
                    return ($config->fallback)();
                }

                throw new TimeoutException(
                    elapsedSeconds: $elapsed,
                    timeoutSeconds: $config->durationSeconds,
                    operationName: $config->operationName,
                    previous: $e,
                );
            }

            throw $e;
        } finally {
            pcntl_alarm(0);
            if ($previousHandler !== null) {
                pcntl_signal(SIGALRM, $previousHandler);
            }
        }
    }

    public static function isSupported(): bool
    {
        return extension_loaded('pcntl') && function_exists('pcntl_alarm') && function_exists('pcntl_signal');
    }
}
```

---

### StreamTimeoutExecutor.php

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Resilience\Timeout;

use Domain\Shared\Timeout\TimeoutConfig;
use Domain\Shared\Timeout\TimeoutException;

final readonly class StreamTimeoutExecutor
{
    /**
     * @template T
     * @param resource $stream
     * @param callable(resource): T $operation
     * @return T
     * @throws TimeoutException
     */
    public function executeOnStream(
        mixed $stream,
        callable $operation,
        TimeoutConfig $config
    ): mixed {
        if (!is_resource($stream)) {
            throw new \InvalidArgumentException('Expected stream resource');
        }

        $startTime = microtime(true);
        $seconds = (int) floor($config->durationSeconds);
        $microseconds = (int) (($config->durationSeconds - $seconds) * 1_000_000);

        stream_set_timeout($stream, $seconds, $microseconds);

        $result = $operation($stream);

        $metadata = stream_get_meta_data($stream);
        if ($metadata['timed_out'] ?? false) {
            $elapsed = microtime(true) - $startTime;

            if ($config->fallback !== null) {
                return ($config->fallback)();
            }

            throw new TimeoutException(
                elapsedSeconds: $elapsed,
                timeoutSeconds: $config->durationSeconds,
                operationName: $config->operationName,
            );
        }

        return $result;
    }
}
```

---

### NullTimeoutExecutor.php

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Resilience\Timeout;

use Domain\Shared\Timeout\TimeoutConfig;
use Domain\Shared\Timeout\TimeoutInterface;
use Psr\Log\LoggerInterface;

final readonly class NullTimeoutExecutor implements TimeoutInterface
{
    public function __construct(
        private LoggerInterface $logger,
    ) {}

    public function execute(callable $operation, TimeoutConfig $config): mixed
    {
        $this->logger->debug('Using NullTimeoutExecutor, timeout will not be enforced', [
            'operation' => $config->operationName,
            'timeout' => $config->durationSeconds,
        ]);

        return $operation();
    }
}
```

---

### TimeoutExecutorFactory.php

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Resilience\Timeout;

use Domain\Shared\Timeout\TimeoutInterface;
use Psr\Log\LoggerInterface;

final readonly class TimeoutExecutorFactory
{
    public function __construct(
        private LoggerInterface $logger,
    ) {}

    public function create(): TimeoutInterface
    {
        if (SignalTimeoutExecutor::isSupported()) {
            return new SignalTimeoutExecutor($this->logger);
        }

        $this->logger->warning('pcntl extension not available, using NullTimeoutExecutor');
        return new NullTimeoutExecutor($this->logger);
    }
}
```

---

## Presentation Layer

### TimeoutMiddleware.php

```php
<?php

declare(strict_types=1);

namespace Presentation\Middleware;

use Domain\Shared\Timeout\TimeoutConfig;
use Domain\Shared\Timeout\TimeoutInterface;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\MiddlewareInterface;
use Psr\Http\Server\RequestHandlerInterface;

final readonly class TimeoutMiddleware implements MiddlewareInterface
{
    public function __construct(
        private TimeoutInterface $timeout,
        private float $defaultTimeoutSeconds = 30.0,
    ) {}

    public function process(ServerRequestInterface $request, RequestHandlerInterface $handler): ResponseInterface
    {
        $timeoutSeconds = (float) ($request->getAttribute('timeout') ?? $this->defaultTimeoutSeconds);

        $config = TimeoutConfig::of(
            seconds: $timeoutSeconds,
            operationName: sprintf('%s %s', $request->getMethod(), (string) $request->getUri()),
        );

        return $this->timeout->execute(
            operation: fn() => $handler->handle($request),
            config: $config,
        );
    }
}
```

---

## DI Configuration

### services.yaml (Symfony)

```yaml
services:
    Domain\Shared\Timeout\TimeoutInterface:
        factory: ['@Infrastructure\Resilience\Timeout\TimeoutExecutorFactory', 'create']

    Infrastructure\Resilience\Timeout\TimeoutExecutorFactory:
        arguments:
            $logger: '@Psr\Log\LoggerInterface'

    Infrastructure\Resilience\Timeout\StreamTimeoutExecutor: ~

    Presentation\Middleware\TimeoutMiddleware:
        arguments:
            $timeout: '@Domain\Shared\Timeout\TimeoutInterface'
            $defaultTimeoutSeconds: 30.0
        tags:
            - { name: 'middleware', priority: 100 }
```

---

## Summary

All components follow:
- `declare(strict_types=1)` at top
- `final readonly` for value objects and services
- Constructor property promotion
- Proper exception handling with context
- PSR-12 coding standard
- No comments (self-documenting code)
