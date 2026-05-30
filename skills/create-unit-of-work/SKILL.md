---
name: create-unit-of-work
description: Generates Unit of Work pattern components for PHP 8.4. Creates transactional consistency infrastructure with aggregate tracking, flush/rollback, domain event collection, and unit tests.
---

# Unit of Work Generator

Creates Unit of Work pattern infrastructure for transactional consistency across multiple aggregates.

> Unit of Work is a persistence-coordination pattern (Fowler, *Patterns of Enterprise Application Architecture*). It maintains a list of objects affected by a business transaction and coordinates writing out their changes plus concurrency resolution. The pattern isn't bound to any specific layer — its interface and implementation live wherever your project coordinates persistence.

## When to Use

| Scenario | Example |
|----------|---------|
| Multi-aggregate transactions | Order + Payment + Inventory in single transaction |
| Batch persistence | Flush multiple entity changes at once |
| Change tracking | Detect dirty entities for selective updates |
| Domain event collection | Collect and dispatch events after successful commit |
| Repository coordination | Ensure all repositories share the same transaction |

## Component Characteristics

### UnitOfWorkInterface
- Coordinates persistence across multiple aggregates
- begin(), commit(), rollback() transaction methods
- registerNew(), registerDirty(), registerDeleted() tracking methods
- flush() to persist all tracked changes
- collectEvents() from tracked aggregates

### UnitOfWork
- Infrastructure implementation (PDO/Doctrine-based)
- Identity Map for tracked entities
- Dirty checking for change detection
- Ordered persistence (inserts → updates → deletes)
- Wraps all operations in database transaction

### AggregateTracker
- Tracks entity state (NEW, CLEAN, DIRTY, DELETED)
- Identity Map prevents duplicate loading
- Computes changeset on flush

### TransactionManagerInterface
- Abstracts transaction lifecycle
- Supports nested transactions (savepoints)
- Implementation-agnostic abstraction over the underlying transactional resource

### DomainEventCollector
- Collects events from all tracked aggregates
- Dispatches events AFTER successful commit
- Clears events on rollback

---

## Generation Process

### Step 1: Analyze Request

Determine:
- Context name (Order, Payment, Inventory)
- Which aggregates participate in unit of work
- Event dispatcher integration (Symfony/custom)

### Step 2: Generate Core Components

Create in this order:

1. **Types & Contracts**
   - `EntityState.php` — State enum (New, Clean, Dirty, Deleted)
   - `TransactionManagerInterface.php` — Transaction contract
   - `DomainEventCollectorInterface.php` — Event collection contract
   - `UnitOfWorkInterface.php` — Main UoW contract

2. **Coordination**
   - `AggregateTracker.php` — Identity map and change tracking

3. **Persistence Implementation**
   - `DoctrineUnitOfWork.php` — Doctrine-based implementation
   - `DoctrineTransactionManager.php` — Doctrine transaction manager
   - `DomainEventCollector.php` — Event collector with dispatcher

4. **Tests**
   - `EntityStateTest.php`
   - `AggregateTrackerTest.php`
   - `DoctrineUnitOfWorkTest.php`

### Step 3: Generate Context-Specific Integration

For each context (e.g., Order), generate a trait or base class:

```
{Context}UnitOfWorkAware.php
```

---

## File Placement

| Component group | Path |
|-----------------|------|
| Types & Contracts | `src/{architecture-path}/UnitOfWork/` |
| Coordination | `src/{architecture-path}/UnitOfWork/` |
| Persistence Implementation | `src/{architecture-path}/UnitOfWork/` |
| Unit Tests | `tests/Unit/{architecture-path}/UnitOfWork/` |

> `{architecture-path}` represents your project's architecture-specific folders. Unit of Work coordinates persistence — its contract typically lives alongside Repository contracts; the Doctrine implementation lives with other persistence adapters. Adjust to your project's layout.

---

## Key Principles

### Transaction Boundaries
1. Begin transaction at use case entry
2. Track all aggregate changes within boundary
3. Flush all changes atomically
4. Dispatch domain events after successful commit
5. Rollback clears all tracked changes

### Identity Map
1. One entity instance per identity in memory
2. Prevent duplicate loads from database
3. Track original state for dirty checking

### Event Ordering
1. Persist all changes first
2. Commit transaction
3. Dispatch collected domain events
4. If dispatch fails, changes are already committed (eventual consistency)

---

## Naming Conventions

| Component | Pattern | Example |
|-----------|---------|---------|
| State Enum | `EntityState` | `EntityState` |
| Main Interface | `UnitOfWorkInterface` | `UnitOfWorkInterface` |
| Implementation | `Doctrine{Name}` | `DoctrineUnitOfWork` |
| Tracker | `AggregateTracker` | `AggregateTracker` |
| Transaction | `TransactionManagerInterface` | `TransactionManagerInterface` |
| Test | `{ClassName}Test` | `DoctrineUnitOfWorkTest` |

---

## Quick Template Reference

### UnitOfWorkInterface

```php
interface UnitOfWorkInterface
{
    public function begin(): void;
    public function commit(): void;
    public function rollback(): void;
    public function registerNew(object $entity): void;
    public function registerDirty(object $entity): void;
    public function registerDeleted(object $entity): void;
    public function flush(): void;
}
```

### EntityState

```php
enum EntityState: string
{
    case New = 'new';
    case Clean = 'clean';
    case Dirty = 'dirty';
    case Deleted = 'deleted';

    public function canTransitionTo(self $next): bool;
}
```

### Usage Pattern

```php
$unitOfWork->begin();

try {
    $order = $orderRepository->findById($orderId);
    $order->confirm();
    $unitOfWork->registerDirty($order);

    $payment = Payment::create($order->totalAmount());
    $unitOfWork->registerNew($payment);

    $unitOfWork->flush();
    $unitOfWork->commit();
} catch (\Throwable $e) {
    $unitOfWork->rollback();
    throw $e;
}
```

---

## DI Configuration

```yaml
# Symfony services.yaml
UnitOfWork\UnitOfWorkInterface:
    alias: UnitOfWork\DoctrineUnitOfWork

UnitOfWork\TransactionManagerInterface:
    alias: UnitOfWork\DoctrineTransactionManager
```

---

## Database Notes

No dedicated table needed — Unit of Work operates on existing aggregate tables. Requires database that supports transactions (PostgreSQL, MySQL with InnoDB).

---

## References

For complete PHP templates and test examples, see:
- `references/templates.md` — All component templates
- `references/examples.md` — Order + Payment transaction example and unit tests
