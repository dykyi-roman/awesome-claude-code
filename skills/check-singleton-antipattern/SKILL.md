---
name: acc-check-singleton-antipattern
description: Detects Singleton anti-pattern in PHP code. Identifies global state via static instances, hidden dependencies, tight coupling, and testability issues.
---

# Singleton Anti-Pattern Detection

Analyze PHP code for Singleton anti-pattern usage that introduces global state and tight coupling.

## Detection Patterns

### 1. Classic Singleton Implementation

```php
// ANTIPATTERN: Static instance with private constructor
final class DatabaseConnection
{
    private static ?self $instance = null;

    private function __construct(
        private readonly PDO $pdo,
    ) {}

    public static function getInstance(): self
    {
        if (self::$instance === null) {
            self::$instance = new self(new PDO('mysql:host=localhost'));
        }
        return self::$instance;
    }
}

// Usage creates hidden dependency
class UserRepository
{
    public function find(int $id): User
    {
        $db = DatabaseConnection::getInstance(); // Hidden dependency!
        return $db->query("SELECT * FROM users WHERE id = ?", [$id]);
    }
}
```

### 2. Registry / Service Locator (Singleton Variant)

```php
// ANTIPATTERN: Global registry acting as singleton container
final class Registry
{
    private static array $services = [];

    public static function set(string $key, mixed $value): void
    {
        self::$services[$key] = $value;
    }

    public static function get(string $key): mixed
    {
        return self::$services[$key] ?? throw new RuntimeException("Not found: $key");
    }
}

// Usage hides ALL dependencies
class OrderService
{
    public function create(array $data): Order
    {
        $repo = Registry::get('orderRepository'); // Hidden dependency
        $mailer = Registry::get('mailer');         // Hidden dependency
    }
}
```

### 3. Static State Accumulation

```php
// ANTIPATTERN: Mutable static state
class EventBus
{
    private static array $listeners = [];

    public static function subscribe(string $event, callable $listener): void
    {
        self::$listeners[$event][] = $listener;
    }

    public static function dispatch(string $event, mixed $data): void
    {
        foreach (self::$listeners[$event] ?? [] as $listener) {
            $listener($data);
        }
    }
}
// Problem: State leaks between tests, no way to reset
```

### 4. Late Static Binding Singleton

```php
// ANTIPATTERN: Singleton via late static binding
abstract class BaseSingleton
{
    protected static array $instances = [];

    public static function getInstance(): static
    {
        $class = static::class;
        if (!isset(static::$instances[$class])) {
            static::$instances[$class] = new static();
        }
        return static::$instances[$class];
    }
}
```

### 5. Framework Anti-Patterns

```php
// ANTIPATTERN: Laravel Facade misuse (global state access)
class OrderController
{
    public function store(): Response
    {
        Cache::put('key', 'value');    // Static singleton access
        Log::info('Order created');     // Static singleton access
        Event::dispatch(new Created()); // Static singleton access
        // All dependencies hidden — not in constructor
    }
}

// CORRECT: Inject dependencies
final readonly class OrderController
{
    public function __construct(
        private CacheInterface $cache,
        private LoggerInterface $logger,
        private EventDispatcherInterface $events,
    ) {}
}
```

## Grep Patterns

```bash
# Classic singleton
Grep: "static.*\$instance|getInstance\(\)|private function __construct" --glob "**/*.php"

# Static service access
Grep: "static function get|static function getInstance|static::getInstance" --glob "**/*.php"

# Global state via static arrays
Grep: "private static array|protected static array" --glob "**/*.php"

# Registry / Service Locator
Grep: "Registry::get|ServiceLocator::get|Container::get" --glob "**/*.php"

# Mutable static properties
Grep: "static \$[a-z]+ =" --glob "**/Domain/**/*.php"
```

## Severity Classification

| Pattern | Severity |
|---------|----------|
| Singleton in Domain layer | 🔴 Critical |
| Service Locator pattern | 🔴 Critical |
| Static mutable state | 🟠 Major |
| Framework facade in Domain | 🟠 Major |
| Static helper/utility | 🟡 Minor |

## Correct Alternatives

### Use Dependency Injection

```php
// CORRECT: DI container manages lifecycle
final readonly class UserRepository
{
    public function __construct(
        private PDO $connection, // Injected, not global
    ) {}

    public function find(UserId $id): User
    {
        // Use injected dependency
        $stmt = $this->connection->prepare('SELECT * FROM users WHERE id = ?');
        $stmt->execute([$id->value()]);
        return $this->hydrate($stmt->fetch());
    }
}

// Container configuration (single instance if needed)
$container->singleton(PDO::class, fn () => new PDO($dsn));
```

### Use Factory for Complex Creation

```php
// CORRECT: Factory instead of Singleton
final readonly class ConnectionFactory
{
    public function __construct(
        private DatabaseConfig $config,
    ) {}

    public function create(): PDO
    {
        return new PDO(
            $this->config->dsn(),
            $this->config->username(),
            $this->config->password(),
        );
    }
}
```

## Output Format

```markdown
### Singleton Anti-Pattern: [Description]

**Severity:** 🔴/🟠/🟡
**Location:** `file.php:line`

**Issue:**
[Description of the singleton/global state problem]

**Impact:**
- Hidden dependency — not visible in constructor
- Tight coupling — cannot substitute in tests
- Global state — shared mutable state between tests/requests

**Code:**
```php
// Current singleton usage
```

**Fix:**
```php
// Refactored with dependency injection
```
```
