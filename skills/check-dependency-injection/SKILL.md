---
name: acc-check-dependency-injection
description: Analyzes PHP code for dependency injection issues. Detects constructor injection usage, interface dependencies, service locator antipattern, new keyword in business logic.
---

# Dependency Injection Check

Analyze PHP code for proper dependency injection patterns.

## Detection Patterns

### 1. New Keyword in Business Logic

```php
// BAD: Hard-coded dependency
class OrderService
{
    public function process(Order $order): void
    {
        $mailer = new Mailer(); // Can't mock this
        $mailer->send($order->getCustomer(), 'confirmation');
    }
}

// GOOD: Injected dependency
class OrderService
{
    public function __construct(
        private MailerInterface $mailer,
    ) {}

    public function process(Order $order): void
    {
        $this->mailer->send($order->getCustomer(), 'confirmation');
    }
}
```

### 2. Service Locator Antipattern

```php
// BAD: Service locator
class UserService
{
    public function register(UserData $data): User
    {
        $hasher = Container::get(PasswordHasher::class);
        $repository = Container::get(UserRepository::class);
        $mailer = Container::get(Mailer::class);

        // Dependencies are hidden
    }
}

// GOOD: Constructor injection
class UserService
{
    public function __construct(
        private PasswordHasher $hasher,
        private UserRepository $repository,
        private Mailer $mailer,
    ) {}

    // Dependencies are explicit
}
```

### 3. Static Method Calls

```php
// BAD: Static calls can't be mocked
class ReportGenerator
{
    public function generate(): Report
    {
        $data = Database::query('SELECT ...');  // Static
        $date = Carbon::now();                   // Static
        $id = Uuid::uuid4();                     // Static

        return new Report($data, $date, $id);
    }
}

// GOOD: Injectable services
class ReportGenerator
{
    public function __construct(
        private Connection $database,
        private ClockInterface $clock,
        private UuidGenerator $uuidGenerator,
    ) {}

    public function generate(): Report
    {
        $data = $this->database->query('SELECT ...');
        $date = $this->clock->now();
        $id = $this->uuidGenerator->generate();

        return new Report($data, $date, $id);
    }
}
```

### 4. Missing Interface

```php
// BAD: Concrete class dependency
class PaymentProcessor
{
    public function __construct(
        private StripeGateway $gateway, // Concrete class
    ) {}
}

// GOOD: Interface dependency
class PaymentProcessor
{
    public function __construct(
        private PaymentGatewayInterface $gateway, // Interface
    ) {}
}
```

### 5. Hidden Dependencies

```php
// BAD: Uses global/superglobal
class UserController
{
    public function current(): User
    {
        $userId = $_SESSION['user_id']; // Hidden dependency
        return $this->repository->find($userId);
    }
}

// GOOD: Explicit dependency
class UserController
{
    public function __construct(
        private SessionInterface $session,
        private UserRepository $repository,
    ) {}

    public function current(): User
    {
        $userId = $this->session->get('user_id');
        return $this->repository->find($userId);
    }
}
```

### 6. Setter Injection Issues

```php
// BAD: Optional setter injection
class OrderService
{
    private ?Logger $logger = null;

    public function setLogger(Logger $logger): void
    {
        $this->logger = $logger;
    }

    public function process(): void
    {
        $this->logger?->info('Processing'); // May be null
    }
}

// GOOD: Constructor injection
class OrderService
{
    public function __construct(
        private LoggerInterface $logger,
    ) {}

    public function process(): void
    {
        $this->logger->info('Processing');
    }
}
```

### 7. Factory Inside Class

```php
// BAD: Factory logic in service
class NotificationService
{
    public function send(string $type, string $message): void
    {
        $channel = match($type) {
            'email' => new EmailChannel(),
            'sms' => new SmsChannel(),
            'push' => new PushChannel(),
        };
        $channel->send($message);
    }
}

// GOOD: Inject factory
class NotificationService
{
    public function __construct(
        private ChannelFactory $channelFactory,
    ) {}

    public function send(string $type, string $message): void
    {
        $channel = $this->channelFactory->create($type);
        $channel->send($message);
    }
}
```

### 8. Environment/Config Access

```php
// BAD: Direct environment access
class ApiClient
{
    public function request(): Response
    {
        $key = getenv('API_KEY'); // Hidden dependency
        // ...
    }
}

// GOOD: Config injection
class ApiClient
{
    public function __construct(
        private string $apiKey, // Or ApiConfig object
    ) {}
}
```

## Grep Patterns

```bash
# New keyword in methods
Grep: "new\s+[A-Z]\w+\(" --glob "**/*.php"

# Service locator
Grep: "Container::(get|make)|App::(make|resolve)" --glob "**/*.php"

# Static method calls
Grep: "[A-Z]\w+::\w+\(" --glob "**/*.php"

# Superglobals
Grep: "\$_(GET|POST|SESSION|COOKIE|ENV|SERVER)" --glob "**/*.php"

# getenv/putenv
Grep: "(getenv|putenv)\(" --glob "**/*.php"
```

## Acceptable Uses of New

```php
// OK: Value objects and DTOs
new Money(100, 'USD');
new DateTime('now');
new OrderId($uuid);

// OK: Exceptions
throw new InvalidArgumentException();

// OK: In factories (that's their job)
class UserFactory {
    public function create(): User {
        return new User();
    }
}
```

## Severity Classification

| Pattern | Severity |
|---------|----------|
| Service locator | 🟠 Major |
| New keyword for services | 🟠 Major |
| Static method calls | 🟠 Major |
| Superglobal access | 🟠 Major |
| Missing interface | 🟡 Minor |
| Setter injection | 🟡 Minor |

## Output Format

```markdown
### DI Issue: [Description]

**Severity:** 🟠/🟡
**Location:** `file.php:line`
**Type:** [Service Locator|New Keyword|Static Call|...]

**Issue:**
[Description of the DI problem]

**Current:**
```php
$mailer = new Mailer();
```

**Suggested:**
```php
public function __construct(
    private MailerInterface $mailer,
) {}
```

**Testing Impact:**
Cannot mock Mailer in unit tests. With injection, tests can use MockMailer.
```
