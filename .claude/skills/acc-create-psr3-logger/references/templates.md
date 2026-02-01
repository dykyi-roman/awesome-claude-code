# PSR-3 Logger Templates

## Stream Logger

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Logger;

use DateTimeImmutable;
use Psr\Log\LoggerInterface;
use Psr\Log\LogLevel;
use Stringable;

final class StreamLogger implements LoggerInterface
{
    /** @var resource */
    private $stream;

    public function __construct(
        string $streamUri = 'php://stdout',
        private readonly string $minLevel = LogLevel::DEBUG,
    ) {
        $stream = fopen($streamUri, 'a');

        if ($stream === false) {
            throw new \RuntimeException("Cannot open stream: {$streamUri}");
        }

        $this->stream = $stream;
    }

    public function __destruct()
    {
        if (is_resource($this->stream)) {
            fclose($this->stream);
        }
    }

    public function emergency(string|Stringable $message, array $context = []): void
    {
        $this->log(LogLevel::EMERGENCY, $message, $context);
    }

    public function alert(string|Stringable $message, array $context = []): void
    {
        $this->log(LogLevel::ALERT, $message, $context);
    }

    public function critical(string|Stringable $message, array $context = []): void
    {
        $this->log(LogLevel::CRITICAL, $message, $context);
    }

    public function error(string|Stringable $message, array $context = []): void
    {
        $this->log(LogLevel::ERROR, $message, $context);
    }

    public function warning(string|Stringable $message, array $context = []): void
    {
        $this->log(LogLevel::WARNING, $message, $context);
    }

    public function notice(string|Stringable $message, array $context = []): void
    {
        $this->log(LogLevel::NOTICE, $message, $context);
    }

    public function info(string|Stringable $message, array $context = []): void
    {
        $this->log(LogLevel::INFO, $message, $context);
    }

    public function debug(string|Stringable $message, array $context = []): void
    {
        $this->log(LogLevel::DEBUG, $message, $context);
    }

    public function log(mixed $level, string|Stringable $message, array $context = []): void
    {
        $timestamp = (new DateTimeImmutable())->format('Y-m-d H:i:s.u');
        $interpolated = $this->interpolate((string) $message, $context);

        $entry = sprintf("[%s] %s: %s\n", $timestamp, strtoupper($level), $interpolated);

        fwrite($this->stream, $entry);
    }

    private function interpolate(string $message, array $context): string
    {
        $replace = [];

        foreach ($context as $key => $value) {
            if (is_string($value) || $value instanceof Stringable) {
                $replace['{' . $key . '}'] = (string) $value;
            }
        }

        return strtr($message, $replace);
    }
}
```

## Array Logger (for testing)

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Logger;

use DateTimeImmutable;
use Psr\Log\LoggerInterface;
use Stringable;

final class ArrayLogger implements LoggerInterface
{
    /** @var array<int, array{level: string, message: string, context: array, timestamp: string}> */
    private array $logs = [];

    public function emergency(string|Stringable $message, array $context = []): void
    {
        $this->log('emergency', $message, $context);
    }

    public function alert(string|Stringable $message, array $context = []): void
    {
        $this->log('alert', $message, $context);
    }

    public function critical(string|Stringable $message, array $context = []): void
    {
        $this->log('critical', $message, $context);
    }

    public function error(string|Stringable $message, array $context = []): void
    {
        $this->log('error', $message, $context);
    }

    public function warning(string|Stringable $message, array $context = []): void
    {
        $this->log('warning', $message, $context);
    }

    public function notice(string|Stringable $message, array $context = []): void
    {
        $this->log('notice', $message, $context);
    }

    public function info(string|Stringable $message, array $context = []): void
    {
        $this->log('info', $message, $context);
    }

    public function debug(string|Stringable $message, array $context = []): void
    {
        $this->log('debug', $message, $context);
    }

    public function log(mixed $level, string|Stringable $message, array $context = []): void
    {
        $this->logs[] = [
            'level' => (string) $level,
            'message' => (string) $message,
            'context' => $context,
            'timestamp' => (new DateTimeImmutable())->format('Y-m-d H:i:s.u'),
        ];
    }

    /** @return array<int, array{level: string, message: string, context: array, timestamp: string}> */
    public function getLogs(): array
    {
        return $this->logs;
    }

    public function clear(): void
    {
        $this->logs = [];
    }

    public function hasLoggedLevel(string $level): bool
    {
        foreach ($this->logs as $log) {
            if ($log['level'] === $level) {
                return true;
            }
        }

        return false;
    }

    public function hasLoggedMessage(string $message): bool
    {
        foreach ($this->logs as $log) {
            if (str_contains($log['message'], $message)) {
                return true;
            }
        }

        return false;
    }
}
```

## Composite Logger

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Logger;

use Psr\Log\LoggerInterface;
use Stringable;

final readonly class CompositeLogger implements LoggerInterface
{
    /** @var LoggerInterface[] */
    private array $loggers;

    public function __construct(LoggerInterface ...$loggers)
    {
        $this->loggers = $loggers;
    }

    public function emergency(string|Stringable $message, array $context = []): void
    {
        $this->log('emergency', $message, $context);
    }

    public function alert(string|Stringable $message, array $context = []): void
    {
        $this->log('alert', $message, $context);
    }

    public function critical(string|Stringable $message, array $context = []): void
    {
        $this->log('critical', $message, $context);
    }

    public function error(string|Stringable $message, array $context = []): void
    {
        $this->log('error', $message, $context);
    }

    public function warning(string|Stringable $message, array $context = []): void
    {
        $this->log('warning', $message, $context);
    }

    public function notice(string|Stringable $message, array $context = []): void
    {
        $this->log('notice', $message, $context);
    }

    public function info(string|Stringable $message, array $context = []): void
    {
        $this->log('info', $message, $context);
    }

    public function debug(string|Stringable $message, array $context = []): void
    {
        $this->log('debug', $message, $context);
    }

    public function log(mixed $level, string|Stringable $message, array $context = []): void
    {
        foreach ($this->loggers as $logger) {
            $logger->log($level, $message, $context);
        }
    }
}
```

## JSON Logger

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Logger;

use DateTimeImmutable;
use Psr\Log\LoggerInterface;
use Stringable;

final class JsonLogger implements LoggerInterface
{
    public function __construct(
        private readonly string $logFile,
    ) {
    }

    public function emergency(string|Stringable $message, array $context = []): void
    {
        $this->log('emergency', $message, $context);
    }

    public function alert(string|Stringable $message, array $context = []): void
    {
        $this->log('alert', $message, $context);
    }

    public function critical(string|Stringable $message, array $context = []): void
    {
        $this->log('critical', $message, $context);
    }

    public function error(string|Stringable $message, array $context = []): void
    {
        $this->log('error', $message, $context);
    }

    public function warning(string|Stringable $message, array $context = []): void
    {
        $this->log('warning', $message, $context);
    }

    public function notice(string|Stringable $message, array $context = []): void
    {
        $this->log('notice', $message, $context);
    }

    public function info(string|Stringable $message, array $context = []): void
    {
        $this->log('info', $message, $context);
    }

    public function debug(string|Stringable $message, array $context = []): void
    {
        $this->log('debug', $message, $context);
    }

    public function log(mixed $level, string|Stringable $message, array $context = []): void
    {
        $entry = [
            'timestamp' => (new DateTimeImmutable())->format(DateTimeImmutable::RFC3339_EXTENDED),
            'level' => (string) $level,
            'message' => (string) $message,
            'context' => $context,
        ];

        file_put_contents(
            $this->logFile,
            json_encode($entry, JSON_UNESCAPED_SLASHES) . "\n",
            FILE_APPEND | LOCK_EX,
        );
    }
}
```
