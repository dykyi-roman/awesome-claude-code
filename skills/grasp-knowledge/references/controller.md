# Controller Pattern

## Definition

Assign responsibility for handling system events to a class that represents the overall system (facade controller) or a use-case scenario (use-case controller).

## When to Apply

- Handling external system events (HTTP, CLI, messages)
- Coordinating use case execution
- Separating UI from domain logic

## Key Indicators

### Violation Signs

| Indicator | Detection | Severity |
|-----------|-----------|----------|
| Fat controller | >100 lines | CRITICAL |
| Business logic | `if/else` in controller | CRITICAL |
| Direct DB access | Repository in controller | WARNING |
| Many dependencies | >5 injected | WARNING |

### Compliance Signs

- Thin controller (< 50 lines)
- Delegates to use case/handler
- Only maps input/output
- Single responsibility

## Patterns

### Thin Controller

```php
<?php

declare(strict_types=1);

// GOOD: Controller only coordinates
final readonly class OrderController
{
    public function __construct(
        private CreateOrderHandler $createHandler,
        private GetOrderHandler $getHandler,
        private CancelOrderHandler $cancelHandler,
    ) {}

    public function create(CreateOrderRequest $request): JsonResponse
    {
        $command = new CreateOrderCommand(
            customerId: $request->customerId(),
            items: $request->items(),
            shippingAddress: $request->shippingAddress(),
        );

        $orderId = ($this->createHandler)($command);

        return new JsonResponse(['id' => $orderId->value], 201);
    }

    public function show(string $id): JsonResponse
    {
        $query = new GetOrderQuery(new OrderId($id));
        $order = ($this->getHandler)($query);

        return new JsonResponse($order);
    }

    public function cancel(string $id): JsonResponse
    {
        $command = new CancelOrderCommand(new OrderId($id));
        ($this->cancelHandler)($command);

        return new JsonResponse(null, 204);
    }
}
```

### Use Case Handler

```php
<?php

declare(strict_types=1);

// Application Controller / Use Case
final readonly class CreateOrderHandler
{
    public function __construct(
        private OrderFactory $factory,
        private OrderRepository $orders,
        private EventDispatcher $events,
    ) {}

    public function __invoke(CreateOrderCommand $command): OrderId
    {
        // Coordinate domain objects
        $order = $this->factory->create($command);

        // Persist
        $this->orders->save($order);

        // Dispatch events
        $this->events->dispatch(...$order->releaseEvents());

        return $order->id;
    }
}
```

### Command/Query Objects

```php
<?php

declare(strict_types=1);

// Command: Intent to change state
final readonly class CreateOrderCommand
{
    public function __construct(
        public CustomerId $customerId,
        public array $items,
        public Address $shippingAddress,
    ) {}
}

// Query: Request for data
final readonly class GetOrderQuery
{
    public function __construct(
        public OrderId $orderId,
    ) {}
}

final readonly class GetOrderHandler
{
    public function __construct(
        private OrderReadRepository $orders,
    ) {}

    public function __invoke(GetOrderQuery $query): OrderDTO
    {
        $order = $this->orders->find($query->orderId);

        if ($order === null) {
            throw new OrderNotFoundException($query->orderId);
        }

        return $order;
    }
}
```

### API Action (Single-Action Controller)

```php
<?php

declare(strict_types=1);

// Single responsibility: one action per controller class
final readonly class CreateOrderAction
{
    public function __construct(
        private CreateOrderHandler $handler,
    ) {}

    public function __invoke(CreateOrderRequest $request): JsonResponse
    {
        try {
            $orderId = ($this->handler)(
                new CreateOrderCommand(
                    customerId: $request->customerId(),
                    items: $request->items(),
                    shippingAddress: $request->shippingAddress(),
                ),
            );

            return new JsonResponse(['id' => $orderId->value], 201);
        } catch (InsufficientStockException $e) {
            return new JsonResponse(['error' => $e->getMessage()], 422);
        }
    }
}
```

### Console Command Controller

```php
<?php

declare(strict_types=1);

// CLI controller delegates to handler
final class ImportOrdersCommand extends Command
{
    public function __construct(
        private ImportOrdersHandler $handler,
    ) {
        parent::__construct();
    }

    protected function configure(): void
    {
        $this
            ->setName('orders:import')
            ->addArgument('file', InputArgument::REQUIRED);
    }

    protected function execute(InputInterface $input, OutputInterface $output): int
    {
        $file = $input->getArgument('file');

        try {
            $result = ($this->handler)(new ImportOrdersCommand($file));

            $output->writeln(sprintf('Imported %d orders', $result->count));

            return Command::SUCCESS;
        } catch (ImportException $e) {
            $output->writeln(sprintf('<error>%s</error>', $e->getMessage()));

            return Command::FAILURE;
        }
    }
}
```

### Message Handler Controller

```php
<?php

declare(strict_types=1);

// Message queue controller
final readonly class OrderPlacedMessageHandler
{
    public function __construct(
        private SendOrderConfirmationHandler $sendConfirmation,
        private UpdateInventoryHandler $updateInventory,
    ) {}

    public function __invoke(OrderPlacedMessage $message): void
    {
        // Coordinate reactions to event
        ($this->sendConfirmation)(
            new SendConfirmationCommand($message->orderId),
        );

        ($this->updateInventory)(
            new UpdateInventoryCommand($message->orderId, $message->items),
        );
    }
}
```

## Anti-patterns

### Fat Controller

```php
<?php

// ANTIPATTERN: Controller does too much
final class OrderController
{
    public function create(Request $request): Response
    {
        // Validation (should be in Request class)
        if (empty($request->get('items'))) {
            return new JsonResponse(['error' => 'Items required'], 400);
        }

        // Business logic (should be in domain/handler)
        $customer = $this->customerRepository->find($request->get('customer_id'));
        if ($customer === null) {
            return new JsonResponse(['error' => 'Customer not found'], 404);
        }

        $order = new Order();
        $order->setCustomer($customer);

        $total = Money::zero();
        foreach ($request->get('items') as $item) {
            $product = $this->productRepository->find($item['id']);
            if ($product->getStock() < $item['quantity']) {
                return new JsonResponse(['error' => 'Insufficient stock'], 422);
            }

            $product->decreaseStock($item['quantity']);
            $this->productRepository->save($product);

            $line = new OrderLine();
            $line->setProduct($product);
            $line->setQuantity($item['quantity']);
            $order->addLine($line);

            $total = $total->add($product->getPrice()->multiply($item['quantity']));
        }

        // More business logic...
        if ($total->isGreaterThan(Money::fromCents(100000))) {
            $this->notificationService->alertHighValueOrder($order);
        }

        $this->orderRepository->save($order);

        // Side effects
        $this->mailer->send(new OrderConfirmationEmail($order));
        $this->logger->info('Order created', ['id' => $order->getId()]);

        return new JsonResponse(['id' => $order->getId()]);
    }
}
```

### Direct Domain Access

```php
<?php

// ANTIPATTERN: Controller directly manipulates domain
final class UserController
{
    public function activate(string $id): Response
    {
        $user = $this->userRepository->find(new UserId($id));
        $user->setStatus(UserStatus::Active); // Direct mutation!
        $user->setActivatedAt(new DateTimeImmutable()); // Direct mutation!
        $this->userRepository->save($user);

        return new JsonResponse(['status' => 'activated']);
    }
}

// FIX: Delegate to handler
final readonly class UserController
{
    public function activate(string $id): Response
    {
        ($this->activateHandler)(new ActivateUserCommand(new UserId($id)));

        return new JsonResponse(['status' => 'activated']);
    }
}
```

## Layer Separation

```
┌─────────────────────────────────────────────────┐
│                 Presentation                     │
│  (Controllers, Actions, CLI Commands)           │
│  - Map input to Command/Query                   │
│  - Call handler                                 │
│  - Map result to response                       │
├─────────────────────────────────────────────────┤
│                  Application                     │
│  (Handlers, Use Cases, Application Services)    │
│  - Coordinate domain objects                    │
│  - Manage transactions                          │
│  - Dispatch events                              │
├─────────────────────────────────────────────────┤
│                    Domain                        │
│  (Entities, Value Objects, Domain Services)     │
│  - Business logic                               │
│  - Invariants                                   │
└─────────────────────────────────────────────────┘
```

## Metrics

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| Controller lines | <50 | 50-100 | >100 |
| Dependencies | ≤3 | 4-5 | >5 |
| Conditionals | 0-1 | 2-3 | >3 |
| Domain calls | 1 (handler) | 2-3 | >3 |
