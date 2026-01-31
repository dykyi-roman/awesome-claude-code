# Saga Patterns

Patterns for managing distributed transactions in Event-Driven Architecture.

## Saga Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           SAGA PATTERN                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   Saga = sequence of local transactions                                  │
│   Each step publishes events that trigger next step                      │
│   If a step fails, compensating transactions undo previous steps         │
│                                                                          │
│   ┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐                  │
│   │  T1    │───▶│  T2    │───▶│  T3    │───▶│  T4    │   Success        │
│   └────────┘    └────────┘    └────────┘    └────────┘                  │
│       │             │             │                                      │
│       ▼             ▼             ▼                                      │
│   ┌────────┐    ┌────────┐    ┌────────┐                                │
│   │  C1    │◀───│  C2    │◀───│  C3    │         Compensation           │
│   └────────┘    └────────┘    └────────┘                                │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Choreography vs Orchestration

### Choreography

Each service knows what to do next; decentralized control.

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Order     │────▶│  Payment    │────▶│  Shipping   │
│   Service   │     │   Service   │     │   Service   │
└─────────────┘     └─────────────┘     └─────────────┘
      │                   │                   │
      ▼                   ▼                   ▼
   OrderPlaced      PaymentCompleted     ShipmentCreated
```

### Orchestration

Central coordinator manages the workflow.

```
                    ┌─────────────────┐
                    │  Saga           │
                    │  Orchestrator   │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
   │   Order     │     │  Payment    │     │  Shipping   │
   │   Service   │     │   Service   │     │   Service   │
   └─────────────┘     └─────────────┘     └─────────────┘
```

## Choreography Implementation

### Step 1: Order Service

```php
<?php

declare(strict_types=1);

namespace Application\Order\UseCase;

final readonly class PlaceOrderUseCase
{
    public function __construct(
        private OrderRepositoryInterface $orders,
        private EventPublisherInterface $events
    ) {}

    public function execute(PlaceOrderCommand $command): OrderDTO
    {
        $order = Order::place(
            id: $this->orders->nextIdentity(),
            customerId: new CustomerId($command->customerId),
            lines: $command->lines
        );

        $this->orders->save($order);

        // Publish event - triggers payment service
        $this->events->publish(new OrderPlaced(
            eventId: Uuid::uuid4()->toString(),
            orderId: $order->id()->value,
            customerId: $command->customerId,
            totalCents: $order->total()->cents(),
            occurredAt: new \DateTimeImmutable()
        ));

        return OrderDTO::fromEntity($order);
    }
}
```

### Step 2: Payment Service Handler

```php
<?php

declare(strict_types=1);

namespace Application\Payment\EventHandler;

final readonly class ProcessPaymentOnOrderPlaced
{
    public function __construct(
        private PaymentServiceInterface $payments,
        private EventPublisherInterface $events
    ) {}

    public function __invoke(OrderPlaced $event): void
    {
        try {
            $payment = $this->payments->charge(
                orderId: $event->orderId,
                amount: $event->totalCents,
                customerId: $event->customerId
            );

            $this->events->publish(new PaymentCompleted(
                eventId: Uuid::uuid4()->toString(),
                orderId: $event->orderId,
                paymentId: $payment->id(),
                occurredAt: new \DateTimeImmutable()
            ));

        } catch (PaymentFailedException $e) {
            $this->events->publish(new PaymentFailed(
                eventId: Uuid::uuid4()->toString(),
                orderId: $event->orderId,
                reason: $e->getMessage(),
                occurredAt: new \DateTimeImmutable()
            ));
        }
    }
}
```

### Step 3: Shipping Service Handler

```php
<?php

declare(strict_types=1);

namespace Application\Shipping\EventHandler;

final readonly class CreateShipmentOnPaymentCompleted
{
    public function __construct(
        private ShippingServiceInterface $shipping,
        private EventPublisherInterface $events
    ) {}

    public function __invoke(PaymentCompleted $event): void
    {
        try {
            $shipment = $this->shipping->createShipment($event->orderId);

            $this->events->publish(new ShipmentCreated(
                eventId: Uuid::uuid4()->toString(),
                orderId: $event->orderId,
                shipmentId: $shipment->id(),
                trackingNumber: $shipment->trackingNumber(),
                occurredAt: new \DateTimeImmutable()
            ));

        } catch (ShippingException $e) {
            $this->events->publish(new ShipmentFailed(
                eventId: Uuid::uuid4()->toString(),
                orderId: $event->orderId,
                reason: $e->getMessage(),
                occurredAt: new \DateTimeImmutable()
            ));
        }
    }
}
```

### Compensation Handler

```php
<?php

declare(strict_types=1);

namespace Application\Order\EventHandler;

final readonly class CancelOrderOnPaymentFailed
{
    public function __construct(
        private OrderRepositoryInterface $orders,
        private EventPublisherInterface $events
    ) {}

    public function __invoke(PaymentFailed $event): void
    {
        $order = $this->orders->findById(new OrderId($event->orderId));

        $order->cancel(reason: "Payment failed: {$event->reason}");

        $this->orders->save($order);

        $this->events->publish(new OrderCancelled(
            eventId: Uuid::uuid4()->toString(),
            orderId: $event->orderId,
            reason: $event->reason,
            occurredAt: new \DateTimeImmutable()
        ));
    }
}
```

## Orchestration Implementation

### Saga State

```php
<?php

declare(strict_types=1);

namespace Domain\Saga;

enum SagaStatus: string
{
    case Started = 'started';
    case Processing = 'processing';
    case Completed = 'completed';
    case Compensating = 'compensating';
    case Failed = 'failed';
}

final class SagaState
{
    private array $completedSteps = [];
    private ?string $failedStep = null;
    private ?string $failureReason = null;

    public function __construct(
        private readonly string $sagaId,
        private readonly string $sagaType,
        private SagaStatus $status,
        private array $data,
        private readonly \DateTimeImmutable $startedAt,
        private ?\DateTimeImmutable $completedAt = null
    ) {}

    public function markStepCompleted(string $step, array $result): void
    {
        $this->completedSteps[$step] = [
            'result' => $result,
            'completedAt' => new \DateTimeImmutable(),
        ];
    }

    public function markStepFailed(string $step, string $reason): void
    {
        $this->status = SagaStatus::Compensating;
        $this->failedStep = $step;
        $this->failureReason = $reason;
    }

    public function completedSteps(): array
    {
        return array_keys($this->completedSteps);
    }

    public function getStepResult(string $step): ?array
    {
        return $this->completedSteps[$step]['result'] ?? null;
    }
}
```

### Saga Definition

```php
<?php

declare(strict_types=1);

namespace Application\Order\Saga;

final readonly class OrderSagaDefinition implements SagaDefinitionInterface
{
    public function steps(): array
    {
        return [
            'create_order' => [
                'action' => CreateOrderStep::class,
                'compensation' => CancelOrderStep::class,
            ],
            'reserve_inventory' => [
                'action' => ReserveInventoryStep::class,
                'compensation' => ReleaseInventoryStep::class,
            ],
            'process_payment' => [
                'action' => ProcessPaymentStep::class,
                'compensation' => RefundPaymentStep::class,
            ],
            'create_shipment' => [
                'action' => CreateShipmentStep::class,
                'compensation' => CancelShipmentStep::class,
            ],
        ];
    }

    public function sagaType(): string
    {
        return 'order_saga';
    }
}
```

### Saga Step Interface

```php
<?php

declare(strict_types=1);

namespace Application\Saga;

interface SagaStepInterface
{
    public function execute(SagaState $state): StepResult;
}

interface CompensationStepInterface
{
    public function compensate(SagaState $state): void;
}

final readonly class StepResult
{
    private function __construct(
        public bool $success,
        public array $data,
        public ?string $error = null
    ) {}

    public static function success(array $data = []): self
    {
        return new self(true, $data);
    }

    public static function failure(string $error): self
    {
        return new self(false, [], $error);
    }
}
```

### Saga Steps

```php
<?php

declare(strict_types=1);

namespace Application\Order\Saga\Step;

final readonly class ProcessPaymentStep implements SagaStepInterface
{
    public function __construct(
        private PaymentServiceInterface $payments
    ) {}

    public function execute(SagaState $state): StepResult
    {
        try {
            $payment = $this->payments->charge(
                orderId: $state->data['order_id'],
                amount: $state->data['total_cents'],
                customerId: $state->data['customer_id']
            );

            return StepResult::success([
                'payment_id' => $payment->id(),
                'transaction_id' => $payment->transactionId(),
            ]);

        } catch (PaymentException $e) {
            return StepResult::failure($e->getMessage());
        }
    }
}

final readonly class RefundPaymentStep implements CompensationStepInterface
{
    public function __construct(
        private PaymentServiceInterface $payments
    ) {}

    public function compensate(SagaState $state): void
    {
        $paymentResult = $state->getStepResult('process_payment');

        if ($paymentResult === null) {
            return; // Payment was never processed
        }

        $this->payments->refund($paymentResult['payment_id']);
    }
}
```

### Saga Orchestrator

```php
<?php

declare(strict_types=1);

namespace Application\Saga;

use Psr\Container\ContainerInterface;

final readonly class SagaOrchestrator
{
    public function __construct(
        private ContainerInterface $container,
        private SagaStateRepositoryInterface $stateRepository,
        private LoggerInterface $logger
    ) {}

    public function execute(SagaDefinitionInterface $definition, array $data): SagaState
    {
        $state = new SagaState(
            sagaId: Uuid::uuid4()->toString(),
            sagaType: $definition->sagaType(),
            status: SagaStatus::Started,
            data: $data,
            startedAt: new \DateTimeImmutable()
        );

        $this->stateRepository->save($state);

        try {
            foreach ($definition->steps() as $stepName => $stepConfig) {
                $this->executeStep($state, $stepName, $stepConfig);
            }

            $state->complete();

        } catch (SagaStepFailedException $e) {
            $this->compensate($state, $definition);
            $state->fail($e->getMessage());
        }

        $this->stateRepository->save($state);

        return $state;
    }

    private function executeStep(SagaState $state, string $stepName, array $config): void
    {
        $this->logger->info("Executing saga step: {$stepName}", [
            'saga_id' => $state->sagaId(),
        ]);

        /** @var SagaStepInterface $step */
        $step = $this->container->get($config['action']);
        $result = $step->execute($state);

        if (!$result->success) {
            $state->markStepFailed($stepName, $result->error);
            throw new SagaStepFailedException($stepName, $result->error);
        }

        $state->markStepCompleted($stepName, $result->data);
        $this->stateRepository->save($state);
    }

    private function compensate(SagaState $state, SagaDefinitionInterface $definition): void
    {
        $completedSteps = array_reverse($state->completedSteps());

        foreach ($completedSteps as $stepName) {
            $config = $definition->steps()[$stepName];

            if (!isset($config['compensation'])) {
                continue;
            }

            $this->logger->info("Compensating saga step: {$stepName}", [
                'saga_id' => $state->sagaId(),
            ]);

            /** @var CompensationStepInterface $compensation */
            $compensation = $this->container->get($config['compensation']);

            try {
                $compensation->compensate($state);
            } catch (\Throwable $e) {
                $this->logger->error("Compensation failed for step: {$stepName}", [
                    'saga_id' => $state->sagaId(),
                    'error' => $e->getMessage(),
                ]);
            }
        }
    }
}
```

### Async Saga Orchestrator

```php
<?php

declare(strict_types=1);

namespace Application\Saga;

final readonly class AsyncSagaOrchestrator
{
    public function __construct(
        private SagaStateRepositoryInterface $stateRepository,
        private EventPublisherInterface $events
    ) {}

    public function start(SagaDefinitionInterface $definition, array $data): string
    {
        $state = new SagaState(
            sagaId: Uuid::uuid4()->toString(),
            sagaType: $definition->sagaType(),
            status: SagaStatus::Started,
            data: $data,
            startedAt: new \DateTimeImmutable()
        );

        $this->stateRepository->save($state);

        // Trigger first step
        $firstStep = array_key_first($definition->steps());
        $this->events->publish(new SagaStepRequested(
            sagaId: $state->sagaId(),
            stepName: $firstStep,
            data: $data
        ));

        return $state->sagaId();
    }

    public function handleStepCompleted(SagaStepCompleted $event): void
    {
        $state = $this->stateRepository->findById($event->sagaId);
        $definition = $this->getDefinition($state->sagaType());

        $state->markStepCompleted($event->stepName, $event->result);

        $nextStep = $this->getNextStep($definition, $event->stepName);

        if ($nextStep === null) {
            $state->complete();
            $this->stateRepository->save($state);
            return;
        }

        $this->events->publish(new SagaStepRequested(
            sagaId: $state->sagaId(),
            stepName: $nextStep,
            data: array_merge($state->data(), $event->result)
        ));

        $this->stateRepository->save($state);
    }

    public function handleStepFailed(SagaStepFailed $event): void
    {
        $state = $this->stateRepository->findById($event->sagaId);

        $state->markStepFailed($event->stepName, $event->reason);

        // Trigger compensation
        $this->events->publish(new SagaCompensationRequested(
            sagaId: $state->sagaId(),
            completedSteps: $state->completedSteps()
        ));

        $this->stateRepository->save($state);
    }
}
```

## Process Manager

Alternative term for Saga Orchestrator with more complex routing logic.

```php
<?php

declare(strict_types=1);

namespace Application\Order\ProcessManager;

final class OrderFulfillmentProcessManager
{
    private array $handlers = [];

    public function __construct(
        private readonly ProcessStateRepositoryInterface $stateRepository,
        private readonly EventPublisherInterface $events
    ) {
        $this->handlers = [
            OrderPlaced::class => 'onOrderPlaced',
            PaymentCompleted::class => 'onPaymentCompleted',
            PaymentFailed::class => 'onPaymentFailed',
            InventoryReserved::class => 'onInventoryReserved',
            InventoryReservationFailed::class => 'onInventoryReservationFailed',
            ShipmentCreated::class => 'onShipmentCreated',
        ];
    }

    public function handle(DomainEvent $event): void
    {
        $handler = $this->handlers[$event::class] ?? null;

        if ($handler === null) {
            return;
        }

        $this->$handler($event);
    }

    private function onOrderPlaced(OrderPlaced $event): void
    {
        $state = new ProcessState(
            processId: $event->orderId,
            status: 'awaiting_payment',
            data: ['order_id' => $event->orderId, 'customer_id' => $event->customerId]
        );

        $this->stateRepository->save($state);

        $this->events->publish(new RequestPayment(
            orderId: $event->orderId,
            amount: $event->totalCents
        ));
    }

    private function onPaymentCompleted(PaymentCompleted $event): void
    {
        $state = $this->stateRepository->findById($event->orderId);
        $state->updateStatus('awaiting_inventory');
        $state->addData('payment_id', $event->paymentId);

        $this->stateRepository->save($state);

        $this->events->publish(new ReserveInventory(
            orderId: $event->orderId
        ));
    }

    private function onPaymentFailed(PaymentFailed $event): void
    {
        $state = $this->stateRepository->findById($event->orderId);
        $state->updateStatus('failed');
        $state->addData('failure_reason', $event->reason);

        $this->stateRepository->save($state);

        $this->events->publish(new CancelOrder(
            orderId: $event->orderId,
            reason: $event->reason
        ));
    }

    // ... more handlers
}
```

## Best Practices

### 1. Make Steps Idempotent

```php
final readonly class ProcessPaymentStep implements SagaStepInterface
{
    public function execute(SagaState $state): StepResult
    {
        // Check if already processed
        $existingPayment = $this->payments->findByOrderId($state->data['order_id']);

        if ($existingPayment !== null) {
            return StepResult::success([
                'payment_id' => $existingPayment->id(),
            ]);
        }

        // Process new payment
        $payment = $this->payments->charge(...);

        return StepResult::success(['payment_id' => $payment->id()]);
    }
}
```

### 2. Store Saga State Durably

```php
// Use database transaction
$this->transaction->transactional(function () use ($state, $step) {
    $result = $step->execute($state);
    $state->markStepCompleted($stepName, $result->data);
    $this->stateRepository->save($state);
});
```

### 3. Handle Partial Failures

```php
final readonly class CompensationStep implements CompensationStepInterface
{
    public function compensate(SagaState $state): void
    {
        try {
            $this->doCompensation($state);
        } catch (\Throwable $e) {
            // Log but don't throw - compensation must be best effort
            $this->logger->error('Compensation failed', [
                'saga_id' => $state->sagaId(),
                'error' => $e->getMessage(),
            ]);

            // Optionally: schedule for manual intervention
            $this->alertService->notifyManualInterventionNeeded($state);
        }
    }
}
```

## Directory Structure

```
src/Application/
├── Saga/
│   ├── SagaOrchestrator.php
│   ├── AsyncSagaOrchestrator.php
│   ├── SagaState.php
│   ├── SagaStepInterface.php
│   ├── CompensationStepInterface.php
│   └── SagaDefinitionInterface.php
└── Order/
    ├── Saga/
    │   ├── OrderSagaDefinition.php
    │   └── Step/
    │       ├── CreateOrderStep.php
    │       ├── CancelOrderStep.php
    │       ├── ProcessPaymentStep.php
    │       ├── RefundPaymentStep.php
    │       ├── ReserveInventoryStep.php
    │       └── ReleaseInventoryStep.php
    └── ProcessManager/
        └── OrderFulfillmentProcessManager.php
```
