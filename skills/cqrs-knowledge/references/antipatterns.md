# CQRS Antipatterns

Common CQRS violations with detection patterns and fixes.

## Critical Violations

### 1. Query with Side Effects

**Description:** Query handler modifies state.

**Why Critical:** Breaks fundamental CQRS principle. Queries should be safe to repeat.

**Detection:**
```bash
Grep: "->save\(|->persist\(|->remove\(|->delete\(" --glob "**/Query/**/*Handler.php"
Grep: "->dispatch\(" --glob "**/Query/**/*Handler.php"
Grep: "INSERT|UPDATE|DELETE" --glob "**/Query/**/*.php"
```

**Bad:**
```php
namespace Application\Order\Query;

final readonly class GetOrderDetailsHandler
{
    public function __invoke(GetOrderDetailsQuery $query): OrderDetailsDTO
    {
        $order = $this->readModel->findById($query->orderId);

        // CRITICAL: Side effects in query
        $this->repository->incrementViewCount($query->orderId);
        $this->eventDispatcher->dispatch(new OrderViewedEvent($query->orderId));
        $this->logger->info('Order viewed');  // Even logging can be problematic

        return $order;
    }
}
```

**Good:**
```php
namespace Application\Order\Query;

final readonly class GetOrderDetailsHandler
{
    public function __invoke(GetOrderDetailsQuery $query): ?OrderDetailsDTO
    {
        // Pure read, no side effects
        return $this->readModel->findById($query->orderId);
    }
}

// If analytics needed, use separate mechanism (e.g., frontend tracking)
```

### 2. Command Returning Rich Data

**Description:** Command handler returns domain entity or complex data.

**Why Critical:** Commands should trigger state changes, not return state. Use queries for data.

**Detection:**
```bash
Grep: "function __invoke.*Command.*\): (Order|User|Product|Customer|Entity)" --glob "**/*Handler.php"
Grep: "return \$this->repository->find" --glob "**/Command/**/*Handler.php"
Grep: "return \$order;|return \$user;|return \$entity;" --glob "**/Command/**/*Handler.php"
```

**Bad:**
```php
namespace Application\Order\Command;

final readonly class CreateOrderHandler
{
    public function __invoke(CreateOrderCommand $command): Order  // Returns entity!
    {
        $order = Order::create(...);
        $this->repository->save($order);
        return $order;  // CRITICAL: Returns rich domain object
    }
}

// Controller
public function create(Request $request): JsonResponse
{
    $order = $this->commandBus->dispatch($command);
    return new JsonResponse($order->toArray());  // Using command result as query
}
```

**Good:**
```php
namespace Application\Order\Command;

final readonly class CreateOrderHandler
{
    public function __invoke(CreateOrderCommand $command): OrderId
    {
        $order = Order::create(
            id: OrderId::generate(),
            ...
        );
        $this->repository->save($order);
        return $order->id();  // Only returns ID
    }
}

// Controller - use query for data
public function create(Request $request): JsonResponse
{
    $orderId = $this->commandBus->dispatch($command);

    // Separate query for response data
    $orderDetails = $this->queryBus->dispatch(
        new GetOrderDetailsQuery($orderId)
    );

    return new JsonResponse($orderDetails);
}
```

### 3. Mixed Read/Write Handler

**Description:** Single handler that both reads and writes, blurring CQRS separation.

**Why Critical:** Makes it unclear if operation is safe to retry, cache, or parallelize.

**Detection:**
```bash
# Find handlers with both query-like and command-like patterns
Grep: "findById.*save\(|find.*persist\(" --glob "**/*Handler.php"
```

**Bad:**
```php
// This handler is both query AND command
final readonly class GetOrCreateCustomerHandler
{
    public function __invoke(GetOrCreateCustomerCommand $command): Customer
    {
        $customer = $this->repository->findByEmail($command->email);

        if ($customer === null) {
            // Write operation
            $customer = Customer::register($command->email, $command->name);
            $this->repository->save($customer);
        }

        return $customer;  // Read operation
    }
}
```

**Good:**
```php
// Separate into two operations
final readonly class FindCustomerByEmailHandler
{
    public function __invoke(FindCustomerByEmailQuery $query): ?CustomerDTO
    {
        return $this->readModel->findByEmail($query->email);
    }
}

final readonly class RegisterCustomerHandler
{
    public function __invoke(RegisterCustomerCommand $command): CustomerId
    {
        // Check if exists first (in controller or application service)
        $customer = Customer::register($command->email, $command->name);
        $this->repository->save($customer);
        return $customer->id();
    }
}

// Controller orchestrates
public function getOrCreate(Request $request): JsonResponse
{
    $existing = $this->queryBus->dispatch(
        new FindCustomerByEmailQuery($request->get('email'))
    );

    if ($existing !== null) {
        return new JsonResponse($existing);
    }

    $customerId = $this->commandBus->dispatch(
        new RegisterCustomerCommand(
            email: $request->get('email'),
            name: $request->get('name')
        )
    );

    return new JsonResponse(
        $this->queryBus->dispatch(new GetCustomerQuery($customerId)),
        201
    );
}
```

## Warnings

### 4. Business Logic in Handler

**Description:** Handler contains domain logic instead of delegating to domain objects.

**Why Bad:** Domain logic scattered, hard to test, violates DDD.

**Detection:**
```bash
Grep: "if \(.*->get.*\(\) ===|if \(.*->status|if \(.*->state" --glob "**/*Handler.php"
Grep: "switch \(.*->get" --glob "**/*Handler.php"
Grep: "foreach.*calculate|foreach.*validate" --glob "**/*Handler.php"
```

**Bad:**
```php
final readonly class ConfirmOrderHandler
{
    public function __invoke(ConfirmOrderCommand $command): void
    {
        $order = $this->repository->findById($command->orderId);

        // BAD: Business logic in handler
        if ($order->getStatus() === 'draft') {
            if (count($order->getLines()) > 0) {
                if ($order->getTotal() > 0) {
                    $order->setStatus('confirmed');
                    $order->setConfirmedAt(new \DateTimeImmutable());
                }
            }
        }

        $this->repository->save($order);
    }
}
```

**Good:**
```php
final readonly class ConfirmOrderHandler
{
    public function __invoke(ConfirmOrderCommand $command): void
    {
        $order = $this->repository->findById($command->orderId);

        if ($order === null) {
            throw new OrderNotFoundException($command->orderId);
        }

        // Delegate to domain object
        $order->confirm();

        $this->repository->save($order);
    }
}

// Domain object has the logic
final class Order
{
    public function confirm(): void
    {
        if (!$this->canBeConfirmed()) {
            throw new InvalidStateTransitionException();
        }
        $this->status = OrderStatus::Confirmed;
        $this->confirmedAt = new \DateTimeImmutable();
    }

    private function canBeConfirmed(): bool
    {
        return $this->status === OrderStatus::Draft
            && !empty($this->lines)
            && $this->total()->isPositive();
    }
}
```

### 5. Query Using Write Database

**Description:** Query handler reads from the same database/model used for writes.

**Why Bad:** Misses CQRS benefits (read optimization, scaling). May read stale data during transactions.

**Detection:**
```bash
Grep: "EntityManager|EntityRepository" --glob "**/Query/**/*Handler.php"
Grep: "Repository" --glob "**/Query/**/*Handler.php" | grep -v "ReadModel\|ReadRepository"
```

**Bad:**
```php
final readonly class GetOrderDetailsHandler
{
    public function __construct(
        private OrderRepositoryInterface $orderRepository  // Write repository
    ) {}

    public function __invoke(GetOrderDetailsQuery $query): OrderDetailsDTO
    {
        // Using write model for read
        $order = $this->orderRepository->findById($query->orderId);

        return OrderDetailsDTO::fromEntity($order);
    }
}
```

**Good:**
```php
final readonly class GetOrderDetailsHandler
{
    public function __construct(
        private OrderReadModelInterface $readModel  // Read-optimized
    ) {}

    public function __invoke(GetOrderDetailsQuery $query): ?OrderDetailsDTO
    {
        // Using dedicated read model
        return $this->readModel->findById($query->orderId);
    }
}
```

### 6. Missing Command Validation

**Description:** Commands accepted without input validation.

**Why Bad:** Invalid commands reach domain, causing unclear errors.

**Detection:**
```bash
# Commands without validation in constructor
Grep: "readonly class.*Command\s*\{" --glob "**/*Command.php" -A 10 | grep -v "throw\|if \("
```

**Bad:**
```php
final readonly class CreateOrderCommand
{
    public function __construct(
        public string $customerId,  // Not validated
        public array $lines         // Not validated
    ) {}
}
```

**Good:**
```php
final readonly class CreateOrderCommand
{
    public function __construct(
        public CustomerId $customerId,  // Value object validates
        /** @var non-empty-array<OrderLineData> */
        public array $lines
    ) {
        if (empty($lines)) {
            throw new InvalidArgumentException('Order must have at least one line');
        }
    }
}
```

### 7. Query Named Like Command

**Description:** Query with imperative naming suggesting mutation.

**Why Bad:** Confusing API, unclear intent.

**Detection:**
```bash
Grep: "class (Create|Update|Delete|Process|Execute|Run).*Query" --glob "**/*.php"
```

**Bad:**
```php
class UpdateOrderStatusQuery { }  // Is this read or write?
class ProcessOrderQuery { }        // Sounds like command
class ExecuteReportQuery { }       // Confusing
```

**Good:**
```php
class GetOrderStatusQuery { }      // Clear read intent
class GetOrderQuery { }            // Clear read intent
class GetReportDataQuery { }       // Clear read intent
```

### 8. Command Named Like Query

**Description:** Command with interrogative naming suggesting read.

**Why Bad:** Confusing API, unclear intent.

**Detection:**
```bash
Grep: "class (Get|Find|List|Search|Fetch).*Command" --glob "**/*.php"
```

**Bad:**
```php
class GetOrderCommand { }      // Sounds like query
class FindUserCommand { }      // Sounds like query
class ListProductsCommand { }  // Sounds like query
```

**Good:**
```php
class RetrieveOrderCommand { }  // If it's actually a command (rare)
// Usually these should just be queries
```

### 9. Handler Handling Multiple Messages

**Description:** Single handler class handles multiple commands/queries.

**Why Bad:** Violates SRP, hard to test, hard to maintain.

**Detection:**
```bash
Grep: "public function handle.*Command|public function handle.*Query" --glob "**/*Handler.php" | sort | uniq -d
# Or look for multiple public methods
```

**Bad:**
```php
class OrderHandler
{
    public function handleCreate(CreateOrderCommand $cmd): void { }
    public function handleConfirm(ConfirmOrderCommand $cmd): void { }
    public function handleCancel(CancelOrderCommand $cmd): void { }
}
```

**Good:**
```php
final readonly class CreateOrderHandler
{
    public function __invoke(CreateOrderCommand $cmd): OrderId { }
}

final readonly class ConfirmOrderHandler
{
    public function __invoke(ConfirmOrderCommand $cmd): void { }
}

final readonly class CancelOrderHandler
{
    public function __invoke(CancelOrderCommand $cmd): void { }
}
```

### 10. Synchronous Query in Command Handler

**Description:** Command handler queries data synchronously for decision making.

**Why Bad:** May cause consistency issues if read model is eventually consistent.

**Detection:**
```bash
Grep: "QueryBus|readModel->find" --glob "**/Command/**/*Handler.php"
```

**Bad:**
```php
final readonly class ConfirmOrderHandler
{
    public function __invoke(ConfirmOrderCommand $command): void
    {
        // BAD: Using read model in command handler
        $customerStatus = $this->queryBus->dispatch(
            new GetCustomerStatusQuery($command->customerId)
        );

        if ($customerStatus->isSuspended()) {
            throw new CustomerSuspendedException();
        }

        // ...
    }
}
```

**Good:**
```php
final readonly class ConfirmOrderHandler
{
    public function __invoke(ConfirmOrderCommand $command): void
    {
        $order = $this->orderRepository->findById($command->orderId);

        // Use write model / domain for decisions
        $customer = $this->customerRepository->findById($order->customerId());

        if ($customer->isSuspended()) {
            throw new CustomerSuspendedException();
        }

        $order->confirm();
        // ...
    }
}
```

## Severity Matrix

| Antipattern | Severity | Impact | Fix Effort |
|-------------|----------|--------|------------|
| Query with side effects | Critical | Data integrity | Medium |
| Command returning entity | Critical | Architecture | Medium |
| Mixed read/write handler | Critical | Architecture | High |
| Business logic in handler | Warning | Maintainability | Medium |
| Query using write DB | Warning | Performance | High |
| Missing command validation | Warning | Reliability | Low |
| Wrong naming convention | Warning | Readability | Low |
| Multi-message handler | Warning | Maintainability | Medium |
| Sync query in command | Warning | Consistency | Medium |
