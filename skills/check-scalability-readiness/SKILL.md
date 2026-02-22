---
name: check-scalability-readiness
description: Analyzes PHP code for scalability issues. Detects file-based sessions, in-memory state, hardcoded hostnames, filesystem-dependent state, and missing stateless design patterns.
---

# Scalability Readiness Check

Analyze PHP code for patterns that prevent horizontal scaling, break in multi-instance deployments, or create single points of failure.

## Detection Patterns

### 1. File-Based Sessions

```php
<?php

declare(strict_types=1);

// BAD: Default file-based session storage
// php.ini: session.save_handler = files
session_start();
$_SESSION['user_id'] = $userId;
// Instance A stores session, Instance B cannot read it

// BAD: Direct $_SESSION usage without external store
final class AuthService
{
    public function login(User $user): void
    {
        $_SESSION['user'] = serialize($user);
        $_SESSION['logged_in'] = true;
        // Sticky sessions required, scaling limited
    }
}

// GOOD: Redis-backed session storage
// php.ini or runtime:
// session.save_handler = redis
// session.save_path = "tcp://redis:6379"

// GOOD: Token-based stateless authentication
final readonly class JwtAuthenticator
{
    public function __construct(
        private JwtEncoder $encoder,
    ) {}

    public function authenticate(Request $request): UserToken
    {
        $jwt = $request->headers->get('Authorization');
        $payload = $this->encoder->decode($jwt);

        return new UserToken(
            userId: new UserId($payload['sub']),
            roles: $payload['roles'],
        );
        // No server-side session state required
    }
}
```

### 2. In-Memory State and Singleton Cache

```php
<?php

declare(strict_types=1);

// BAD: Static in-memory cache
final class ConfigService
{
    private static array $cache = [];

    public static function get(string $key): mixed
    {
        if (!isset(self::$cache[$key])) {
            self::$cache[$key] = self::loadFromDatabase($key);
        }

        return self::$cache[$key];
        // Each instance has different cache state
        // Cache invalidation does not propagate
    }
}

// BAD: Global mutable state
$GLOBALS['app_state'] = ['initialized' => true];

// BAD: Singleton with mutable state
final class Registry
{
    private static ?self $instance = null;
    private array $data = [];

    public static function getInstance(): self
    {
        return self::$instance ??= new self();
    }

    public function set(string $key, mixed $value): void
    {
        $this->data[$key] = $value; // Lost between requests in FPM, inconsistent across instances
    }
}

// GOOD: External cache (Redis)
final readonly class ConfigService
{
    public function __construct(
        private CacheInterface $cache,
        private ConfigRepository $repository,
    ) {}

    public function get(string $key): mixed
    {
        return $this->cache->get(
            'config:' . $key,
            fn () => $this->repository->findByKey($key),
        );
        // All instances share the same cache
    }
}
```

### 3. Hardcoded Hostnames and Addresses

```php
<?php

declare(strict_types=1);

// BAD: Hardcoded hostnames
final class DatabaseConfig
{
    private string $host = 'localhost';
    private int $port = 3306;
    private string $redisHost = '127.0.0.1';
}

// BAD: Hardcoded service URLs
final readonly class ApiClient
{
    public function call(): Response
    {
        return $this->http->get('http://192.168.1.100:8080/api/data');
    }
}

// GOOD: Environment-driven configuration
final readonly class DatabaseConfig
{
    public function __construct(
        private string $host,
        private int $port,
        private string $redisHost,
    ) {}

    public static function fromEnvironment(): self
    {
        return new self(
            host: getenv('DB_HOST') ?: throw new \RuntimeException('DB_HOST not set'),
            port: (int) (getenv('DB_PORT') ?: '3306'),
            redisHost: getenv('REDIS_HOST') ?: throw new \RuntimeException('REDIS_HOST not set'),
        );
    }
}
```

### 4. Filesystem State and Local File Storage

```php
<?php

declare(strict_types=1);

// BAD: Local filesystem for state storage
final class QueueService
{
    public function enqueue(Job $job): void
    {
        file_put_contents(
            '/tmp/queue/' . uniqid() . '.job',
            serialize($job),
        );
        // Other instances cannot read this file
    }
}

// BAD: File-based locking
final class LockService
{
    public function acquire(string $key): bool
    {
        $fp = fopen('/tmp/locks/' . $key . '.lock', 'c');

        return flock($fp, LOCK_EX | LOCK_NB);
        // Lock is local to this filesystem/instance
    }
}

// BAD: Local file uploads
move_uploaded_file($tmpName, '/var/www/uploads/' . $filename);
// Only accessible on this instance

// GOOD: External storage for uploads
final readonly class FileUploadService
{
    public function __construct(
        private FilesystemOperator $storage, // S3, GCS, or MinIO
    ) {}

    public function upload(UploadedFile $file): string
    {
        $path = sprintf('uploads/%s/%s', date('Y/m/d'), $file->hashName());
        $this->storage->write($path, $file->getContent());

        return $path;
    }
}

// GOOD: Distributed locking
final readonly class DistributedLockService
{
    public function __construct(
        private LockFactory $lockFactory, // Redis-backed
    ) {}

    public function acquire(string $key, int $ttl = 30): Lock
    {
        $lock = $this->lockFactory->createLock($key, $ttl);
        $lock->acquire(true);

        return $lock;
    }
}
```

### 5. Missing Shared-Nothing Architecture

```php
<?php

declare(strict_types=1);

// BAD: Process depends on local cron schedule
// crontab: * * * * * php /var/www/artisan schedule:run
// Multiple instances = duplicate cron execution

// GOOD: Distributed cron with lock
final readonly class ScheduledTaskRunner
{
    public function __construct(
        private LockFactory $lockFactory,
    ) {}

    public function runOnce(string $taskName, callable $task): void
    {
        $lock = $this->lockFactory->createLock('cron:' . $taskName, 300);

        if (!$lock->acquire(false)) {
            return; // Another instance is running this task
        }

        try {
            $task();
        } finally {
            $lock->release();
        }
    }
}
```

## Grep Patterns

```bash
# File-based sessions
Grep: "\\\$_SESSION|session_start\(\)|session\.save_handler\s*=\s*files" --glob "**/*.php"
Grep: "session\.save_handler" --glob "**/*.ini"

# Static in-memory cache
Grep: "private static.*\\\$cache|private static.*=\s*\[\]|static.*\\\$instance" --glob "**/*.php"

# Global state
Grep: "\\\$GLOBALS|global\s+\\\$" --glob "**/*.php"

# Hardcoded hostnames
Grep: "localhost|127\.0\.0\.1|192\.168\.|10\.0\." --glob "**/src/**/*.php"
Grep: "'localhost'|\"localhost\"|'127\.0\.0\.1'" --glob "**/*.php"

# Local file operations for state
Grep: "file_put_contents\(|file_get_contents\(.*tmp|flock\(" --glob "**/src/**/*.php"
Grep: "move_uploaded_file\(" --glob "**/*.php"

# Local filesystem paths
Grep: "/tmp/|/var/www/uploads|/var/log/" --glob "**/src/**/*.php"

# Check for shared-nothing patterns
Grep: "FilesystemOperator|S3Client|Flysystem" --glob "**/*.php"
Grep: "RedisAdapter|Redis.*session|PredisClient" --glob "**/*.php"
```

## Severity Classification

| Pattern | Severity |
|---------|----------|
| File-based sessions in production | 🔴 Critical |
| Local filesystem for state storage | 🔴 Critical |
| Hardcoded hostnames in source code | 🟠 Major |
| Static in-memory cache for shared data | 🟠 Major |
| Local file uploads without external storage | 🟠 Major |
| Global mutable state | 🟠 Major |
| Missing distributed cron lock | 🟡 Minor |
| Singleton pattern with mutable state | 🟡 Minor |

## Output Format

```markdown
### Scalability Issue: [Brief Description]

**Severity:** 🔴/🟠/🟡
**Location:** `file.php:line`
**Type:** [File Session|In-Memory State|Hardcoded Host|Filesystem State|Shared-Nothing]

**Issue:**
[Description of the scalability blocker]

**Impact:**
- Cannot scale beyond single instance
- State lost on instance restart/replacement
- Inconsistent behavior in multi-instance deployment

**Code:**
```php
// Non-scalable pattern
```

**Fix:**
```php
// Horizontally scalable pattern
```
```

## When This Is Acceptable

- **Single-instance deployment** -- Small applications that will never require horizontal scaling
- **CLI tools** -- Command-line scripts that run on a single machine
- **Development environment** -- Local development uses file sessions and localhost
- **Static configuration** -- Immutable static arrays used as lookup tables (not mutable state)

### False Positive Indicators
- Static array is a constant lookup table (no mutations)
- File operations are for logging to stdout/stderr (Docker best practice)
- localhost appears only in test fixtures or development configuration
- $_SESSION usage is in a legacy adapter with Redis configured at runtime
