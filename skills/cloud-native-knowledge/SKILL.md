---
name: cloud-native-knowledge
description: Cloud Native knowledge base. Provides 12-Factor App principles with PHP-specific implementations, container-first patterns, and environment configuration for architecture audits.
---

# Cloud Native Knowledge Base

Quick reference for 12-Factor App principles with PHP-specific implementations and container-first patterns.

## 12-Factor App Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     12-FACTOR APP FLOW                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐     │
│   │ Codebase │───▶│   Build  │───▶│ Release  │───▶│   Run    │     │
│   │ (Git)    │    │ (Docker) │    │ (Tag)    │    │ (K8s)    │     │
│   └──────────┘    └──────────┘    └──────────┘    └──────────┘     │
│        │                │               │               │           │
│        │                │               │               │           │
│   ┌────▼─────┐    ┌────▼─────┐    ┌────▼─────┐    ┌────▼─────┐    │
│   │ composer │    │  ENV     │    │ Backing  │    │ Stateless│    │
│   │ .lock    │    │ Config   │    │ Services │    │ Processes│    │
│   │ (Deps)   │    │ (No .env │    │ (Redis,  │    │ (PHP-FPM │    │
│   │          │    │  in prod)│    │  DB, MQ) │    │  shared  │    │
│   └──────────┘    └──────────┘    └──────────┘    │  nothing)│    │
│                                                    └──────────┘    │
│                                                                      │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐     │
│   │ Port     │    │ Concur-  │    │ Dispos-  │    │ Dev/Prod │     │
│   │ Binding  │    │ rency    │    │ ability  │    │ Parity   │     │
│   │ (FPM,   │    │ (FPM     │    │ (Fast    │    │ (Docker  │     │
│   │  Runner) │    │  workers)│    │  start/  │    │  Compose)│     │
│   └──────────┘    └──────────┘    │  stop)   │    └──────────┘     │
│                                    └──────────┘                      │
│   ┌──────────┐    ┌──────────┐                                      │
│   │ Logs     │    │ Admin    │                                      │
│   │ (stderr  │    │ Processes│                                      │
│   │  stream) │    │ (Console │                                      │
│   └──────────┘    │  cmds)   │                                      │
│                    └──────────┘                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## The 12 Factors

| # | Factor | PHP Implementation | Anti-Pattern |
|---|--------|-------------------|-------------|
| 1 | **Codebase** | One Git repo per service | Multiple services in one repo (unless monorepo with clear boundaries) |
| 2 | **Dependencies** | `composer.lock` committed, no global installs | System-level `pecl install` without Dockerfile |
| 3 | **Config** | `$_ENV`, `getenv()`, DotEnv (dev only) | Hardcoded DB credentials, config in code |
| 4 | **Backing services** | DSN via env vars, adapter pattern | Direct `new Redis('localhost')` |
| 5 | **Build, release, run** | Docker multi-stage build | `composer install` in production at runtime |
| 6 | **Processes** | Stateless PHP-FPM, shared-nothing | `$_SESSION` file storage, local temp files |
| 7 | **Port binding** | PHP built-in server, FrankenPHP, RoadRunner | Apache module (mod_php) requiring full server |
| 8 | **Concurrency** | PHP-FPM process model, horizontal scaling | Single monolithic process |
| 9 | **Disposability** | Fast startup, `pcntl_signal` for SIGTERM | Long bootstrap, no graceful shutdown |
| 10 | **Dev/prod parity** | Docker Compose matches production | SQLite in dev, PostgreSQL in prod |
| 11 | **Logs** | Monolog `StreamHandler('php://stderr')` | Writing to `/var/log/app.log` files |
| 12 | **Admin processes** | Symfony Console, artisan, one-off containers | SSH into server and run scripts |

## Factor Details with PHP Examples

### Factor 3: Config — Environment Variables

```php
<?php

declare(strict_types=1);

namespace Config;

final readonly class DatabaseConfig
{
    public readonly string $host;
    public readonly int $port;
    public readonly string $name;
    public readonly string $user;
    public readonly string $password;

    public function __construct()
    {
        $this->host = $this->requireEnv('DB_HOST');
        $this->port = (int) $this->requireEnv('DB_PORT');
        $this->name = $this->requireEnv('DB_NAME');
        $this->user = $this->requireEnv('DB_USER');
        $this->password = $this->requireEnv('DB_PASSWORD');
    }

    public function dsn(): string
    {
        return sprintf(
            'pgsql:host=%s;port=%d;dbname=%s',
            $this->host,
            $this->port,
            $this->name,
        );
    }

    private function requireEnv(string $name): string
    {
        $value = $_ENV[$name] ?? getenv($name);

        if ($value === false || $value === '') {
            throw new \RuntimeException(sprintf(
                'Required environment variable "%s" is not set',
                $name,
            ));
        }

        return (string) $value;
    }
}
```

### Factor 4: Backing Services — Adapter Pattern

```php
<?php

declare(strict_types=1);

namespace Cache;

final readonly class RedisCacheAdapter implements CacheInterface
{
    private \Redis $redis;

    public function __construct()
    {
        $this->redis = new \Redis();
        $this->redis->connect(
            (string) ($_ENV['REDIS_HOST'] ?? 'localhost'),
            (int) ($_ENV['REDIS_PORT'] ?? 6379),
        );

        $password = $_ENV['REDIS_PASSWORD'] ?? null;
        if ($password !== null && $password !== '') {
            $this->redis->auth($password);
        }
    }

    public function get(string $key): mixed
    {
        $value = $this->redis->get($key);

        return $value !== false ? unserialize($value) : null;
    }

    public function set(string $key, mixed $value, int $ttl = 3600): void
    {
        $this->redis->setex($key, $ttl, serialize($value));
    }

    public function delete(string $key): void
    {
        $this->redis->del($key);
    }
}
```

### Factor 5: Build, Release, Run — Docker Multi-Stage

```dockerfile
# Stage 1: Build (install dependencies, compile assets)
FROM php:8.4-cli AS builder

COPY --from=composer:2 /usr/bin/composer /usr/bin/composer
WORKDIR /app

COPY composer.json composer.lock ./
RUN composer install --no-dev --no-scripts --prefer-dist --optimize-autoloader

COPY . .
RUN composer dump-autoload --optimize --classmap-authoritative

# Stage 2: Run (minimal production image)
FROM php:8.4-fpm-alpine AS runtime

RUN docker-php-ext-install pdo_pgsql opcache

COPY docker/php/php.ini /usr/local/etc/php/conf.d/app.ini
COPY docker/php/fpm-pool.conf /usr/local/etc/php-fpm.d/www.conf
COPY --from=builder /app /app

WORKDIR /app

EXPOSE 9000
CMD ["php-fpm"]
```

### Factor 9: Disposability — Graceful Shutdown

```php
<?php

declare(strict_types=1);

namespace Worker;

final class GracefulWorker
{
    private bool $shouldStop = false;

    public function __construct(
        private readonly MessageConsumerInterface $consumer,
    ) {
        pcntl_signal(SIGTERM, [$this, 'handleSignal']);
        pcntl_signal(SIGINT, [$this, 'handleSignal']);
    }

    public function run(): void
    {
        while (!$this->shouldStop) {
            pcntl_signal_dispatch();

            $message = $this->consumer->consume(timeoutMs: 1000);

            if ($message !== null) {
                $this->process($message);
                $this->consumer->acknowledge($message);
            }
        }

        $this->consumer->disconnect();
    }

    public function handleSignal(int $signal): void
    {
        $this->shouldStop = true;
    }

    private function process(Message $message): void
    {
        // Process message — keep this fast and idempotent
    }
}
```

### Factor 11: Logs — Stream to stderr

```php
<?php

declare(strict_types=1);

namespace Logging;

use Monolog\Handler\StreamHandler;
use Monolog\Logger;
use Psr\Log\LoggerInterface;

final readonly class LoggerFactory
{
    public static function create(string $channel = 'app'): LoggerInterface
    {
        $logger = new Logger($channel);

        // 12-Factor: treat logs as event streams to stderr
        // Container runtime (Docker/K8s) captures and forwards
        $logger->pushHandler(new StreamHandler('php://stderr', Logger::INFO));

        return $logger;
    }
}
```

### Factor 12: Admin Processes — One-Off Containers

```php
<?php

declare(strict_types=1);

namespace Console;

use Symfony\Component\Console\Attribute\AsCommand;
use Symfony\Component\Console\Command\Command;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Output\OutputInterface;

#[AsCommand(name: 'app:migrate', description: 'Run database migrations')]
final class MigrateCommand extends Command
{
    public function __construct(
        private readonly MigrationRunnerInterface $migrationRunner,
    ) {
        parent::__construct();
    }

    protected function execute(InputInterface $input, OutputInterface $output): int
    {
        $output->writeln('Running migrations...');

        $applied = $this->migrationRunner->run();

        $output->writeln(sprintf('Applied %d migrations.', $applied));

        return Command::SUCCESS;
    }
}

// Run as one-off container:
// docker run --rm myapp:latest php bin/console app:migrate
```

## PHP Violations Table

| Factor | Violation | Why It Breaks | Fix |
|--------|-----------|---------------|-----|
| 1 | Multiple apps in one repo without clear boundaries | Deploy coupling, version entanglement | Split repos or use monorepo tooling |
| 2 | `pecl install` at runtime | Non-reproducible builds | Install extensions in Dockerfile |
| 3 | `.env` file in production | Secrets in filesystem, not rotatable | Use real env vars or secrets vault |
| 3 | `define('DB_HOST', 'localhost')` | Config in code | Use `$_ENV['DB_HOST']` |
| 4 | `new Redis('10.0.0.5')` hardcoded | Cannot swap backing service | Inject via env var DSN |
| 5 | `composer install` at deploy time | Slow, network-dependent, non-reproducible | Install at build stage |
| 6 | `$_SESSION` with file handler | State tied to instance | Redis session handler |
| 6 | `file_put_contents('/tmp/data.json')` | State on local disk | Redis or object storage |
| 7 | Apache mod_php only | Cannot self-serve on a port | FPM + nginx, or FrankenPHP |
| 8 | Single-process Swoole without scaling | Cannot scale horizontally | FPM workers or multi-process Swoole |
| 9 | 30s bootstrap, no SIGTERM handler | Slow deploys, dropped requests | Preloading + signal handling |
| 10 | SQLite dev, PostgreSQL prod | Behavior differences in queries | Docker Compose with PostgreSQL |
| 11 | `file_put_contents('/var/log/app.log')` | Logs not collected by runtime | Monolog to `php://stderr` |
| 12 | SSH into server to run scripts | Not auditable, not reproducible | One-off container commands |

## Container-First PHP Patterns

### Health Check Endpoint

```php
<?php

declare(strict_types=1);

namespace Action;

final readonly class HealthAction
{
    public function __construct(
        private \PDO $pdo,
        private \Redis $redis,
    ) {}

    public function __invoke(): array
    {
        $checks = [];

        try {
            $this->pdo->query('SELECT 1');
            $checks['database'] = 'ok';
        } catch (\Throwable) {
            $checks['database'] = 'fail';
        }

        try {
            $this->redis->ping();
            $checks['redis'] = 'ok';
        } catch (\Throwable) {
            $checks['redis'] = 'fail';
        }

        $healthy = !in_array('fail', $checks, true);

        return [
            'status' => $healthy ? 'healthy' : 'unhealthy',
            'checks' => $checks,
        ];
    }
}
```

### Readiness vs Liveness

```
┌─────────────────────────────────────────────────────────────────────┐
│                   CONTAINER PROBES                                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   Liveness Probe (/healthz)                                         │
│   • "Is the process alive?"                                         │
│   • Checks: PHP-FPM responds, not deadlocked                       │
│   • Failure: container is RESTARTED                                 │
│   • Keep simple: just return 200                                    │
│                                                                      │
│   Readiness Probe (/readyz)                                         │
│   • "Can this instance serve traffic?"                              │
│   • Checks: DB reachable, Redis reachable, migrations applied      │
│   • Failure: instance removed from load balancer                    │
│   • More comprehensive: verify all backing services                 │
│                                                                      │
│   Startup Probe                                                     │
│   • "Has the app finished bootstrapping?"                           │
│   • Checks: OPcache warmed, preloading done                        │
│   • Failure: container not yet considered for liveness/readiness    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Detection Patterns

```bash
# Factor 3: Config via env vars
Grep: "getenv\(|\\$_ENV\[|env\(" --glob "**/*.php"
Grep: "define\(.*HOST\|define\(.*PASSWORD\|define\(.*SECRET" --glob "**/*.php"
Glob: **/.env
Glob: **/.env.prod

# Factor 4: Backing service configuration
Grep: "REDIS_HOST|REDIS_URL|DATABASE_URL|RABBITMQ_URL" --glob "**/.env*"
Grep: "new Redis\(|new \\\\PDO\(" --glob "**/src/**/*.php"

# Factor 5: Build artifacts
Glob: **/Dockerfile
Grep: "composer install" --glob "**/Dockerfile"
Grep: "multi-stage|AS builder|AS runtime" --glob "**/Dockerfile"

# Factor 6: Stateless violations
Grep: "session\.save_handler.*files|session_start" --glob "**/*.php"
Grep: "file_put_contents|fwrite" --glob "**/src/**/*.php"

# Factor 9: Graceful shutdown
Grep: "pcntl_signal|SIGTERM|SIGINT" --glob "**/*.php"

# Factor 11: Log streaming
Grep: "php://stderr|php://stdout" --glob "**/*.php"
Grep: "StreamHandler|error_log" --glob "**/*.php"
Grep: "file_put_contents.*log|fopen.*log" --glob "**/*.php"

# Factor 12: Admin processes
Grep: "AsCommand|Command::class" --glob "**/*.php"
Glob: **/bin/console
Glob: **/artisan

# Container health checks
Grep: "HEALTHCHECK|healthz|readyz" --glob "**/Dockerfile"
Grep: "health_check|liveness|readiness" --glob "**/docker-compose*.yml"
```

## Quick Reference

### 12-Factor Compliance Checklist

| Factor | Check | Pass Criteria |
|--------|-------|---------------|
| Codebase | Single repo per deployable | `git remote -v` shows one origin |
| Dependencies | Lock file committed | `composer.lock` in Git |
| Config | No secrets in code | Zero `define()` with credentials |
| Backing services | DSN from env | All connections via `$_ENV` |
| Build/Release/Run | Docker multi-stage | Separate build and runtime stages |
| Processes | Stateless | No `$_SESSION` files, no local temp |
| Port binding | Self-contained | FPM or embedded server |
| Concurrency | Process model | `pm = dynamic` or `static` |
| Disposability | Fast start/stop | < 5s startup, SIGTERM handler |
| Dev/prod parity | Same services | Docker Compose mirrors production |
| Logs | Stream to stderr | Monolog `php://stderr` handler |
| Admin | One-off containers | Console commands, no SSH |

## References

For detailed information, load these reference files:

- `references/twelve-factors.md` — Detailed explanation of each factor with PHP code examples, DotEnv setup, Symfony secrets vault, Docker CMD, signal handling, log streaming
