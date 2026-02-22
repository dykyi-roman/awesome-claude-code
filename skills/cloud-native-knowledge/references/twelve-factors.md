# Twelve-Factor App Reference for PHP

## Factor 1: Codebase — One Codebase, Many Deploys

### Correct Structure

```
my-service/
├── src/
│   ├── Domain/
│   ├── Application/
│   ├── Infrastructure/
│   └── Presentation/
├── config/
├── tests/
├── composer.json
├── composer.lock
├── Dockerfile
└── .env.example       # Template only, never real credentials
```

### Monorepo Exception

For monorepos, each service has its own Dockerfile and can be deployed independently:

```
monorepo/
├── services/
│   ├── order-service/
│   │   ├── src/
│   │   ├── Dockerfile
│   │   └── composer.json
│   └── payment-service/
│       ├── src/
│       ├── Dockerfile
│       └── composer.json
└── shared/
    └── common-lib/        # Shared code as composer package
```

## Factor 2: Dependencies — Explicitly Declare and Isolate

### Composer Lock

```json
{
    "require": {
        "php": "^8.4",
        "psr/log": "^3.0",
        "symfony/console": "^7.2",
        "predis/predis": "^2.3"
    },
    "require-dev": {
        "phpunit/phpunit": "^11.0",
        "phpstan/phpstan": "^2.0"
    }
}
```

### Dockerfile with Extensions

```dockerfile
FROM php:8.4-fpm-alpine

# All dependencies declared explicitly
RUN apk add --no-cache postgresql-dev \
    && docker-php-ext-install pdo_pgsql opcache \
    && pecl install redis \
    && docker-php-ext-enable redis
```

## Factor 3: Config — Store Config in the Environment

### `getenv()` vs `$_ENV`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Config;

// Preferred: $_ENV (populated by PHP-FPM env directives)
$dbHost = $_ENV['DB_HOST'] ?? throw new \RuntimeException('DB_HOST not set');

// Alternative: getenv() (works in CLI and FPM)
$dbHost = getenv('DB_HOST') ?: throw new \RuntimeException('DB_HOST not set');

// NEVER in production code:
$dbHost = 'localhost';              // hardcoded
$dbHost = parse_ini_file('.env');   // file-based in prod
```

### DotEnv Setup (Development Only)

```php
<?php

declare(strict_types=1);

// public/index.php — Bootstrap
require dirname(__DIR__) . '/vendor/autoload.php';

// Only load .env in development
if (file_exists(dirname(__DIR__) . '/.env')) {
    $dotenv = Dotenv\Dotenv::createImmutable(dirname(__DIR__));
    $dotenv->load();
    $dotenv->required([
        'DB_HOST', 'DB_PORT', 'DB_NAME',
        'DB_USER', 'DB_PASSWORD',
        'REDIS_HOST', 'APP_SECRET',
    ]);
}

// In production: env vars set by container runtime (K8s, ECS, etc.)
```

### Symfony Secrets Vault

```php
<?php

declare(strict_types=1);

// Symfony secrets for sensitive config (encrypted, committed to repo)
// Only decryption key is an env var

// config/packages/framework.yaml:
// framework:
//     secrets:
//         decryption_env_var: SYMFONY_DECRYPTION_SECRET

// Create secret:
// bin/console secrets:set DATABASE_URL --env=prod

// Usage in services.yaml:
// parameters:
//     database_url: '%env(DATABASE_URL)%'
```

### Environment-Specific Config Anti-Patterns

| Pattern | Problem | Solution |
|---------|---------|----------|
| `config/database.prod.php` | Config in code, requires redeploy to change | Env vars |
| `.env` in Docker image | Secrets baked into image | Runtime env vars |
| `if (APP_ENV === 'prod')` | Environment-aware code | Same code, different config |
| Hardcoded service URLs | Cannot move services | Env vars for all URLs |
| Config in database | Extra dependency for bootstrap | Env vars for bootstrap config |

## Factor 5: Build, Release, Run

### Docker CMD for PHP-FPM

```dockerfile
# Correct: exec form (PID 1, receives signals)
CMD ["php-fpm"]

# Incorrect: shell form (runs under /bin/sh, signals lost)
CMD php-fpm

# With entrypoint for pre-flight checks:
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["php-fpm"]
```

### Entrypoint Script

```bash
#!/bin/sh
set -e

# Wait for database
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -q; do
    echo "Waiting for database..."
    sleep 1
done

# Run migrations (optional, depends on strategy)
if [ "${RUN_MIGRATIONS:-false}" = "true" ]; then
    php bin/console doctrine:migrations:migrate --no-interaction
fi

# Execute the main command (php-fpm)
exec "$@"
```

## Factor 7: Port Binding

### PHP-FPM with Nginx

```nginx
# nginx.conf — reverse proxy to PHP-FPM
server {
    listen 8080;
    root /app/public;
    index index.php;

    location / {
        try_files $uri /index.php$is_args$args;
    }

    location ~ ^/index\.php(/|$) {
        fastcgi_pass 127.0.0.1:9000;
        fastcgi_param SCRIPT_FILENAME $realpath_root$fastcgi_script_name;
        include fastcgi_params;
        internal;
    }
}
```

### FrankenPHP (Self-Contained)

```dockerfile
FROM dunglas/frankenphp:php8.4-alpine

COPY . /app/public

ENV SERVER_NAME=:8080
ENV FRANKENPHP_CONFIG="worker ./public/index.php"

EXPOSE 8080
```

### RoadRunner (Self-Contained)

```php
<?php

declare(strict_types=1);

// worker.php — RoadRunner PSR-7 worker
use Spiral\RoadRunner\Http\PSR7Worker;
use Nyholm\Psr7\Factory\Psr17Factory;

require __DIR__ . '/vendor/autoload.php';

$psr17Factory = new Psr17Factory();
$worker = new PSR7Worker(
    \Spiral\RoadRunner\Worker::create(),
    $psr17Factory,
    $psr17Factory,
    $psr17Factory,
);

$app = require __DIR__ . '/config/bootstrap.php';

while ($request = $worker->waitRequest()) {
    try {
        $response = $app->handle($request);
        $worker->respond($response);
    } catch (\Throwable $e) {
        $worker->getWorker()->error($e->getMessage());
    }
}
```

## Factor 9: Disposability — Graceful Shutdown

### Signal Handling

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Worker;

final class SignalAwareConsumer
{
    private bool $running = true;

    public function __construct(
        private readonly QueueInterface $queue,
        private readonly HandlerInterface $handler,
    ) {
        if (extension_loaded('pcntl')) {
            pcntl_signal(SIGTERM, fn () => $this->running = false);
            pcntl_signal(SIGINT, fn () => $this->running = false);
        }
    }

    public function consume(): void
    {
        while ($this->running) {
            if (extension_loaded('pcntl')) {
                pcntl_signal_dispatch();
            }

            $message = $this->queue->dequeue(timeoutMs: 1000);

            if ($message === null) {
                continue;
            }

            try {
                $this->handler->handle($message);
                $this->queue->ack($message);
            } catch (\Throwable $e) {
                $this->queue->nack($message);
            }
        }

        // Graceful cleanup
        $this->queue->disconnect();
    }
}
```

### PHP-FPM Graceful Shutdown

```ini
; php-fpm.conf
; Send SIGQUIT for graceful stop (finish current request)
process_control_timeout = 10

; Kubernetes: set terminationGracePeriodSeconds >= process_control_timeout
; SIGTERM → FPM finishes active requests → exits
```

## Factor 11: Logs — Log Streaming

### Monolog Configuration

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Logging;

use Monolog\Formatter\JsonFormatter;
use Monolog\Handler\StreamHandler;
use Monolog\Logger;
use Monolog\Processor\UidProcessor;
use Psr\Log\LoggerInterface;

final readonly class StructuredLoggerFactory
{
    public static function create(string $channel = 'app'): LoggerInterface
    {
        $logger = new Logger($channel);

        // Stream to stderr — container runtime collects
        $handler = new StreamHandler('php://stderr', Logger::INFO);
        $handler->setFormatter(new JsonFormatter());

        $logger->pushHandler($handler);

        // Add request ID for distributed tracing
        $logger->pushProcessor(new UidProcessor());

        return $logger;
    }
}
```

### Symfony Monolog Config

```yaml
# config/packages/monolog.yaml
monolog:
    handlers:
        main:
            type: stream
            path: "php://stderr"
            level: info
            formatter: monolog.formatter.json
        console:
            type: console
            process_psr_3_messages: false
            channels: ["!event", "!doctrine"]
```

### Log Format (Structured JSON)

```json
{
    "message": "Order placed",
    "context": {
        "order_id": "ord_abc123",
        "customer_id": "cust_xyz",
        "total": 99.99
    },
    "level": 200,
    "level_name": "INFO",
    "channel": "app",
    "datetime": "2026-02-22T10:30:00+00:00",
    "extra": {
        "uid": "req_f8a2b1c3"
    }
}
```

## Factor 12: Admin Processes

### Symfony Console Command

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Console;

use Symfony\Component\Console\Attribute\AsCommand;
use Symfony\Component\Console\Command\Command;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Output\OutputInterface;

#[AsCommand(
    name: 'app:cleanup-expired-sessions',
    description: 'Remove expired sessions from Redis',
)]
final class CleanupExpiredSessionsCommand extends Command
{
    public function __construct(
        private readonly SessionCleanerInterface $cleaner,
    ) {
        parent::__construct();
    }

    protected function execute(InputInterface $input, OutputInterface $output): int
    {
        $count = $this->cleaner->cleanExpired();
        $output->writeln(sprintf('Cleaned %d expired sessions.', $count));

        return Command::SUCCESS;
    }
}
```

### Running Admin Commands in Containers

```bash
# Run migration as one-off container (same image, different command)
docker run --rm --env-file .env myapp:v1.2.3 php bin/console doctrine:migrations:migrate --no-interaction

# Run cleanup job
docker run --rm --env-file .env myapp:v1.2.3 php bin/console app:cleanup-expired-sessions

# Kubernetes Job for one-off command
# kubectl create job --from=cronjob/session-cleanup manual-cleanup
```

### Makefile Admin Commands

```makefile
.PHONY: migrate seed cache-clear

migrate:
	docker compose exec app php bin/console doctrine:migrations:migrate --no-interaction

seed:
	docker compose exec app php bin/console app:seed-database

cache-clear:
	docker compose exec app php bin/console cache:clear
```

## Docker Compose for Dev/Prod Parity (Factor 10)

```yaml
# docker-compose.yml
services:
  app:
    build:
      context: .
      target: runtime
    environment:
      DB_HOST: postgres
      DB_PORT: 5432
      DB_NAME: myapp
      DB_USER: app
      DB_PASSWORD: secret
      REDIS_HOST: redis
      REDIS_PORT: 6379
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started

  postgres:
    image: postgres:17-alpine
    environment:
      POSTGRES_DB: myapp
      POSTGRES_USER: app
      POSTGRES_PASSWORD: secret
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app -d myapp"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
```
