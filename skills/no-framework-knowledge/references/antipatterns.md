# No-Framework PHP Antipatterns

Common mistakes when building framework-free PHP applications, with detection patterns and fixes.

## Critical Antipatterns

### 1. Reinventing the Wheel

**Description:** Building a custom ORM, router, or template engine when battle-tested PSR-compliant packages exist.

**Why Critical:** Custom implementations introduce bugs, lack community testing, and waste development time.

**Detection:**

```bash
# Custom ORM / query builder in the project
Grep: "class.*QueryBuilder|class.*ORM|class.*EntityManager" --glob "**/src/**/*.php"
Grep: "function query\(|function execute\(.*sql" --glob "**/src/Infrastructure/**/*.php" -A 5

# Custom router (beyond thin FastRoute wrapper)
Grep: "class.*Router" --glob "**/src/**/*.php"
Grep: "preg_match.*REQUEST_URI|parse_url.*REQUEST_URI" --glob "**/src/**/*.php"

# Custom template engine
Grep: "class.*TemplateEngine|class.*ViewRenderer" --glob "**/src/**/*.php"
Grep: "ob_start|ob_get_clean|extract\(" --glob "**/src/**/*.php"
```

**Bad:**

```php
declare(strict_types=1);

namespace Infrastructure\Persistence;

// Custom ORM — hundreds of lines, fragile, untested
final class CustomEntityManager
{
    public function persist(object $entity): void
    {
        $reflection = new \ReflectionClass($entity);
        $table = strtolower($reflection->getShortName()) . 's';
        $columns = [];
        $values = [];

        foreach ($reflection->getProperties() as $prop) {
            $columns[] = $prop->getName();
            $values[] = $prop->getValue($entity);
        }

        // Fragile SQL construction, SQL injection risk
        $sql = sprintf(
            'INSERT INTO %s (%s) VALUES (%s)',
            $table,
            implode(', ', $columns),
            implode(', ', array_fill(0, count($values), '?')),
        );

        $this->pdo->prepare($sql)->execute($values);
    }
}
```

**Good:**

```php
declare(strict_types=1);

// Use Doctrine ORM standalone — battle-tested, well-documented
// composer require doctrine/orm doctrine/migrations

namespace Infrastructure\Persistence\Doctrine\Repository;

use Doctrine\ORM\EntityManagerInterface;

final readonly class DoctrineOrderRepository implements OrderRepositoryInterface
{
    public function __construct(
        private EntityManagerInterface $em,
    ) {}

    public function save(Order $order): void
    {
        $this->em->persist($order);
        $this->em->flush();
    }
}
```

### 2. Missing PSR Compliance

**Description:** Ignoring PSR standards for HTTP messages, containers, logging, and autoloading.

**Why Critical:** Loses interoperability with the PHP ecosystem. Cannot swap implementations.

**Detection:**

```bash
# Raw superglobals instead of PSR-7
Grep: "\\\$_GET|\\\$_POST|\\\$_REQUEST|\\\$_SERVER\[.HTTP" --glob "**/src/**/*.php"

# Raw header() and echo instead of PSR-7 Response
Grep: "\\bheader\(|^\\s*echo\\b|print\\b" --glob "**/src/**/*.php"

# Custom container without PSR-11
Grep: "class.*Container" --glob "**/src/**/*.php"
Grep: "ContainerInterface" --glob "**/src/**/Container*.php"

# Manual require/include instead of PSR-4
Grep: "require_once|include_once|require ['\"]|include ['\"]" --glob "**/src/**/*.php"
```

**Bad:**

```php
// No PSR-7, raw globals
$name = $_POST['name'];
$id = $_GET['id'];

header('Content-Type: application/json');
echo json_encode(['status' => 'ok']);
```

**Good:**

```php
declare(strict_types=1);

// PSR-7 request/response
$name = $request->getParsedBody()['name'] ?? '';
$id = $request->getQueryParams()['id'] ?? '';

return new Response(
    status: 200,
    headers: ['Content-Type' => 'application/json'],
    body: json_encode(['status' => 'ok'], JSON_THROW_ON_ERROR),
);
```

### 3. Global State and Singletons

**Description:** Using global variables, static state, or singleton pattern for shared services.

**Why Critical:** Makes testing impossible, hides dependencies, creates coupling.

**Detection:**

```bash
# Global keyword
Grep: "\\bglobal \\$" --glob "**/src/**/*.php"

# Static instance / singleton
Grep: "static.*\\\$instance|::getInstance\(\)|private static" --glob "**/src/**/*.php"

# Global functions as service locators
Grep: "function app\(\)|function container\(\)|function resolve\(" --glob "**/src/**/*.php"

# Session superglobal
Grep: "\\\$_SESSION" --glob "**/src/**/*.php"
```

**Bad:**

```php
declare(strict_types=1);

final class Database
{
    private static ?self $instance = null;

    private function __construct(
        private readonly \PDO $pdo,
    ) {}

    public static function getInstance(): self
    {
        if (self::$instance === null) {
            self::$instance = new self(new \PDO(/* ... */));
        }

        return self::$instance;
    }
}

// Usage — hidden dependency, untestable
$db = Database::getInstance();
```

**Good:**

```php
declare(strict_types=1);

// Inject via constructor — explicit, testable
final readonly class DoctrineOrderRepository implements OrderRepositoryInterface
{
    public function __construct(
        private \PDO $pdo,
    ) {}
}

// DI container handles lifecycle
// config/container.php
$builder->addDefinitions([
    \PDO::class => DI\factory(static fn(): \PDO => new \PDO(/* ... */)),
]);
```

### 4. Tight Coupling Between Layers

**Description:** Domain depends on Infrastructure, Application imports Presentation, or direct class instantiation across layer boundaries.

**Why Critical:** Changes in one layer cascade to others. Domain cannot be tested in isolation.

**Detection:**

```bash
# Domain importing Infrastructure
Grep: "use Infrastructure\\\\" --glob "**/Domain/**/*.php"

# Domain importing Presentation
Grep: "use Presentation\\\\" --glob "**/Domain/**/*.php"

# Application importing Infrastructure
Grep: "use Infrastructure\\\\" --glob "**/Application/**/*.php"

# Application importing Presentation
Grep: "use Presentation\\\\" --glob "**/Application/**/*.php"

# Direct instantiation of infrastructure in application
Grep: "new Doctrine|new Redis|new PDO|new Guzzle" --glob "**/Application/**/*.php"
```

**Bad:**

```php
declare(strict_types=1);

namespace Application\Order\UseCase;

use Infrastructure\Persistence\Doctrine\Repository\DoctrineOrderRepository; // VIOLATION!
use Infrastructure\Cache\RedisCache; // VIOLATION!

final readonly class GetOrderUseCase
{
    public function __construct(
        private DoctrineOrderRepository $repository,  // Concrete class, not interface
        private RedisCache $cache,                     // Infrastructure in Application
    ) {}
}
```

**Good:**

```php
declare(strict_types=1);

namespace Application\Order\UseCase;

use Domain\Order\Repository\OrderRepositoryInterface; // Domain interface
use Application\Shared\Port\CacheInterface;            // Application port

final readonly class GetOrderUseCase
{
    public function __construct(
        private OrderRepositoryInterface $repository,  // Interface
        private CacheInterface $cache,                  // Interface
    ) {}
}
```

## Warning Antipatterns

### 5. No Autoloading or Manual Requires

**Description:** Using `require_once` / `include` chains instead of Composer PSR-4 autoloading.

**Detection:**

```bash
Grep: "require_once|include_once" --glob "**/src/**/*.php"
Grep: "require ['\"]\\.\\./" --glob "**/public/index.php"
Grep: "spl_autoload_register" --glob "**/src/**/*.php"
```

**Bad:**

```php
<?php
require_once '../src/Domain/Order/Entity/Order.php';
require_once '../src/Domain/Order/ValueObject/OrderId.php';
require_once '../src/Infrastructure/Persistence/PdoOrderRepository.php';
// 50 more require_once...
```

**Good:**

```php
declare(strict_types=1);

// Single autoloader from Composer
require dirname(__DIR__) . '/vendor/autoload.php';

// All classes resolved automatically via PSR-4
```

### 6. Missing Dependency Injection

**Description:** Creating dependencies inside classes with `new` instead of injecting them.

**Detection:**

```bash
# new inside domain/application (excluding Value Objects and DTOs)
Grep: "new [A-Z].*Repository\(|new [A-Z].*Service\(|new [A-Z].*Client\(" --glob "**/src/Application/**/*.php"
Grep: "new [A-Z].*Repository\(|new [A-Z].*Service\(|new [A-Z].*Client\(" --glob "**/src/Domain/**/*.php"
```

**Bad:**

```php
declare(strict_types=1);

namespace Application\Order\UseCase;

final class CreateOrderUseCase
{
    public function execute(array $data): void
    {
        $pdo = new \PDO('pgsql:host=localhost;dbname=app', 'user', 'pass'); // Hardcoded!
        $repo = new PdoOrderRepository($pdo);                                // Created inline!
        $logger = new FileLogger('/var/log/app.log');                         // Created inline!
        // ...
    }
}
```

**Good:**

```php
declare(strict_types=1);

namespace Application\Order\UseCase;

final readonly class CreateOrderUseCase
{
    public function __construct(
        private OrderRepositoryInterface $orders,
        private LoggerInterface $logger,
    ) {}

    public function execute(CreateOrderCommand $command): OrderId
    {
        // Dependencies injected, testable, swappable
    }
}
```

### 7. No Error Handling Strategy

**Description:** Missing error middleware, catching all exceptions silently, or exposing stack traces in production.

**Detection:**

```bash
# Empty catch blocks
Grep: "catch.*\\{\\s*\\}" --glob "**/src/**/*.php"

# Catch-all without logging
Grep: "catch \\(\\\\Throwable|catch \\(\\\\Exception" --glob "**/src/**/*.php" -A 3

# Missing error handler middleware
Grep: "ErrorHandler|ExceptionHandler" --glob "**/config/middleware*.php"

# Stack traces leaked to output
Grep: "getTraceAsString|getMessage\(\)" --glob "**/src/Presentation/**/*.php"
```

**Bad:**

```php
try {
    $order = $this->createOrder->execute($command);
} catch (\Exception $e) {
    // Silent failure — error is lost
}
```

**Good:**

```php
declare(strict_types=1);

// Error handling via middleware — catches everything
$pipeline->pipe($container->get(ErrorHandlerMiddleware::class));

// Domain exceptions map to HTTP status codes in Presentation layer
return match (true) {
    $e instanceof OrderNotFoundException => new Response(404, body: json_encode([
        'error' => $e->getMessage(),
    ], JSON_THROW_ON_ERROR)),
    $e instanceof InvalidStateTransitionException => new Response(409, body: json_encode([
        'error' => $e->getMessage(),
    ], JSON_THROW_ON_ERROR)),
    default => new Response(500, body: json_encode([
        'error' => 'Internal Server Error',
    ], JSON_THROW_ON_ERROR)),
};
```

### 8. Auth/Session Logic in Domain Layer

**Severity:** Warning

**Description:** Domain entities or services importing JWT libraries, session handling, or password hashing implementations directly.

**Detection:**

```bash
Grep: "use Lcobucci\\\\JWT|use Firebase\\\\JWT" --glob "**/Domain/**/*.php"
Grep: "password_hash\(|password_verify\(" --glob "**/Domain/**/*.php"
Grep: "\\$_SESSION|session_start" --glob "**/Domain/**/*.php"
Grep: "use Infrastructure\\\\Security" --glob "**/Domain/**/*.php"
```

**Bad:**

```php
declare(strict_types=1);

namespace Domain\User\Service;

use Lcobucci\JWT\Configuration; // VIOLATION: JWT library in Domain

final readonly class UserAuthService
{
    public function __construct(
        private Configuration $jwtConfig,
    ) {}

    public function authenticate(string $email, string $password): string
    {
        // VIOLATION: JWT token generation in Domain
        return $this->jwtConfig->builder()
            ->withClaim('email', $email)
            ->getToken($this->jwtConfig->signer(), $this->jwtConfig->signingKey())
            ->toString();
    }
}
```

**Good:**

```php
declare(strict_types=1);

namespace Domain\User\Port;

// Domain port — no library dependencies
interface TokenGeneratorInterface
{
    public function generate(UserId $userId, array $claims = []): string;
}
```

```php
declare(strict_types=1);

namespace Infrastructure\Security;

use Domain\User\Port\TokenGeneratorInterface;
use Lcobucci\JWT\Configuration;

// Infrastructure adapter — JWT library only here
final readonly class JwtTokenGenerator implements TokenGeneratorInterface
{
    public function __construct(
        private Configuration $config,
    ) {}

    public function generate(UserId $userId, array $claims = []): string
    {
        $builder = $this->config->builder()
            ->withClaim('sub', $userId->value);

        foreach ($claims as $key => $value) {
            $builder = $builder->withClaim($key, $value);
        }

        return $builder
            ->getToken($this->config->signer(), $this->config->signingKey())
            ->toString();
    }
}
```

### 9. Missing Queue Resilience

**Severity:** Warning

**Description:** Queue workers and job handlers without retry logic, error handling, or graceful shutdown.

**Detection:**

```bash
# Workers without signal handling
Grep: "while.*true|while.*running" --glob "**/src/Infrastructure/**/Worker*.php"
Grep: "pcntl_signal|SIGTERM|SIGINT" --glob "**/src/Infrastructure/**/Worker*.php" --output_mode count

# Handlers without try-catch
Grep: "function handle\(|function process\(" --glob "**/src/Infrastructure/**/Handler*.php"
Grep: "try.*catch" --glob "**/src/Infrastructure/**/Handler*.php" --output_mode count
```

**Bad:**

```php
declare(strict_types=1);

namespace Infrastructure\Queue;

// VIOLATION: No retry, no error handling, no graceful shutdown
final class SimpleWorker
{
    public function run(): void
    {
        while (true) { // No signal handling!
            $message = $this->consumer->receive();
            $handler = $this->resolveHandler($message);
            $handler->handle($message->getBody()); // No try-catch!
        }
    }
}
```

**Good:**

```php
declare(strict_types=1);

namespace Infrastructure\Queue;

use Psr\Log\LoggerInterface;

final class ResilientWorker
{
    private bool $running = true;

    public function __construct(
        private readonly ConsumerInterface $consumer,
        private readonly HandlerResolver $resolver,
        private readonly LoggerInterface $logger,
        private readonly int $maxRetries = 3,
    ) {
        pcntl_signal(SIGTERM, fn() => $this->running = false);
        pcntl_signal(SIGINT, fn() => $this->running = false);
    }

    public function run(): void
    {
        while ($this->running) {
            pcntl_signal_dispatch();
            $message = $this->consumer->receive(timeout: 5000);

            if ($message === null) {
                continue;
            }

            try {
                $handler = $this->resolver->resolve($message);
                $handler->handle($message->getBody());
                $this->consumer->acknowledge($message);
            } catch (\Throwable $e) {
                $this->logger->error('Job failed', [
                    'message' => $message->getProperty('type'),
                    'error' => $e->getMessage(),
                ]);
                $this->consumer->reject($message, requeue: $message->getAttempt() < $this->maxRetries);
            }
        }

        $this->logger->info('Worker stopped gracefully');
    }
}
```

## Severity Matrix

| Antipattern | Severity | Impact | Fix Effort |
|-------------|----------|--------|------------|
| Reinventing the Wheel | Critical | Reliability | High |
| Missing PSR Compliance | Critical | Interoperability | Medium |
| Global State / Singletons | Critical | Testability | Medium |
| Tight Coupling Between Layers | Critical | Maintainability | High |
| No Autoloading | Warning | Maintainability | Low |
| Missing DI | Warning | Testability | Medium |
| No Error Handling Strategy | Warning | Reliability | Medium |
| Auth/Session Logic in Domain | Warning | Separation of concerns | Medium |
| Missing Queue Resilience | Warning | Reliability | Low |

## Full Detection Script

```bash
# Run all antipattern checks for a no-framework project

# Critical checks
Grep: "class.*QueryBuilder|class.*ORM" --glob "**/src/**/*.php"
Grep: "\\\$_GET|\\\$_POST|\\\$_REQUEST" --glob "**/src/**/*.php"
Grep: "static.*\\\$instance|::getInstance\(\)" --glob "**/src/**/*.php"
Grep: "use Infrastructure\\\\" --glob "**/Domain/**/*.php"

# Warning checks
Grep: "require_once|include_once" --glob "**/src/**/*.php"
Grep: "new [A-Z].*Repository\(|new [A-Z].*Service\(" --glob "**/Application/**/*.php"
Grep: "catch.*\\{\\s*\\}" --glob "**/src/**/*.php"

# Auth in Domain checks
Grep: "use Lcobucci\\\\JWT|use Firebase\\\\JWT" --glob "**/Domain/**/*.php"
Grep: "password_hash\(|password_verify\(" --glob "**/Domain/**/*.php"
Grep: "\\$_SESSION" --glob "**/Domain/**/*.php"

# Queue in Domain checks
Grep: "use Enqueue\\\\|use PhpAmqpLib\\\\" --glob "**/Domain/**/*.php"
Grep: "use Interop\\\\Queue\\\\" --glob "**/Domain/**/*.php"

# Missing queue resilience
Grep: "while.*true" --glob "**/Infrastructure/**/Worker*.php"
Grep: "pcntl_signal" --glob "**/Infrastructure/**/Worker*.php" --output_mode count
```
