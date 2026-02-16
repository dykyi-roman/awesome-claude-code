# Adapters Patterns

Detailed patterns for Hexagonal Architecture Adapters in PHP.

## Adapter Definition

### What is an Adapter?

An Adapter connects the application core to external systems by implementing or using ports. Adapters contain all technology-specific code.

### Adapter Types

| Type | Direction | Purpose | Example |
|------|-----------|---------|---------|
| **Driving Adapter** | Inbound | Receives external input | HTTP Controller, CLI Command |
| **Driven Adapter** | Outbound | Provides external output | Repository, API Client |

## Driving Adapters (Primary)

### Definition

Adapters that receive input from external actors and call the application core through driving ports.

### Location

Infrastructure layer — these are framework-specific implementations.

### HTTP Controller Adapter

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Http\Controller\Order;

use Application\Order\Port\Input\CreateOrderUseCaseInterface;
use Application\Order\DTO\CreateOrderRequest;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;

final readonly class CreateOrderController
{
    public function __construct(
        private CreateOrderUseCaseInterface $createOrder
    ) {}

    public function __invoke(Request $request): JsonResponse
    {
        try {
            $dto = CreateOrderRequest::fromArray($request->toArray());

            $response = $this->createOrder->execute($dto);

            return new JsonResponse(
                $response->toArray(),
                Response::HTTP_CREATED
            );
        } catch (ValidationException $e) {
            return new JsonResponse(
                ['errors' => $e->getErrors()],
                Response::HTTP_BAD_REQUEST
            );
        }
    }
}
```

### CLI Command Adapter

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Console\Command;

use Application\Order\Port\Input\ProcessPendingOrdersUseCaseInterface;
use Symfony\Component\Console\Attribute\AsCommand;
use Symfony\Component\Console\Command\Command;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Output\OutputInterface;

#[AsCommand(name: 'order:process-pending')]
final class ProcessPendingOrdersCommand extends Command
{
    public function __construct(
        private readonly ProcessPendingOrdersUseCaseInterface $processPendingOrders
    ) {
        parent::__construct();
    }

    protected function execute(InputInterface $input, OutputInterface $output): int
    {
        $result = $this->processPendingOrders->execute();

        $output->writeln("Processed {$result->count} orders");

        return Command::SUCCESS;
    }
}
```

### Message Consumer Adapter

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Messaging\Consumer;

use Application\Order\Port\Input\HandlePaymentReceivedUseCaseInterface;
use Application\Order\DTO\PaymentReceivedRequest;
use Symfony\Component\Messenger\Attribute\AsMessageHandler;

#[AsMessageHandler]
final readonly class PaymentReceivedHandler
{
    public function __construct(
        private HandlePaymentReceivedUseCaseInterface $handlePaymentReceived
    ) {}

    public function __invoke(PaymentReceivedMessage $message): void
    {
        $request = new PaymentReceivedRequest(
            orderId: $message->orderId,
            transactionId: $message->transactionId,
            amount: $message->amount
        );

        $this->handlePaymentReceived->execute($request);
    }
}
```

### GraphQL Resolver Adapter

```php
<?php

declare(strict_types=1);

namespace Infrastructure\GraphQL\Resolver;

use Application\Order\Port\Input\GetOrderUseCaseInterface;
use Application\Order\DTO\GetOrderRequest;

final readonly class OrderResolver
{
    public function __construct(
        private GetOrderUseCaseInterface $getOrder
    ) {}

    public function resolve(string $id): array
    {
        $request = new GetOrderRequest(orderId: $id);

        $response = $this->getOrder->execute($request);

        return $response->toArray();
    }
}
```

## Driven Adapters (Secondary)

### Definition

Adapters that implement driven ports to provide external functionality to the application core.

### Location

Infrastructure layer — these are technology-specific implementations.

### Repository Adapter (Doctrine)

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Persistence\Doctrine;

use Domain\Order\Entity\Order;
use Domain\Order\Port\Output\OrderRepositoryInterface;
use Domain\Order\ValueObject\OrderId;
use Domain\Order\ValueObject\CustomerId;
use Doctrine\ORM\EntityManagerInterface;

final readonly class DoctrineOrderRepository implements OrderRepositoryInterface
{
    public function __construct(
        private EntityManagerInterface $em
    ) {}

    public function findById(OrderId $id): ?Order
    {
        return $this->em->find(Order::class, $id->value);
    }

    public function findByCustomerId(CustomerId $customerId): array
    {
        return $this->em->createQueryBuilder()
            ->select('o')
            ->from(Order::class, 'o')
            ->where('o.customerId = :customerId')
            ->setParameter('customerId', $customerId->value)
            ->getQuery()
            ->getResult();
    }

    public function save(Order $order): void
    {
        $this->em->persist($order);
        $this->em->flush();
    }

    public function remove(Order $order): void
    {
        $this->em->remove($order);
        $this->em->flush();
    }

    public function nextIdentity(): OrderId
    {
        return OrderId::generate();
    }
}
```

### External API Adapter

```php
<?php

declare(strict_types=1);

namespace Infrastructure\ExternalService\Payment;

use Application\Payment\Port\Output\PaymentGatewayInterface;
use Application\Payment\DTO\PaymentRequest;
use Application\Payment\DTO\PaymentResponse;
use Application\Payment\DTO\RefundResponse;
use Stripe\StripeClient;
use Stripe\Exception\CardException;

final readonly class StripePaymentAdapter implements PaymentGatewayInterface
{
    public function __construct(
        private StripeClient $stripe
    ) {}

    public function charge(PaymentRequest $request): PaymentResponse
    {
        try {
            $charge = $this->stripe->charges->create([
                'amount' => $request->amount,
                'currency' => $request->currency,
                'source' => $request->token,
                'metadata' => ['order_id' => $request->orderId],
            ]);

            return PaymentResponse::success(
                transactionId: $charge->id,
                amount: $charge->amount
            );
        } catch (CardException $e) {
            return PaymentResponse::failed(
                errorCode: $e->getStripeCode(),
                errorMessage: $e->getMessage()
            );
        }
    }

    public function refund(string $transactionId, int $amount): RefundResponse
    {
        $refund = $this->stripe->refunds->create([
            'charge' => $transactionId,
            'amount' => $amount,
        ]);

        return new RefundResponse(
            refundId: $refund->id,
            status: $refund->status
        );
    }
}
```

### Message Publisher Adapter

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Messaging\Publisher;

use Application\Shared\Port\Output\EventPublisherInterface;
use Domain\Shared\Event\DomainEvent;
use Symfony\Component\Messenger\MessageBusInterface;

final readonly class MessengerEventPublisher implements EventPublisherInterface
{
    public function __construct(
        private MessageBusInterface $messageBus
    ) {}

    public function publish(DomainEvent $event): void
    {
        $this->messageBus->dispatch($event);
    }

    public function publishAll(array $events): void
    {
        foreach ($events as $event) {
            $this->publish($event);
        }
    }
}
```

### Cache Adapter

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Cache;

use Application\Order\Port\Output\OrderCacheInterface;
use Application\Order\DTO\OrderDTO;
use Psr\Cache\CacheItemPoolInterface;

final readonly class RedisOrderCache implements OrderCacheInterface
{
    private const TTL = 3600;

    public function __construct(
        private CacheItemPoolInterface $cache
    ) {}

    public function get(string $orderId): ?OrderDTO
    {
        $item = $this->cache->getItem($this->key($orderId));

        if (!$item->isHit()) {
            return null;
        }

        return OrderDTO::fromArray($item->get());
    }

    public function set(string $orderId, OrderDTO $order): void
    {
        $item = $this->cache->getItem($this->key($orderId));
        $item->set($order->toArray());
        $item->expiresAfter(self::TTL);
        $this->cache->save($item);
    }

    public function invalidate(string $orderId): void
    {
        $this->cache->deleteItem($this->key($orderId));
    }

    private function key(string $orderId): string
    {
        return "order:{$orderId}";
    }
}
```

## Adapter Design Guidelines

### 1. No Business Logic

```php
// GOOD: Only translation and delegation
final readonly class CreateOrderController
{
    public function __invoke(Request $request): JsonResponse
    {
        $dto = CreateOrderRequest::fromArray($request->toArray());
        $response = $this->createOrder->execute($dto);
        return new JsonResponse($response->toArray(), 201);
    }
}

// BAD: Business logic in adapter
final readonly class CreateOrderController
{
    public function __invoke(Request $request): JsonResponse
    {
        // BAD: Business logic
        if ($request->get('total') > 10000) {
            $request->set('requires_approval', true);
        }

        // BAD: Validation logic
        if (!$this->customerService->isActive($request->get('customer_id'))) {
            throw new InactiveCustomerException();
        }

        $dto = CreateOrderRequest::fromArray($request->toArray());
        // ...
    }
}
```

### 2. Error Translation

```php
final readonly class CreateOrderController
{
    public function __invoke(Request $request): JsonResponse
    {
        try {
            $response = $this->createOrder->execute($dto);
            return new JsonResponse($response->toArray(), 201);
        } catch (OrderNotFoundException $e) {
            // Translate domain exception to HTTP response
            return new JsonResponse(
                ['error' => 'Order not found'],
                Response::HTTP_NOT_FOUND
            );
        } catch (InsufficientInventoryException $e) {
            return new JsonResponse(
                ['error' => 'Insufficient inventory', 'product' => $e->productId],
                Response::HTTP_CONFLICT
            );
        }
    }
}
```

### 3. Adapter Composition

```php
// Decorator pattern for cross-cutting concerns
final readonly class LoggingPaymentAdapter implements PaymentGatewayInterface
{
    public function __construct(
        private PaymentGatewayInterface $inner,
        private LoggerInterface $logger
    ) {}

    public function charge(PaymentRequest $request): PaymentResponse
    {
        $this->logger->info('Processing payment', ['order' => $request->orderId]);

        $response = $this->inner->charge($request);

        $this->logger->info('Payment processed', [
            'order' => $request->orderId,
            'success' => $response->isSuccess(),
        ]);

        return $response;
    }
}
```

## Adapter Organization

### Directory Structure

```
Infrastructure/
├── Http/
│   └── Controller/
│       ├── Order/
│       │   ├── CreateOrderController.php
│       │   └── GetOrderController.php
│       └── Payment/
│           └── ProcessPaymentController.php
├── Console/
│   └── Command/
│       └── ProcessPendingOrdersCommand.php
├── Messaging/
│   ├── Consumer/
│   │   └── PaymentReceivedHandler.php
│   └── Publisher/
│       └── MessengerEventPublisher.php
├── Persistence/
│   └── Doctrine/
│       ├── DoctrineOrderRepository.php
│       └── DoctrineCustomerRepository.php
├── ExternalService/
│   ├── Payment/
│   │   └── StripePaymentAdapter.php
│   └── Shipping/
│       └── FedExShippingAdapter.php
└── Cache/
    └── RedisOrderCache.php
```

## Detection Patterns

```bash
# Find driving adapters
Glob: **/Infrastructure/Http/**/*.php
Glob: **/Infrastructure/Console/**/*.php
Glob: **/Infrastructure/Messaging/Consumer/**/*.php

# Find driven adapters
Grep: "implements.*Interface" --glob "**/Infrastructure/**/*.php"

# Check adapters use ports
Grep: "UseCaseInterface|RepositoryInterface|GatewayInterface" --glob "**/Infrastructure/**/*.php"

# Warning: Business logic in adapter
Grep: "if \(.*->|switch \(" --glob "**/Infrastructure/Http/**/*.php"
```
