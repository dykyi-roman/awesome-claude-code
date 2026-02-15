---
name: acc-create-unit-of-work
description: Generates Unit of Work pattern components for PHP 8.4. Creates transactional consistency infrastructure with aggregate tracking, flush/rollback, domain event collection, and unit tests.
---

# Unit of Work Generator

Creates Unit of Work pattern infrastructure for transactional consistency across multiple aggregates.

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
- Application layer port
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
- Domain layer contract

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

1. **Domain Layer** (`src/Domain/Shared/UnitOfWork/`)
   - `EntityState.php` — State enum (New, Clean, Dirty, Deleted)
   - `TransactionManagerInterface.php` — Transaction contract
   - `DomainEventCollectorInterface.php` — Event collection contract

2. **Application Layer** (`src/Application/Shared/UnitOfWork/`)
   - `UnitOfWorkInterface.php` — Main port
   - `AggregateTracker.php` — Identity map and change tracking

3. **Infrastructure Layer** (`src/Infrastructure/Persistence/UnitOfWork/`)
   - `DoctrineUnitOfWork.php` — Doctrine-based implementation
   - `DoctrineTransactionManager.php` — Doctrine transaction manager
   - `DomainEventCollector.php` — Event collector with dispatcher

4. **Tests**
   - `EntityStateTest.php`
   - `AggregateTrackerTest.php`
   - `DoctrineUnitOfWorkTest.php`

### Step 3: Generate Context-Specific Integration

For each context (e.g., Order):
```
src/Application/{Context}/
└── {Context}UnitOfWorkAware.php (trait or base class)
```

---

## File Placement

| Layer | Path |
|-------|------|
| Domain Types | `src/Domain/Shared/UnitOfWork/` |
| Application Port | `src/Application/Shared/UnitOfWork/` |
| Infrastructure | `src/Infrastructure/Persistence/UnitOfWork/` |
| Unit Tests | `tests/Unit/{Layer}/{Path}/` |

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
Application\Shared\UnitOfWork\UnitOfWorkInterface:
    alias: Infrastructure\Persistence\UnitOfWork\DoctrineUnitOfWork

Domain\Shared\UnitOfWork\TransactionManagerInterface:
    alias: Infrastructure\Persistence\UnitOfWork\DoctrineTransactionManager
```

---

## Database Notes

No dedicated table needed — Unit of Work operates on existing aggregate tables. Requires database that supports transactions (PostgreSQL, MySQL with InnoDB).

---

## References

For complete PHP templates and test examples, see:
- `references/templates.md` — All component templates
- `references/examples.md` — Order + Payment transaction example and unit tests
