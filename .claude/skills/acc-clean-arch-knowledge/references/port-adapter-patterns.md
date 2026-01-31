# Port & Adapter Patterns

Detailed patterns for Hexagonal Architecture (Ports & Adapters) in PHP.

## Hexagonal Architecture Overview

```
                    ┌─────────────────────┐
                    │   PRIMARY ACTORS    │
                    │ (Users, Other Apps) │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  DRIVING ADAPTERS   │
                    │ (Controllers, CLI,  │
                    │  Message Handlers)  │
                    └──────────┬──────────┘
                               │
              ┌────────────────▼────────────────┐
              │         DRIVING PORTS           │
              │    (Input Boundaries/APIs)      │
              └────────────────┬────────────────┘
                               │
              ┌────────────────▼────────────────┐
              │          APPLICATION            │
              │        (Use Cases/Core)         │
              └────────────────┬────────────────┘
                               │
              ┌────────────────▼────────────────┐
              │         DRIVEN PORTS            │
              │ (Output Boundaries/Interfaces)  │
              └────────────────┬────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │   DRIVEN ADAPTERS   │
                    │ (Repositories, APIs,│
                    │  Message Queues)    │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  SECONDARY ACTORS   │
                    │ (DB, APIs, Services)│
                    └─────────────────────┘
```

## Port Types

### Driving Ports (Primary/Input)

Interfaces through which external actors interact with the application.

**Location:** Application layer

**Purpose:** Define how the application can be used

```php
<?php

declare(strict_types=1);

namespace Application\Order\Port;

use Application\Order\Command\CreateOrderCommand;
use Application\Order\Query\GetOrderQuery;
use Domain\Order\ValueObject\OrderId;

// Driving port for command handling
interface CreateOrderUseCaseInterface
{
    public function execute(CreateOrderCommand $command): OrderId;
}

// Driving port for query handling
interface GetOrderQueryInterface
{
    public function execute(GetOrderQuery $query): ?OrderDTO;
}
```

### Driven Ports (Secondary/Output)

Interfaces through which the application interacts with external systems.

**Location:** Application layer (for application concerns) or Domain layer (for persistence)

**Purpose:** Define what the application needs from the outside world

```php
<?php

declare(strict_types=1);

namespace Application\Order\Port;

// Driven port for external payment service
interface PaymentGatewayInterface
{
    public function charge(PaymentRequest $request): PaymentResponse;
    public function refund(string $transactionId, Money $amount): RefundResponse;
}

// Driven port for external notification service
interface NotificationServiceInterface
{
    public function sendEmail(EmailMessage $message): void;
    public function sendSms(SmsMessage $message): void;
}

// Driven port for external inventory service
interface InventoryServiceInterface
{
    public function reserve(ProductId $productId, int $quantity): ReservationId;
    public function release(ReservationId $reservationId): void;
}
```

## Adapter Types

### Driving Adapters (Primary)

Implementations that receive input and call the application.

**Location:** Presentation/Infrastructure layer

**Examples:** HTTP Controllers, CLI Commands, Message Consumers

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\Order;

use Application\Order\Port\CreateOrderUseCaseInterface;
use Application\Order\Command\CreateOrderCommand;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;

// HTTP Driving Adapter
final readonly class CreateOrderController
{
    public function __construct(
        private CreateOrderUseCaseInterface $createOrder
    ) {}

    public function __invoke(Request $request): JsonResponse
    {
        $command = CreateOrderCommand::fromArray($request->toArray());

        $orderId = $this->createOrder->execute($command);

        return new JsonResponse(
            ['id' => $orderId->value],
            JsonResponse::HTTP_CREATED
        );
    }
}
```

```php
<?php

declare(strict_types=1);

namespace Presentation\Console\Order;

use Application\Order\Port\CreateOrderUseCaseInterface;
use Symfony\Component\Console\Command\Command;

// CLI Driving Adapter
final class CreateOrderConsoleCommand extends Command
{
    public function __construct(
        private readonly CreateOrderUseCaseInterface $createOrder
    ) {
        parent::__construct('order:create');
    }

    protected function execute(InputInterface $input, OutputInterface $output): int
    {
        $command = new CreateOrderCommand(
            customerId: new CustomerId($input->getArgument('customer')),
            lines: $this->parseLines($input->getOption('lines'))
        );

        $orderId = $this->createOrder->execute($command);

        $output->writeln("Created order: {$orderId->value}");

        return Command::SUCCESS;
    }
}
```

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Messaging;

use Application\Order\Port\CreateOrderUseCaseInterface;
use Symfony\Component\Messenger\Attribute\AsMessageHandler;

// Message Consumer Driving Adapter
#[AsMessageHandler]
final readonly class CreateOrderFromEventHandler
{
    public function __construct(
        private CreateOrderUseCaseInterface $createOrder
    ) {}

    public function __invoke(ExternalOrderReceivedEvent $event): void
    {
        $command = new CreateOrderCommand(
            customerId: new CustomerId($event->customerId),
            lines: $event->lines
        );

        $this->createOrder->execute($command);
    }
}
```

### Driven Adapters (Secondary)

Implementations that the application calls to interact with external systems.

**Location:** Infrastructure layer

**Examples:** Repository implementations, API clients, Message publishers

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Payment;

use Application\Order\Port\PaymentGatewayInterface;
use Application\Order\DTO\PaymentRequest;
use Application\Order\DTO\PaymentResponse;
use Stripe\StripeClient;

// Payment Gateway Driven Adapter
final readonly class StripePaymentGateway implements PaymentGatewayInterface
{
    public function __construct(
        private StripeClient $stripe,
        private LoggerInterface $logger
    ) {}

    public function charge(PaymentRequest $request): PaymentResponse
    {
        try {
            $charge = $this->stripe->charges->create([
                'amount' => $request->amount->cents(),
                'currency' => $request->currency->value,
                'source' => $request->token,
                'metadata' => ['order_id' => $request->orderId->value],
            ]);

            return new PaymentResponse(
                transactionId: $charge->id,
                status: PaymentStatus::Success
            );
        } catch (CardException $e) {
            $this->logger->warning('Payment failed', [
                'order_id' => $request->orderId->value,
                'error' => $e->getMessage(),
            ]);

            return new PaymentResponse(
                transactionId: null,
                status: PaymentStatus::Failed,
                errorMessage: $e->getMessage()
            );
        }
    }
}
```

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Notification;

use Application\Order\Port\NotificationServiceInterface;
use Application\Order\DTO\EmailMessage;
use Symfony\Component\Mailer\MailerInterface;
use Symfony\Component\Mime\Email;

// Email Notification Driven Adapter
final readonly class SymfonyMailerNotificationService implements NotificationServiceInterface
{
    public function __construct(
        private MailerInterface $mailer
    ) {}

    public function sendEmail(EmailMessage $message): void
    {
        $email = (new Email())
            ->from($message->from)
            ->to($message->to)
            ->subject($message->subject)
            ->html($message->body);

        $this->mailer->send($email);
    }
}
```

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Persistence;

use Domain\Order\Entity\Order;
use Domain\Order\Repository\OrderRepositoryInterface;
use Domain\Order\ValueObject\OrderId;
use Doctrine\ORM\EntityManagerInterface;

// Repository Driven Adapter
final readonly class DoctrineOrderRepository implements OrderRepositoryInterface
{
    public function __construct(
        private EntityManagerInterface $em
    ) {}

    public function findById(OrderId $id): ?Order
    {
        return $this->em->find(Order::class, $id->value);
    }

    public function save(Order $order): void
    {
        $this->em->persist($order);
        $this->em->flush();
    }

    public function nextIdentity(): OrderId
    {
        return OrderId::generate();
    }
}
```

## Port Design Guidelines

### 1. Application-Centric Naming

Name ports from the application's perspective, not the adapter's.

```php
// GOOD - Application perspective
interface PaymentGatewayInterface
{
    public function charge(PaymentRequest $request): PaymentResponse;
}

// BAD - Adapter perspective
interface StripeServiceInterface  // Too specific to implementation
{
    public function createCharge(array $params): object;
}
```

### 2. Use Application/Domain Types

Ports should use types from inner layers, not infrastructure types.

```php
// GOOD - Uses Application DTOs
interface PaymentGatewayInterface
{
    public function charge(PaymentRequest $request): PaymentResponse;
}

// BAD - Uses infrastructure types
interface PaymentGatewayInterface
{
    public function charge(array $params): StripeCharge;  // Leaking Stripe
}
```

### 3. Single Responsibility

Each port should have a focused responsibility.

```php
// GOOD - Focused ports
interface PaymentGatewayInterface
{
    public function charge(PaymentRequest $request): PaymentResponse;
    public function refund(RefundRequest $request): RefundResponse;
}

interface NotificationServiceInterface
{
    public function notify(Notification $notification): void;
}

// BAD - God interface
interface ExternalServicesInterface
{
    public function charge(...);
    public function sendEmail(...);
    public function sendSms(...);
    public function createShipment(...);
}
```

### 4. Async-Ready Design

Design ports to support both sync and async implementations.

```php
// Port that can be implemented sync or async
interface NotificationServiceInterface
{
    public function notify(Notification $notification): void;
}

// Sync implementation
final readonly class SyncNotificationService implements NotificationServiceInterface
{
    public function notify(Notification $notification): void
    {
        $this->mailer->send($notification->toEmail());
    }
}

// Async implementation
final readonly class AsyncNotificationService implements NotificationServiceInterface
{
    public function __construct(
        private MessageBusInterface $bus
    ) {}

    public function notify(Notification $notification): void
    {
        $this->bus->dispatch(new SendNotificationMessage($notification));
    }
}
```

## Adapter Design Guidelines

### 1. Handle Infrastructure Errors

Adapters should translate infrastructure exceptions to domain/application exceptions.

```php
final readonly class StripePaymentGateway implements PaymentGatewayInterface
{
    public function charge(PaymentRequest $request): PaymentResponse
    {
        try {
            $charge = $this->stripe->charges->create([...]);
            return PaymentResponse::success($charge->id);
        } catch (CardException $e) {
            // Translate to application exception
            return PaymentResponse::declined($e->getMessage());
        } catch (RateLimitException $e) {
            throw new PaymentServiceUnavailableException('Rate limited', $e);
        } catch (ApiException $e) {
            throw new PaymentServiceUnavailableException('API error', $e);
        }
    }
}
```

### 2. Implement Circuit Breaker

For external services, implement resilience patterns.

```php
final readonly class ResilientPaymentGateway implements PaymentGatewayInterface
{
    public function __construct(
        private PaymentGatewayInterface $inner,
        private CircuitBreaker $circuitBreaker
    ) {}

    public function charge(PaymentRequest $request): PaymentResponse
    {
        return $this->circuitBreaker->execute(
            fn () => $this->inner->charge($request)
        );
    }
}
```

### 3. Adapter Composition

Use decorator pattern for cross-cutting concerns.

```php
// Base adapter
final readonly class StripePaymentGateway implements PaymentGatewayInterface { }

// Logging decorator
final readonly class LoggingPaymentGateway implements PaymentGatewayInterface
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
            'status' => $response->status->value,
        ]);

        return $response;
    }
}

// Metrics decorator
final readonly class MetricsPaymentGateway implements PaymentGatewayInterface
{
    public function charge(PaymentRequest $request): PaymentResponse
    {
        $start = microtime(true);

        $response = $this->inner->charge($request);

        $this->metrics->timing('payment.charge', microtime(true) - $start);
        $this->metrics->increment("payment.{$response->status->value}");

        return $response;
    }
}

// Wire them together
$gateway = new MetricsPaymentGateway(
    new LoggingPaymentGateway(
        new StripePaymentGateway($stripeClient),
        $logger
    ),
    $metrics
);
```

## Detection Patterns

```bash
# Find Ports
Glob: **/Application/**/Port/*Interface.php
Grep: "interface.*Interface" --glob "**/Application/**/*.php"

# Find Driven Adapters
Grep: "implements.*Interface" --glob "**/Infrastructure/**/*.php"

# Find Driving Adapters
Grep: "UseCase|UseCaseInterface" --glob "**/Presentation/**/*.php"
Grep: "UseCase|UseCaseInterface" --glob "**/Console/**/*.php"

# Verify adapters implement ports
Grep: "class.*implements.*(Gateway|Service|Repository)Interface" --glob "**/Infrastructure/**/*.php"

# Check for missing ports (direct external calls)
Grep: "new (Stripe|Twilio|Aws)" --glob "**/Application/**/*.php"  # Should be 0
```
