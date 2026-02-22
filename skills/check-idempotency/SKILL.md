---
name: check-idempotency
description: Analyzes PHP code for idempotency issues. Detects missing idempotency keys on POST/PUT endpoints, non-idempotent command handlers, duplicate write risks, and retry-unsafe operations.
---

# Idempotency Check

Analyze PHP code for idempotency violations that can cause duplicate writes, double charges, or inconsistent state on retries.

## Detection Patterns

### 1. Missing Idempotency Key on POST/PUT Endpoints

```php
<?php

declare(strict_types=1);

// BAD: POST endpoint creates resource without deduplication
final class CreateOrderAction
{
    public function __invoke(Request $request): Response
    {
        $order = $this->orderService->create($request->validated());

        return new JsonResponse($order, 201);
        // Retry from client = duplicate order!
    }
}

// GOOD: POST endpoint requires idempotency key
final class CreateOrderAction
{
    public function __invoke(Request $request): Response
    {
        $idempotencyKey = $request->headers->get('Idempotency-Key');
        if ($idempotencyKey === null) {
            return new JsonResponse(['error' => 'Idempotency-Key header required'], 422);
        }

        $existing = $this->idempotencyStore->find($idempotencyKey);
        if ($existing !== null) {
            return new JsonResponse($existing->payload(), $existing->statusCode());
        }

        $order = $this->orderService->create($request->validated());

        $this->idempotencyStore->save($idempotencyKey, $order, 201);

        return new JsonResponse($order, 201);
    }
}
```

### 2. Non-Idempotent Command Handlers

```php
<?php

declare(strict_types=1);

// BAD: Handler executes without checking previous execution
final readonly class ChargePaymentHandler
{
    public function __construct(
        private PaymentGateway $gateway,
    ) {}

    public function __invoke(ChargePaymentCommand $command): void
    {
        // If message is redelivered, payment is charged twice!
        $this->gateway->charge($command->amount, $command->cardToken);
    }
}

// GOOD: Handler checks for previous execution
final readonly class ChargePaymentHandler
{
    public function __construct(
        private PaymentGateway $gateway,
        private ProcessedCommandStore $processedStore,
    ) {}

    public function __invoke(ChargePaymentCommand $command): void
    {
        if ($this->processedStore->wasProcessed($command->commandId)) {
            return; // Already executed, skip
        }

        $this->gateway->charge($command->amount, $command->cardToken);
        $this->processedStore->markProcessed($command->commandId);
    }
}
```

### 3. Duplicate Write Risk in Critical Operations

```php
<?php

declare(strict_types=1);

// BAD: Payment without dedup guard
final readonly class PaymentService
{
    public function charge(UserId $userId, Money $amount): PaymentResult
    {
        // No guard against duplicate charges
        $result = $this->gateway->charge($userId->toString(), $amount->cents());
        $this->repository->save(new Payment($userId, $amount, $result->transactionId()));

        return $result;
    }
}

// GOOD: Payment with unique constraint and idempotency
final readonly class PaymentService
{
    public function charge(UserId $userId, Money $amount, string $requestId): PaymentResult
    {
        $existing = $this->repository->findByRequestId($requestId);
        if ($existing !== null) {
            return PaymentResult::fromExisting($existing);
        }

        $result = $this->gateway->charge(
            $userId->toString(),
            $amount->cents(),
            idempotencyKey: $requestId,
        );

        $this->repository->save(
            new Payment($userId, $amount, $result->transactionId(), $requestId),
        );

        return $result;
    }
}
```

### 4. Retry-Unsafe Operations in Retry Loops

```php
<?php

declare(strict_types=1);

// BAD: Email send in retry loop without idempotency guard
final readonly class NotificationService
{
    public function sendWithRetry(Notification $notification): void
    {
        $attempts = 0;
        while ($attempts < 3) {
            try {
                $this->mailer->send($notification->toEmail());
                $this->smsService->send($notification->toSms());
                return;
            } catch (TransportException $e) {
                $attempts++;
                // Email might have been sent, SMS failed
                // Retry sends email AGAIN!
            }
        }
    }
}

// GOOD: Track each step independently with idempotency
final readonly class NotificationService
{
    public function sendWithRetry(Notification $notification): void
    {
        $this->sendStep(
            stepId: $notification->id() . ':email',
            action: fn () => $this->mailer->send($notification->toEmail()),
        );

        $this->sendStep(
            stepId: $notification->id() . ':sms',
            action: fn () => $this->smsService->send($notification->toSms()),
        );
    }

    private function sendStep(string $stepId, callable $action): void
    {
        if ($this->stepStore->isCompleted($stepId)) {
            return;
        }

        $action();
        $this->stepStore->markCompleted($stepId);
    }
}
```

## Grep Patterns

```bash
# POST/PUT actions without idempotency key check
Grep: "class.*Action|class.*Controller" --glob "**/*Action*.php"
Grep: "Idempotency-Key|idempotency_key|idempotencyKey" --glob "**/*.php"

# Command handlers without dedup check
Grep: "class.*Handler.*\{" --glob "**/*Handler*.php"
Grep: "wasProcessed|isProcessed|alreadyHandled" --glob "**/*Handler*.php"

# Payment/charge operations without idempotency
Grep: "->charge\(|->pay\(|->refund\(|->transfer\(" --glob "**/*.php"
Grep: "findByRequestId|findByIdempotencyKey" --glob "**/*.php"

# Retry loops with side effects
Grep: "while.*retry|for.*attempt|catch.*retry" --glob "**/*.php"

# Email/SMS in retry blocks
Grep: "->send\(.*Email|->send\(.*Sms|mailer->send" --glob "**/*.php"

# Missing unique constraints on write operations
Grep: "->save\(|->persist\(|->insert\(" --glob "**/*Handler*.php"
```

## Severity Classification

| Pattern | Severity |
|---------|----------|
| Payment/charge without idempotency key | 🔴 Critical |
| Command handler without dedup check | 🔴 Critical |
| POST endpoint without Idempotency-Key | 🟠 Major |
| Email send in retry loop without guard | 🟠 Major |
| Write operation without unique constraint | 🟠 Major |
| Missing idempotency on non-critical updates | 🟡 Minor |

## Output Format

```markdown
### Idempotency Issue: [Brief Description]

**Severity:** 🔴/🟠/🟡
**Location:** `file.php:line`
**Type:** [Missing Key|Non-Idempotent Handler|Duplicate Write|Retry-Unsafe]

**Issue:**
[Description of the idempotency violation]

**Risk:**
- Duplicate charges/payments on retry
- Double email/SMS delivery
- Inconsistent state after network failure

**Code:**
```php
// Problematic pattern
```

**Fix:**
```php
// With idempotency guard
```
```

## When This Is Acceptable

- **GET/DELETE requests** -- GET is inherently idempotent, DELETE on same resource is safe (returns 404 on retry)
- **Internal synchronous calls** -- Direct method calls within a single transaction boundary don't need idempotency keys
- **Upsert operations** -- INSERT ON CONFLICT UPDATE is inherently idempotent by design
- **Read-only commands** -- Query handlers that only read data don't need dedup checks

### False Positive Indicators
- Operation is wrapped in a database transaction with unique constraint
- Gateway already enforces idempotency (e.g., Stripe idempotency key at SDK level)
- Operation is naturally idempotent (setting a value, not incrementing)
