# Unit of Work Templates

Complete PHP 8.4 templates for all Unit of Work pattern components.

---

## Domain Layer

### EntityState Enum

**Path:** `src/Domain/Shared/UnitOfWork/EntityState.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\UnitOfWork;

enum EntityState: string
{
    case New = 'new';
    case Clean = 'clean';
    case Dirty = 'dirty';
    case Deleted = 'deleted';

    public function canTransitionTo(self $next): bool
    {
        return match ($this) {
            self::New => $next === self::Dirty || $next === self::Deleted,
            self::Clean => $next === self::Dirty || $next === self::Deleted,
            self::Dirty => $next === self::Deleted,
            self::Deleted => false,
        };
    }

    public function isManaged(): bool
    {
        return $this !== self::Deleted;
    }

    public function isNew(): bool
    {
        return $this === self::New;
    }

    public function isClean(): bool
    {
        return $this === self::Clean;
    }

    public function isDirty(): bool
    {
        return $this === self::Dirty;
    }

    public function isDeleted(): bool
    {
        return $this === self::Deleted;
    }
}
```

---

### TransactionManagerInterface

**Path:** `src/Domain/Shared/UnitOfWork/TransactionManagerInterface.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\UnitOfWork;

interface TransactionManagerInterface
{
    public function begin(): void;

    public function commit(): void;

    public function rollback(): void;

    public function createSavepoint(string $name): void;

    public function releaseSavepoint(string $name): void;

    public function rollbackToSavepoint(string $name): void;

    public function isTransactionActive(): bool;
}
```

---

### DomainEventCollectorInterface

**Path:** `src/Domain/Shared/UnitOfWork/DomainEventCollectorInterface.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\UnitOfWork;

interface DomainEventCollectorInterface
{
    /**
     * @param array<object> $events
     */
    public function collect(array $events): void;

    public function flush(): void;

    public function clear(): void;
}
```

---

## Application Layer

### UnitOfWorkInterface

**Path:** `src/Application/Shared/UnitOfWork/UnitOfWorkInterface.php`

```php
<?php

declare(strict_types=1);

namespace Application\Shared\UnitOfWork;

interface UnitOfWorkInterface
{
    public function begin(): void;

    public function commit(): void;

    public function rollback(): void;

    public function registerNew(object $entity): void;

    public function registerClean(object $entity): void;

    public function registerDirty(object $entity): void;

    public function registerDeleted(object $entity): void;

    public function flush(): void;

    public function clear(): void;

    public function isManaged(object $entity): bool;

    public function getState(object $entity): ?EntityState;
}
```

---

### AggregateTracker

**Path:** `src/Application/Shared/UnitOfWork/AggregateTracker.php`

```php
<?php

declare(strict_types=1);

namespace Application\Shared\UnitOfWork;

use Domain\Shared\UnitOfWork\EntityState;

final class AggregateTracker
{
    /**
     * @var array<int, object>
     */
    private array $identityMap = [];

    /**
     * @var array<int, EntityState>
     */
    private array $states = [];

    public function register(object $entity, EntityState $state): void
    {
        $id = $this->getObjectId($entity);

        if (isset($this->states[$id])) {
            $currentState = $this->states[$id];
            if (!$currentState->canTransitionTo($state)) {
                throw new \RuntimeException(sprintf(
                    'Invalid state transition from %s to %s for entity %s',
                    $currentState->value,
                    $state->value,
                    get_class($entity)
                ));
            }
        }

        $this->identityMap[$id] = $entity;
        $this->states[$id] = $state;
    }

    public function getState(object $entity): ?EntityState
    {
        $id = $this->getObjectId($entity);

        return $this->states[$id] ?? null;
    }

    public function isManaged(object $entity): bool
    {
        $id = $this->getObjectId($entity);

        return isset($this->identityMap[$id]);
    }

    /**
     * @return array<object>
     */
    public function getNew(): array
    {
        return $this->getByState(EntityState::New);
    }

    /**
     * @return array<object>
     */
    public function getDirty(): array
    {
        return $this->getByState(EntityState::Dirty);
    }

    /**
     * @return array<object>
     */
    public function getDeleted(): array
    {
        return $this->getByState(EntityState::Deleted);
    }

    public function clear(): void
    {
        $this->identityMap = [];
        $this->states = [];
    }

    /**
     * @return array<object>
     */
    private function getByState(EntityState $state): array
    {
        $result = [];

        foreach ($this->states as $id => $entityState) {
            if ($entityState === $state) {
                $result[] = $this->identityMap[$id];
            }
        }

        return $result;
    }

    private function getObjectId(object $entity): int
    {
        return spl_object_id($entity);
    }
}
```

---

## Infrastructure Layer

### DoctrineUnitOfWork

**Path:** `src/Infrastructure/Persistence/UnitOfWork/DoctrineUnitOfWork.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Persistence\UnitOfWork;

use Application\Shared\UnitOfWork\AggregateTracker;
use Application\Shared\UnitOfWork\UnitOfWorkInterface;
use Domain\Shared\Event\HasDomainEventsInterface;
use Domain\Shared\UnitOfWork\DomainEventCollectorInterface;
use Domain\Shared\UnitOfWork\EntityState;
use Domain\Shared\UnitOfWork\TransactionManagerInterface;
use Doctrine\ORM\EntityManagerInterface;

final readonly class DoctrineUnitOfWork implements UnitOfWorkInterface
{
    private AggregateTracker $tracker;

    public function __construct(
        private EntityManagerInterface $entityManager,
        private TransactionManagerInterface $transactionManager,
        private DomainEventCollectorInterface $eventCollector,
    ) {
        $this->tracker = new AggregateTracker();
    }

    public function begin(): void
    {
        $this->transactionManager->begin();
    }

    public function commit(): void
    {
        $this->transactionManager->commit();
        $this->eventCollector->flush();
    }

    public function rollback(): void
    {
        $this->transactionManager->rollback();
        $this->eventCollector->clear();
        $this->tracker->clear();
    }

    public function registerNew(object $entity): void
    {
        $this->tracker->register($entity, EntityState::New);
    }

    public function registerClean(object $entity): void
    {
        $this->tracker->register($entity, EntityState::Clean);
    }

    public function registerDirty(object $entity): void
    {
        $this->tracker->register($entity, EntityState::Dirty);
    }

    public function registerDeleted(object $entity): void
    {
        $this->tracker->register($entity, EntityState::Deleted);
    }

    public function flush(): void
    {
        $this->persistNew();
        $this->persistDirty();
        $this->persistDeleted();

        $this->entityManager->flush();

        $this->collectEvents();
    }

    public function clear(): void
    {
        $this->tracker->clear();
        $this->eventCollector->clear();
    }

    public function isManaged(object $entity): bool
    {
        return $this->tracker->isManaged($entity);
    }

    public function getState(object $entity): ?EntityState
    {
        return $this->tracker->getState($entity);
    }

    private function persistNew(): void
    {
        foreach ($this->tracker->getNew() as $entity) {
            $this->entityManager->persist($entity);
        }
    }

    private function persistDirty(): void
    {
        foreach ($this->tracker->getDirty() as $entity) {
            $this->entityManager->persist($entity);
        }
    }

    private function persistDeleted(): void
    {
        foreach ($this->tracker->getDeleted() as $entity) {
            $this->entityManager->remove($entity);
        }
    }

    private function collectEvents(): void
    {
        $events = [];

        foreach (array_merge($this->tracker->getNew(), $this->tracker->getDirty()) as $entity) {
            if ($entity instanceof HasDomainEventsInterface) {
                $events = array_merge($events, $entity->releaseEvents());
            }
        }

        if (count($events) > 0) {
            $this->eventCollector->collect($events);
        }
    }
}
```

---

### DoctrineTransactionManager

**Path:** `src/Infrastructure/Persistence/UnitOfWork/DoctrineTransactionManager.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Persistence\UnitOfWork;

use Doctrine\DBAL\Connection;
use Domain\Shared\UnitOfWork\TransactionManagerInterface;

final readonly class DoctrineTransactionManager implements TransactionManagerInterface
{
    public function __construct(
        private Connection $connection,
    ) {
    }

    public function begin(): void
    {
        $this->connection->beginTransaction();
    }

    public function commit(): void
    {
        $this->connection->commit();
    }

    public function rollback(): void
    {
        $this->connection->rollBack();
    }

    public function createSavepoint(string $name): void
    {
        $this->connection->createSavepoint($name);
    }

    public function releaseSavepoint(string $name): void
    {
        $this->connection->releaseSavepoint($name);
    }

    public function rollbackToSavepoint(string $name): void
    {
        $this->connection->rollbackSavepoint($name);
    }

    public function isTransactionActive(): bool
    {
        return $this->connection->isTransactionActive();
    }
}
```

---

### DomainEventCollector

**Path:** `src/Infrastructure/Persistence/UnitOfWork/DomainEventCollector.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Persistence\UnitOfWork;

use Domain\Shared\UnitOfWork\DomainEventCollectorInterface;
use Psr\EventDispatcher\EventDispatcherInterface;

final class DomainEventCollector implements DomainEventCollectorInterface
{
    /**
     * @var array<object>
     */
    private array $events = [];

    public function __construct(
        private readonly EventDispatcherInterface $eventDispatcher,
    ) {
    }

    public function collect(array $events): void
    {
        $this->events = array_merge($this->events, $events);
    }

    public function flush(): void
    {
        foreach ($this->events as $event) {
            $this->eventDispatcher->dispatch($event);
        }

        $this->clear();
    }

    public function clear(): void
    {
        $this->events = [];
    }
}
```

---

## HasDomainEventsInterface (Helper)

**Path:** `src/Domain/Shared/Event/HasDomainEventsInterface.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\Event;

interface HasDomainEventsInterface
{
    /**
     * @return array<object>
     */
    public function releaseEvents(): array;
}
```

---

## Usage Example Trait

**Path:** `src/Domain/Shared/Event/RaisesDomainEventsTrait.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\Event;

trait RaisesDomainEventsTrait
{
    /**
     * @var array<object>
     */
    private array $domainEvents = [];

    protected function raiseEvent(object $event): void
    {
        $this->domainEvents[] = $event;
    }

    public function releaseEvents(): array
    {
        $events = $this->domainEvents;
        $this->domainEvents = [];

        return $events;
    }
}
```

---

## Test Templates

### EntityStateTest

**Path:** `tests/Unit/Domain/Shared/UnitOfWork/EntityStateTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\Shared\UnitOfWork;

use Domain\Shared\UnitOfWork\EntityState;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(EntityState::class)]
final class EntityStateTest extends TestCase
{
    public function testNewCanTransitionToDirty(): void
    {
        $state = EntityState::New;

        self::assertTrue($state->canTransitionTo(EntityState::Dirty));
    }

    public function testNewCanTransitionToDeleted(): void
    {
        $state = EntityState::New;

        self::assertTrue($state->canTransitionTo(EntityState::Deleted));
    }

    public function testCleanCanTransitionToDirty(): void
    {
        $state = EntityState::Clean;

        self::assertTrue($state->canTransitionTo(EntityState::Dirty));
    }

    public function testCleanCanTransitionToDeleted(): void
    {
        $state = EntityState::Clean;

        self::assertTrue($state->canTransitionTo(EntityState::Deleted));
    }

    public function testDirtyCanTransitionToDeleted(): void
    {
        $state = EntityState::Dirty;

        self::assertTrue($state->canTransitionTo(EntityState::Deleted));
    }

    public function testDeletedCannotTransition(): void
    {
        $state = EntityState::Deleted;

        self::assertFalse($state->canTransitionTo(EntityState::New));
        self::assertFalse($state->canTransitionTo(EntityState::Clean));
        self::assertFalse($state->canTransitionTo(EntityState::Dirty));
    }

    public function testIsManaged(): void
    {
        self::assertTrue(EntityState::New->isManaged());
        self::assertTrue(EntityState::Clean->isManaged());
        self::assertTrue(EntityState::Dirty->isManaged());
        self::assertFalse(EntityState::Deleted->isManaged());
    }

    public function testIsNew(): void
    {
        self::assertTrue(EntityState::New->isNew());
        self::assertFalse(EntityState::Clean->isNew());
    }

    public function testIsClean(): void
    {
        self::assertTrue(EntityState::Clean->isClean());
        self::assertFalse(EntityState::New->isClean());
    }

    public function testIsDirty(): void
    {
        self::assertTrue(EntityState::Dirty->isDirty());
        self::assertFalse(EntityState::Clean->isDirty());
    }

    public function testIsDeleted(): void
    {
        self::assertTrue(EntityState::Deleted->isDeleted());
        self::assertFalse(EntityState::Clean->isDeleted());
    }
}
```

---

### AggregateTrackerTest

**Path:** `tests/Unit/Application/Shared/UnitOfWork/AggregateTrackerTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Application\Shared\UnitOfWork;

use Application\Shared\UnitOfWork\AggregateTracker;
use Domain\Shared\UnitOfWork\EntityState;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(AggregateTracker::class)]
final class AggregateTrackerTest extends TestCase
{
    private AggregateTracker $tracker;

    protected function setUp(): void
    {
        $this->tracker = new AggregateTracker();
    }

    public function testRegisterNewEntity(): void
    {
        $entity = new \stdClass();

        $this->tracker->register($entity, EntityState::New);

        self::assertTrue($this->tracker->isManaged($entity));
        self::assertSame(EntityState::New, $this->tracker->getState($entity));
    }

    public function testGetNew(): void
    {
        $entity1 = new \stdClass();
        $entity2 = new \stdClass();

        $this->tracker->register($entity1, EntityState::New);
        $this->tracker->register($entity2, EntityState::Dirty);

        $newEntities = $this->tracker->getNew();

        self::assertCount(1, $newEntities);
        self::assertContains($entity1, $newEntities);
    }

    public function testGetDirty(): void
    {
        $entity = new \stdClass();

        $this->tracker->register($entity, EntityState::Dirty);

        $dirtyEntities = $this->tracker->getDirty();

        self::assertCount(1, $dirtyEntities);
        self::assertContains($entity, $dirtyEntities);
    }

    public function testGetDeleted(): void
    {
        $entity = new \stdClass();

        $this->tracker->register($entity, EntityState::Deleted);

        $deletedEntities = $this->tracker->getDeleted();

        self::assertCount(1, $deletedEntities);
        self::assertContains($entity, $deletedEntities);
    }

    public function testTransitionFromNewToDirty(): void
    {
        $entity = new \stdClass();

        $this->tracker->register($entity, EntityState::New);
        $this->tracker->register($entity, EntityState::Dirty);

        self::assertSame(EntityState::Dirty, $this->tracker->getState($entity));
    }

    public function testInvalidTransitionThrowsException(): void
    {
        $entity = new \stdClass();

        $this->tracker->register($entity, EntityState::Deleted);

        $this->expectException(\RuntimeException::class);
        $this->expectExceptionMessage('Invalid state transition');

        $this->tracker->register($entity, EntityState::New);
    }

    public function testClear(): void
    {
        $entity = new \stdClass();

        $this->tracker->register($entity, EntityState::New);
        $this->tracker->clear();

        self::assertFalse($this->tracker->isManaged($entity));
        self::assertNull($this->tracker->getState($entity));
    }
}
```

---

### DoctrineUnitOfWorkTest

**Path:** `tests/Unit/Infrastructure/Persistence/UnitOfWork/DoctrineUnitOfWorkTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Infrastructure\Persistence\UnitOfWork;

use Domain\Shared\Event\HasDomainEventsInterface;
use Domain\Shared\UnitOfWork\DomainEventCollectorInterface;
use Domain\Shared\UnitOfWork\EntityState;
use Domain\Shared\UnitOfWork\TransactionManagerInterface;
use Doctrine\ORM\EntityManagerInterface;
use Infrastructure\Persistence\UnitOfWork\DoctrineUnitOfWork;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(DoctrineUnitOfWork::class)]
final class DoctrineUnitOfWorkTest extends TestCase
{
    private EntityManagerInterface $entityManager;
    private TransactionManagerInterface $transactionManager;
    private DomainEventCollectorInterface $eventCollector;
    private DoctrineUnitOfWork $unitOfWork;

    protected function setUp(): void
    {
        $this->entityManager = $this->createMock(EntityManagerInterface::class);
        $this->transactionManager = $this->createMock(TransactionManagerInterface::class);
        $this->eventCollector = $this->createMock(DomainEventCollectorInterface::class);

        $this->unitOfWork = new DoctrineUnitOfWork(
            $this->entityManager,
            $this->transactionManager,
            $this->eventCollector,
        );
    }

    public function testBeginDelegatesToTransactionManager(): void
    {
        $this->transactionManager->expects($this->once())->method('begin');

        $this->unitOfWork->begin();
    }

    public function testCommitDelegatesToTransactionManagerAndFlushesEvents(): void
    {
        $this->transactionManager->expects($this->once())->method('commit');
        $this->eventCollector->expects($this->once())->method('flush');

        $this->unitOfWork->commit();
    }

    public function testRollbackClearsTrackerAndEvents(): void
    {
        $this->transactionManager->expects($this->once())->method('rollback');
        $this->eventCollector->expects($this->once())->method('clear');

        $this->unitOfWork->rollback();
    }

    public function testRegisterNew(): void
    {
        $entity = new \stdClass();

        $this->unitOfWork->registerNew($entity);

        self::assertTrue($this->unitOfWork->isManaged($entity));
        self::assertSame(EntityState::New, $this->unitOfWork->getState($entity));
    }

    public function testRegisterDirty(): void
    {
        $entity = new \stdClass();

        $this->unitOfWork->registerDirty($entity);

        self::assertTrue($this->unitOfWork->isManaged($entity));
        self::assertSame(EntityState::Dirty, $this->unitOfWork->getState($entity));
    }

    public function testRegisterDeleted(): void
    {
        $entity = new \stdClass();

        $this->unitOfWork->registerDeleted($entity);

        self::assertTrue($this->unitOfWork->isManaged($entity));
        self::assertSame(EntityState::Deleted, $this->unitOfWork->getState($entity));
    }

    public function testFlushPersistsNewEntities(): void
    {
        $entity = new \stdClass();

        $this->entityManager->expects($this->once())
            ->method('persist')
            ->with($entity);
        $this->entityManager->expects($this->once())->method('flush');

        $this->unitOfWork->registerNew($entity);
        $this->unitOfWork->flush();
    }

    public function testFlushPersistsDirtyEntities(): void
    {
        $entity = new \stdClass();

        $this->entityManager->expects($this->once())
            ->method('persist')
            ->with($entity);
        $this->entityManager->expects($this->once())->method('flush');

        $this->unitOfWork->registerDirty($entity);
        $this->unitOfWork->flush();
    }

    public function testFlushRemovesDeletedEntities(): void
    {
        $entity = new \stdClass();

        $this->entityManager->expects($this->once())
            ->method('remove')
            ->with($entity);
        $this->entityManager->expects($this->once())->method('flush');

        $this->unitOfWork->registerDeleted($entity);
        $this->unitOfWork->flush();
    }

    public function testFlushCollectsEventsFromAggregates(): void
    {
        $event = new \stdClass();
        $entity = $this->createMock(HasDomainEventsInterface::class);
        $entity->method('releaseEvents')->willReturn([$event]);

        $this->eventCollector->expects($this->once())
            ->method('collect')
            ->with([$event]);

        $this->entityManager->expects($this->once())->method('persist');
        $this->entityManager->expects($this->once())->method('flush');

        $this->unitOfWork->registerNew($entity);
        $this->unitOfWork->flush();
    }

    public function testClear(): void
    {
        $entity = new \stdClass();

        $this->unitOfWork->registerNew($entity);
        $this->unitOfWork->clear();

        self::assertFalse($this->unitOfWork->isManaged($entity));
    }
}
```
