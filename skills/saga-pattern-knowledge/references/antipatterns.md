# Saga Pattern Antipatterns

## Critical Violations

### 1. Missing Compensating Actions

**Problem:** Saga steps without compensation logic.

```php
// ❌ WRONG: No compensation
final readonly class ChargePaymentStep implements SagaStepInterface
{
    public function execute(SagaContext $context): StepResult
    {
        $this->payments->charge($context->get('order_id'));
        return StepResult::success();
    }

    public function compensate(SagaContext $context): StepResult
    {
        // Nothing here! Payment cannot be undone!
        return StepResult::success();
    }
}
```

**Consequence:** System left in inconsistent state on failure.

```php
// ✅ CORRECT: Proper compensation
final readonly class ChargePaymentStep implements SagaStepInterface
{
    public function execute(SagaContext $context): StepResult
    {
        $result = $this->payments->charge($context->get('order_id'));
        $context->set('payment_id', $result->paymentId);
        return StepResult::success();
    }

    public function compensate(SagaContext $context): StepResult
    {
        $this->payments->refund($context->get('payment_id'));
        return StepResult::success();
    }
}
```

### 2. Non-Idempotent Steps

**Problem:** Steps that cause duplicate effects on retry.

```php
// ❌ WRONG: Creates duplicate charges on retry
final readonly class ChargePaymentStep implements SagaStepInterface
{
    public function execute(SagaContext $context): StepResult
    {
        // No idempotency check - retries create duplicate charges
        $this->payments->charge(
            customerId: $context->get('customer_id'),
            amount: $context->get('amount')
        );
        return StepResult::success();
    }
}
```

**Consequence:** Customer charged multiple times on retry.

```php
// ✅ CORRECT: Idempotent with idempotency key
final readonly class ChargePaymentStep implements SagaStepInterface
{
    public function execute(SagaContext $context): StepResult
    {
        $idempotencyKey = "{$context->sagaId}_charge";

        // Check if already executed
        $existing = $this->payments->findByIdempotencyKey($idempotencyKey);
        if ($existing) {
            $context->set('payment_id', $existing->id);
            return StepResult::success();
        }

        $result = $this->payments->charge(
            customerId: $context->get('customer_id'),
            amount: $context->get('amount'),
            idempotencyKey: $idempotencyKey
        );

        $context->set('payment_id', $result->paymentId);
        return StepResult::success();
    }
}
```

### 3. No Saga State Persistence

**Problem:** Saga state kept only in memory.

```php
// ❌ WRONG: State lost on crash
final class SagaOrchestrator
{
    private array $completedSteps = []; // Lost on restart!

    public function execute(): void
    {
        foreach ($this->steps as $step) {
            $step->execute($this->context);
            $this->completedSteps[] = $step->name(); // Not persisted
        }
    }
}
```

**Consequence:** No way to resume or compensate after crash.

```php
// ✅ CORRECT: Persistent state
final class SagaOrchestrator
{
    public function execute(): void
    {
        foreach ($this->steps as $step) {
            $step->execute($this->context);

            $this->persistence->save(
                $this->context->sagaId,
                $this->state,
                $this->completedSteps
            );
        }
    }
}
```

### 4. Distributed Transaction Attempt

**Problem:** Trying to use two-phase commit across services.

```php
// ❌ WRONG: Distributed transaction
public function execute(PlaceOrderCommand $command): void
{
    $this->orderDb->beginTransaction();
    $this->inventoryDb->beginTransaction(); // Different database!

    try {
        $this->orderDb->save($order);
        $this->inventoryDb->reserve($items);

        $this->orderDb->commit();
        $this->inventoryDb->commit(); // Can fail after first commit!
    } catch (\Throwable $e) {
        $this->orderDb->rollback();
        $this->inventoryDb->rollback();
    }
}
```

**Consequence:** Partial commits on failure.

```php
// ✅ CORRECT: Use saga pattern
public function execute(PlaceOrderCommand $command): void
{
    $saga = $this->sagaFactory->createOrderSaga($command);
    $result = $saga->execute();

    if ($result->isFailed()) {
        // Saga handles compensation
        throw new OrderCreationFailed($result->error());
    }
}
```

### 5. Forward-Only Saga

**Problem:** Saga has no compensation path at all.

```php
// ❌ WRONG: No compensation whatsoever
final class OrderProcessingSaga
{
    public function run(): void
    {
        $this->reserveInventory();
        $this->chargePayment();
        $this->createShipment();
        // If any step fails, previous steps are not undone!
    }
}
```

## Warning-Level Issues

### 6. Wrong Compensation Order

**Problem:** Compensations not executed in reverse order.

```php
// ❌ WRONG: Compensating in forward order
private function compensate(): void
{
    foreach ($this->completedSteps as $stepName) { // Wrong order!
        $this->findStep($stepName)->compensate($this->context);
    }
}
```

```php
// ✅ CORRECT: Reverse order
private function compensate(): void
{
    $reversed = array_reverse($this->completedSteps);
    foreach ($reversed as $stepName) {
        $this->findStep($stepName)->compensate($this->context);
    }
}
```

### 7. Missing Correlation ID

**Problem:** Cannot trace saga across services.

```php
// ❌ WRONG: No correlation
public function execute(SagaContext $context): StepResult
{
    $this->inventoryService->reserve(
        orderId: $context->get('order_id'),
        items: $context->get('items')
        // No way to trace this call to the saga
    );
}
```

```php
// ✅ CORRECT: Propagate correlation ID
public function execute(SagaContext $context): StepResult
{
    $this->inventoryService->reserve(
        orderId: $context->get('order_id'),
        items: $context->get('items'),
        correlationId: $context->correlationId,
        causationId: $context->sagaId
    );
}
```

### 8. No Timeout Handling

**Problem:** Saga waits forever for step completion.

```php
// ❌ WRONG: No timeout
public function execute(SagaContext $context): StepResult
{
    $result = $this->externalService->call(...); // Can hang forever
    return StepResult::success();
}
```

```php
// ✅ CORRECT: Timeout handling
public function execute(SagaContext $context): StepResult
{
    try {
        $result = $this->externalService->callWithTimeout(
            timeout: 30,
            ...
        );
        return StepResult::success();
    } catch (TimeoutException $e) {
        // Decide: retry, fail, or compensate
        return StepResult::failure('Step timed out');
    }
}
```

### 9. Compensation Data Not Stored

**Problem:** Missing data needed for compensation.

```php
// ❌ WRONG: No data for compensation
public function execute(SagaContext $context): StepResult
{
    $result = $this->payments->charge(...);
    // Didn't store payment_id!
    return StepResult::success();
}

public function compensate(SagaContext $context): StepResult
{
    $paymentId = $context->get('payment_id'); // null!
    $this->payments->refund($paymentId); // Fails
}
```

### 10. Silent Compensation Failures

**Problem:** Compensation errors are swallowed.

```php
// ❌ WRONG: Silent failure
public function compensate(SagaContext $context): StepResult
{
    try {
        $this->inventory->release(...);
    } catch (\Throwable $e) {
        // Silently ignore! System inconsistent
    }
    return StepResult::success();
}
```

```php
// ✅ CORRECT: Proper error handling
public function compensate(SagaContext $context): StepResult
{
    try {
        $this->inventory->release(...);
        return StepResult::success();
    } catch (\Throwable $e) {
        $this->logger->error('Compensation failed', [
            'saga_id' => $context->sagaId,
            'step' => $this->name(),
            'error' => $e->getMessage(),
        ]);
        return StepResult::failure($e->getMessage());
    }
}
```

## Detection Queries

```bash
# Find saga implementations without compensation
Grep: "implements.*SagaStep" --glob "**/*.php"
# Then check each file for compensate() method

# Find potential distributed transactions
Grep: "beginTransaction.*beginTransaction|->begin\(.*->begin\(" --glob "**/*.php"

# Check for idempotency keys
Grep: "idempotency|IdempotencyKey" --glob "**/Saga/**/*.php"

# Find missing correlation IDs
Grep: "SagaContext" --glob "**/*.php"
# Check if correlationId is passed to external calls

# Find timeout configurations
Grep: "timeout|Timeout" --glob "**/Saga/**/*.php"

# Check for saga persistence
Grep: "SagaPersistence|sagaRepository|saga.*save" --glob "**/*.php"

# Find silent catch blocks
Grep: "catch.*\{.*\}" --glob "**/Saga/**/*.php"
```

## Checklist for Code Review

- [ ] Every saga step has a compensate() method
- [ ] Steps are idempotent (use idempotency keys)
- [ ] Saga state is persisted after each step
- [ ] Compensations run in reverse order
- [ ] Correlation ID propagated to all calls
- [ ] Timeouts configured for external calls
- [ ] All data needed for compensation is stored
- [ ] Compensation failures are properly handled
- [ ] No distributed transaction attempts
- [ ] Proper logging and monitoring
