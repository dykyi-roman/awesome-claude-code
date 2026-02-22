---
name: check-12-factor-compliance
description: Analyzes PHP code for 12-Factor App compliance. Detects hardcoded configuration, file-based state, env-specific conditionals, non-streaming logs, and missing environment variable usage.
---

# 12-Factor App Compliance Check

Analyze PHP code for violations of the [12-Factor App](https://12factor.net/) methodology that hinder deployment, scalability, and operational excellence.

## Detection Patterns

### 1. Hardcoded Configuration (Factor III: Config)

```php
<?php

declare(strict_types=1);

// BAD: Configuration values embedded in source code
final class MailerConfig
{
    private string $smtpHost = 'smtp.gmail.com';
    private int $smtpPort = 587;
    private string $apiKey = 'sk-live-abc123xyz';
}

// BAD: Database credentials in code
final class DatabaseConfig
{
    public function getDsn(): string
    {
        return 'mysql:host=localhost;port=3306;dbname=myapp';
    }

    public function getUser(): string
    {
        return 'root';
    }

    public function getPassword(): string
    {
        return 'secret123';
    }
}

// GOOD: All configuration from environment variables
final readonly class MailerConfig
{
    public function __construct(
        private string $smtpHost,
        private int $smtpPort,
        private string $apiKey,
    ) {}

    public static function fromEnvironment(): self
    {
        return new self(
            smtpHost: self::requireEnv('SMTP_HOST'),
            smtpPort: (int) self::requireEnv('SMTP_PORT'),
            apiKey: self::requireEnv('MAILER_API_KEY'),
        );
    }

    private static function requireEnv(string $name): string
    {
        return getenv($name) ?: throw new \RuntimeException(
            sprintf('Environment variable %s is required', $name),
        );
    }
}
```

### 2. File-Based State (Factor VI: Processes)

```php
<?php

declare(strict_types=1);

// BAD: Persistent state in local filesystem
final class CounterService
{
    public function increment(string $key): int
    {
        $file = '/var/data/counters/' . $key . '.txt';
        $current = (int) file_get_contents($file);
        file_put_contents($file, (string) ($current + 1));

        return $current + 1;
        // State lost on container restart, inconsistent across instances
    }
}

// BAD: Cache stored in local files
final class FileCacheService
{
    public function get(string $key): mixed
    {
        $path = '/tmp/cache/' . md5($key);
        if (!file_exists($path)) {
            return null;
        }

        return unserialize(file_get_contents($path));
    }
}

// GOOD: State in external backing service
final readonly class CounterService
{
    public function __construct(
        private \Redis $redis,
    ) {}

    public function increment(string $key): int
    {
        return $this->redis->incr('counter:' . $key);
    }
}
```

### 3. Environment-Specific Conditionals (Factor X: Dev/Prod Parity)

```php
<?php

declare(strict_types=1);

// BAD: Behavior branches based on environment name
final class NotificationService
{
    public function send(Notification $notification): void
    {
        if (getenv('APP_ENV') === 'production') {
            $this->smsGateway->send($notification);
        } else {
            // Skip SMS in dev/staging
            error_log('SMS skipped: ' . $notification->message());
        }
    }
}

// BAD: Different logic per environment
if ($_SERVER['APP_ENV'] === 'production') {
    $cache = new RedisCache($redisHost);
} elseif ($_SERVER['APP_ENV'] === 'staging') {
    $cache = new FileCache('/tmp/cache');
} else {
    $cache = new ArrayCache();
}

// GOOD: Same code, different config per environment
// Use interfaces and inject implementation via DI container
final readonly class NotificationService
{
    public function __construct(
        private SmsGatewayInterface $smsGateway, // Real in prod, null/fake in dev
    ) {}

    public function send(Notification $notification): void
    {
        $this->smsGateway->send($notification);
    }
}

// services.yaml (production):
// SmsGatewayInterface: '@TwilioSmsGateway'

// services.yaml (development):
// SmsGatewayInterface: '@NullSmsGateway'
```

### 4. Non-Streaming Logs (Factor XI: Logs)

```php
<?php

declare(strict_types=1);

// BAD: Writing logs to local files
final class Logger
{
    public function log(string $message): void
    {
        file_put_contents(
            '/var/log/app/application.log',
            date('Y-m-d H:i:s') . ' ' . $message . PHP_EOL,
            FILE_APPEND,
        );
        // Log files grow unbounded, lost on container death
    }
}

// BAD: Custom log rotation in application
final class RotatingLogger
{
    public function log(string $message): void
    {
        $file = '/var/log/app/app-' . date('Y-m-d') . '.log';
        file_put_contents($file, $message . PHP_EOL, FILE_APPEND);

        // Application should NOT manage log rotation
        $this->cleanOldLogs();
    }
}

// GOOD: Write to stdout/stderr (event stream)
final readonly class StreamLogger implements LoggerInterface
{
    public function log(mixed $level, string|\Stringable $message, array $context = []): void
    {
        $entry = json_encode([
            'timestamp' => (new DateTimeImmutable())->format(DateTimeInterface::RFC3339),
            'level' => $level,
            'message' => (string) $message,
            'context' => $context,
        ], JSON_THROW_ON_ERROR);

        // Write to stderr -- container runtime captures this
        fwrite(STDERR, $entry . PHP_EOL);
    }
}

// GOOD: Monolog with stderr handler
// monolog.yaml:
// monolog:
//     handlers:
//         main:
//             type: stream
//             path: "php://stderr"
//             level: info
//             formatter: json
```

### 5. Missing Environment Variable Usage (Factor III: Config)

```php
<?php

declare(strict_types=1);

// BAD: Configuration not driven by environment
final class AppConfig
{
    public function getCacheDriver(): string
    {
        return 'redis'; // Hardcoded, cannot change without deploy
    }

    public function getMaxUploadSize(): int
    {
        return 10 * 1024 * 1024; // 10MB hardcoded
    }

    public function getApiBaseUrl(): string
    {
        return 'https://api.example.com/v2'; // Hardcoded URL
    }
}

// GOOD: Environment-driven configuration
final readonly class AppConfig
{
    public function __construct(
        private string $cacheDriver,
        private int $maxUploadSize,
        private string $apiBaseUrl,
    ) {}

    public static function fromEnvironment(): self
    {
        return new self(
            cacheDriver: getenv('CACHE_DRIVER') ?: 'redis',
            maxUploadSize: (int) (getenv('MAX_UPLOAD_SIZE') ?: '10485760'),
            apiBaseUrl: getenv('API_BASE_URL') ?: throw new \RuntimeException('API_BASE_URL required'),
        );
    }
}
```

### 6. Hardcoded Backing Services (Factor IV: Backing Services)

```php
<?php

declare(strict_types=1);

// BAD: Backing service URLs hardcoded
final class ExternalServices
{
    public function getPaymentGateway(): PaymentClient
    {
        return new PaymentClient('https://api.stripe.com/v1');
    }

    public function getSearchEngine(): SearchClient
    {
        return new SearchClient('http://elasticsearch:9200');
    }

    public function getQueueConnection(): AMQPConnection
    {
        return new AMQPConnection('amqp://guest:guest@rabbitmq:5672/');
    }
}

// GOOD: Backing services as attached resources via config
final readonly class ExternalServices
{
    public function __construct(
        private string $paymentGatewayUrl,
        private string $searchEngineUrl,
        private string $queueDsn,
    ) {}

    public static function fromEnvironment(): self
    {
        return new self(
            paymentGatewayUrl: getenv('PAYMENT_GATEWAY_URL')
                ?: throw new \RuntimeException('PAYMENT_GATEWAY_URL required'),
            searchEngineUrl: getenv('SEARCH_ENGINE_URL')
                ?: throw new \RuntimeException('SEARCH_ENGINE_URL required'),
            queueDsn: getenv('QUEUE_DSN')
                ?: throw new \RuntimeException('QUEUE_DSN required'),
        );
    }

    public function getPaymentGateway(): PaymentClient
    {
        return new PaymentClient($this->paymentGatewayUrl);
    }

    public function getSearchEngine(): SearchClient
    {
        return new SearchClient($this->searchEngineUrl);
    }

    public function getQueueConnection(): AMQPConnection
    {
        return new AMQPConnection($this->queueDsn);
    }
}
```

## Grep Patterns

```bash
# Hardcoded configuration values (Factor III)
Grep: "= 'smtp\.|= 'redis://|= 'mysql://|= 'amqp://|= 'https?://" --glob "**/src/**/*.php"
Grep: "'localhost'|'127\.0\.0\.1'|:3306|:6379|:5672|:9200" --glob "**/src/**/*.php"

# Hardcoded credentials
Grep: "password.*=.*['\"]|apiKey.*=.*['\"]|secret.*=.*['\"]" --glob "**/src/**/*.php"

# File-based state (Factor VI)
Grep: "file_put_contents\(|file_get_contents\(.*var|fwrite\(.*tmp" --glob "**/src/**/*.php"

# Environment-specific conditionals (Factor X)
Grep: "APP_ENV.*===|getenv\(['\"]APP_ENV|SERVER\[.APP_ENV" --glob "**/src/**/*.php"
Grep: "=== 'production'|=== 'staging'|=== 'development'" --glob "**/src/**/*.php"

# Non-streaming logs (Factor XI)
Grep: "file_put_contents\(.*\.log|fopen\(.*\.log|error_log\(" --glob "**/src/**/*.php"

# Missing env var usage (Factor III)
Grep: "getenv\(|env\(|\\\$_ENV|_SERVER\[" --glob "**/src/**/*.php"

# Backing service URLs in code (Factor IV)
Grep: "new.*Client\(['\"]https?://|new.*Connection\(['\"]" --glob "**/src/**/*.php"
```

## 12-Factor Mapping

| Factor | Name | What to Check |
|--------|------|---------------|
| I | Codebase | Single repo, multiple deploys |
| II | Dependencies | composer.json declares all deps |
| III | Config | No hardcoded config in source |
| IV | Backing Services | URLs/DSNs from environment |
| V | Build, Release, Run | Separate build and run stages |
| VI | Processes | Stateless, shared-nothing |
| VII | Port Binding | Self-contained, no external webserver dependency |
| VIII | Concurrency | Scale via process model |
| IX | Disposability | Fast startup, graceful shutdown |
| X | Dev/Prod Parity | Minimal gap between environments |
| XI | Logs | Treat logs as event streams |
| XII | Admin Processes | One-off admin tasks as processes |

## Severity Classification

| Pattern | Severity |
|---------|----------|
| Hardcoded credentials in source code | 🔴 Critical |
| Hardcoded database/service URLs | 🟠 Major |
| File-based persistent state | 🟠 Major |
| Environment-specific conditionals | 🟠 Major |
| Non-streaming logs (file-based) | 🟠 Major |
| Hardcoded non-secret config values | 🟡 Minor |
| Missing env var for optional settings | 🟡 Minor |

## Output Format

```markdown
### 12-Factor Violation: [Factor Name] -- [Brief Description]

**Severity:** 🔴/🟠/🟡
**Location:** `file.php:line`
**Factor:** [III Config|IV Backing Services|VI Processes|X Dev/Prod Parity|XI Logs]

**Issue:**
[Description of the 12-Factor violation]

**Impact:**
- Cannot deploy to different environments without code change
- State lost on container restart
- Logs lost when instance terminates

**Code:**
```php
// Non-compliant code
```

**Fix:**
```php
// 12-Factor compliant code
```
```

## When This Is Acceptable

- **Framework defaults** -- Framework-provided defaults (like Monolog file handler in dev) are standard practice
- **Constants** -- Truly constant values (HTTP status codes, mathematical constants) belong in code
- **Test configuration** -- Test suites may use hardcoded config for reproducibility
- **CLI tools** -- Local development tools may use filesystem legitimately

### False Positive Indicators
- Value is a mathematical or protocol constant, not a deployment config
- Hardcoded value is a default with environment override: `getenv('X') ?: 'default'`
- File path is for temporary processing, not persistent state
- Code is in a test file, fixture, or seed script
