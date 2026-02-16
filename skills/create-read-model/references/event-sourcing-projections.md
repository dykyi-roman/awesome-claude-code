# Event Sourcing Projections

Advanced projection patterns for rebuilding read models from event stores.

## Event Replay Projection

### ProjectionRunnerInterface

**File:** `src/Application/{BoundedContext}/Projection/ProjectionRunnerInterface.php`

```php
<?php

declare(strict_types=1);

namespace Application\{BoundedContext}\Projection;

interface ProjectionRunnerInterface
{
    public function run(string $projectionName): void;

    public function rebuild(string $projectionName): void;

    public function stop(string $projectionName): void;
}
```

---

### ProjectionRunner

**File:** `src/Application/{BoundedContext}/Projection/ProjectionRunner.php`

```php
<?php

declare(strict_types=1);

namespace Application\{BoundedContext}\Projection;

use Domain\{BoundedContext}\EventStore\EventStoreInterface;
use Psr\Log\LoggerInterface;

final readonly class ProjectionRunner implements ProjectionRunnerInterface
{
    /**
     * @param array<string, ProjectionInterface> $projections
     */
    public function __construct(
        private EventStoreInterface $eventStore,
        private ProjectionCheckpointStore $checkpointStore,
        private array $projections,
        private LoggerInterface $logger,
        private int $batchSize = 100
    ) {}

    public function run(string $projectionName): void
    {
        $projection = $this->getProjection($projectionName);
        $checkpoint = $this->checkpointStore->load($projectionName);
        $fromPosition = $checkpoint?->lastPosition ?? 0;

        $events = $this->eventStore->loadAllFromPosition($fromPosition, $this->batchSize);

        foreach ($events as $event) {
            $projection->project($event);
            $this->checkpointStore->save(
                new ProjectionCheckpoint(
                    projectionName: $projectionName,
                    lastPosition: $event->position,
                    updatedAt: new \DateTimeImmutable()
                )
            );
        }
    }

    public function rebuild(string $projectionName): void
    {
        $projection = $this->getProjection($projectionName);
        $projection->reset();
        $this->checkpointStore->delete($projectionName);

        $this->logger->info('Rebuilding projection', ['projection' => $projectionName]);
        $this->run($projectionName);
    }

    public function stop(string $projectionName): void
    {
        $this->checkpointStore->markStopped($projectionName);
    }

    private function getProjection(string $name): ProjectionInterface
    {
        if (!isset($this->projections[$name])) {
            throw new \InvalidArgumentException(
                sprintf('Projection "%s" not registered', $name)
            );
        }

        return $this->projections[$name];
    }
}
```

---

## Projection Versioning

### ProjectionVersion

**File:** `src/Application/{BoundedContext}/Projection/ProjectionVersion.php`

```php
<?php

declare(strict_types=1);

namespace Application\{BoundedContext}\Projection;

final readonly class ProjectionVersion
{
    public function __construct(
        public string $projectionName,
        public int $version,
        public string $schemaHash
    ) {}

    public function requiresMigration(self $current): bool
    {
        return $this->version !== $current->version
            || $this->schemaHash !== $current->schemaHash;
    }

    public function toString(): string
    {
        return sprintf('%s:v%d:%s', $this->projectionName, $this->version, $this->schemaHash);
    }
}
```

---

### VersionedProjectionInterface

**File:** `src/Application/{BoundedContext}/Projection/VersionedProjectionInterface.php`

```php
<?php

declare(strict_types=1);

namespace Application\{BoundedContext}\Projection;

interface VersionedProjectionInterface extends ProjectionInterface
{
    public function getVersion(): ProjectionVersion;

    public function migrate(ProjectionVersion $fromVersion): void;
}
```

---

## Checkpoint Tracking

### ProjectionCheckpoint

**File:** `src/Application/{BoundedContext}/Projection/ProjectionCheckpoint.php`

```php
<?php

declare(strict_types=1);

namespace Application\{BoundedContext}\Projection;

final readonly class ProjectionCheckpoint
{
    public function __construct(
        public string $projectionName,
        public int $lastPosition,
        public \DateTimeImmutable $updatedAt
    ) {}

    public function toArray(): array
    {
        return [
            'projection_name' => $this->projectionName,
            'last_position' => $this->lastPosition,
            'updated_at' => $this->updatedAt->format('Y-m-d H:i:s'),
        ];
    }

    public static function fromArray(array $data): self
    {
        return new self(
            projectionName: $data['projection_name'],
            lastPosition: (int) $data['last_position'],
            updatedAt: new \DateTimeImmutable($data['updated_at'])
        );
    }
}
```

---

### ProjectionCheckpointStore

**File:** `src/Application/{BoundedContext}/Projection/ProjectionCheckpointStore.php`

```php
<?php

declare(strict_types=1);

namespace Application\{BoundedContext}\Projection;

interface ProjectionCheckpointStore
{
    public function load(string $projectionName): ?ProjectionCheckpoint;

    public function save(ProjectionCheckpoint $checkpoint): void;

    public function delete(string $projectionName): void;

    public function markStopped(string $projectionName): void;
}
```

---

### DoctrineProjectionCheckpointStore

**File:** `src/Infrastructure/{BoundedContext}/Projection/DoctrineProjectionCheckpointStore.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\{BoundedContext}\Projection;

use Application\{BoundedContext}\Projection\ProjectionCheckpoint;
use Application\{BoundedContext}\Projection\ProjectionCheckpointStore;
use Doctrine\DBAL\Connection;

final readonly class DoctrineProjectionCheckpointStore implements ProjectionCheckpointStore
{
    public function __construct(
        private Connection $connection
    ) {}

    public function load(string $projectionName): ?ProjectionCheckpoint
    {
        $row = $this->connection->fetchAssociative(
            'SELECT * FROM projection_checkpoints WHERE projection_name = ?',
            [$projectionName]
        );

        if ($row === false) {
            return null;
        }

        return ProjectionCheckpoint::fromArray($row);
    }

    public function save(ProjectionCheckpoint $checkpoint): void
    {
        $this->connection->executeStatement(
            'INSERT INTO projection_checkpoints (projection_name, last_position, updated_at)
             VALUES (:name, :position, :updated_at)
             ON DUPLICATE KEY UPDATE last_position = :position, updated_at = :updated_at',
            [
                'name' => $checkpoint->projectionName,
                'position' => $checkpoint->lastPosition,
                'updated_at' => $checkpoint->updatedAt->format('Y-m-d H:i:s'),
            ]
        );
    }

    public function delete(string $projectionName): void
    {
        $this->connection->executeStatement(
            'DELETE FROM projection_checkpoints WHERE projection_name = ?',
            [$projectionName]
        );
    }

    public function markStopped(string $projectionName): void
    {
        $this->connection->executeStatement(
            'UPDATE projection_checkpoints SET stopped = 1 WHERE projection_name = ?',
            [$projectionName]
        );
    }
}
```

---

## Async Projection

### ProjectionWorker

**File:** `src/Infrastructure/{BoundedContext}/Projection/ProjectionWorker.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\{BoundedContext}\Projection;

use Application\{BoundedContext}\Projection\ProjectionRunnerInterface;
use Psr\Log\LoggerInterface;

final class ProjectionWorker
{
    private bool $running = false;

    public function __construct(
        private readonly ProjectionRunnerInterface $runner,
        private readonly LoggerInterface $logger,
        private readonly int $pollIntervalMs = 100,
        private readonly int $idleTimeoutMs = 1000
    ) {}

    public function start(string $projectionName): void
    {
        $this->running = true;
        $this->logger->info('Starting projection worker', ['projection' => $projectionName]);

        while ($this->running) {
            try {
                $this->runner->run($projectionName);
                usleep($this->pollIntervalMs * 1000);
            } catch (\Throwable $e) {
                $this->logger->error('Projection worker error', [
                    'projection' => $projectionName,
                    'error' => $e->getMessage(),
                ]);
                usleep($this->idleTimeoutMs * 1000);
            }
        }
    }

    public function stop(): void
    {
        $this->running = false;
    }
}
```

---

## Database Schema

```sql
CREATE TABLE projection_checkpoints (
    projection_name VARCHAR(255) PRIMARY KEY,
    last_position BIGINT NOT NULL DEFAULT 0,
    stopped TINYINT(1) NOT NULL DEFAULT 0,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_stopped (stopped)
);
```

---

## Tests

### ProjectionRunnerTest

**File:** `tests/Unit/Application/{BoundedContext}/Projection/ProjectionRunnerTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Application\{BoundedContext}\Projection;

use Application\{BoundedContext}\Projection\ProjectionCheckpoint;
use Application\{BoundedContext}\Projection\ProjectionCheckpointStore;
use Application\{BoundedContext}\Projection\ProjectionInterface;
use Application\{BoundedContext}\Projection\ProjectionRunner;
use Domain\{BoundedContext}\EventStore\EventStoreInterface;
use Domain\{BoundedContext}\EventStore\EventStream;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;
use Psr\Log\NullLogger;

#[Group('unit')]
#[CoversClass(ProjectionRunner::class)]
final class ProjectionRunnerTest extends TestCase
{
    public function testRunProjectsEventsFromCheckpoint(): void
    {
        $projection = $this->createMock(ProjectionInterface::class);
        $projection->expects(self::atLeastOnce())->method('project');

        $checkpoint = new ProjectionCheckpoint('order-summary', 5, new \DateTimeImmutable());
        $checkpointStore = $this->createMock(ProjectionCheckpointStore::class);
        $checkpointStore->method('load')->willReturn($checkpoint);

        $eventStore = $this->createMock(EventStoreInterface::class);
        $eventStore->method('loadAllFromPosition')->willReturn(EventStream::empty());

        $runner = new ProjectionRunner(
            eventStore: $eventStore,
            checkpointStore: $checkpointStore,
            projections: ['order-summary' => $projection],
            logger: new NullLogger()
        );

        $runner->run('order-summary');
    }

    public function testRebuildResetsAndReruns(): void
    {
        $projection = $this->createMock(ProjectionInterface::class);
        $projection->expects(self::once())->method('reset');

        $checkpointStore = $this->createMock(ProjectionCheckpointStore::class);
        $checkpointStore->expects(self::once())->method('delete')->with('order-summary');

        $eventStore = $this->createMock(EventStoreInterface::class);
        $eventStore->method('loadAllFromPosition')->willReturn(EventStream::empty());

        $runner = new ProjectionRunner(
            eventStore: $eventStore,
            checkpointStore: $checkpointStore,
            projections: ['order-summary' => $projection],
            logger: new NullLogger()
        );

        $runner->rebuild('order-summary');
    }

    public function testThrowsForUnregisteredProjection(): void
    {
        $eventStore = $this->createMock(EventStoreInterface::class);
        $checkpointStore = $this->createMock(ProjectionCheckpointStore::class);

        $runner = new ProjectionRunner(
            eventStore: $eventStore,
            checkpointStore: $checkpointStore,
            projections: [],
            logger: new NullLogger()
        );

        $this->expectException(\InvalidArgumentException::class);
        $runner->run('unknown');
    }
}
```

---

### ProjectionCheckpointTest

**File:** `tests/Unit/Application/{BoundedContext}/Projection/ProjectionCheckpointTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Application\{BoundedContext}\Projection;

use Application\{BoundedContext}\Projection\ProjectionCheckpoint;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(ProjectionCheckpoint::class)]
final class ProjectionCheckpointTest extends TestCase
{
    public function testConstructsWithProperties(): void
    {
        $now = new \DateTimeImmutable();
        $checkpoint = new ProjectionCheckpoint('order-summary', 42, $now);

        self::assertSame('order-summary', $checkpoint->projectionName);
        self::assertSame(42, $checkpoint->lastPosition);
        self::assertSame($now, $checkpoint->updatedAt);
    }

    public function testToArrayReturnsExpectedFormat(): void
    {
        $now = new \DateTimeImmutable('2025-01-15 10:30:00');
        $checkpoint = new ProjectionCheckpoint('order-summary', 42, $now);

        $array = $checkpoint->toArray();

        self::assertSame('order-summary', $array['projection_name']);
        self::assertSame(42, $array['last_position']);
        self::assertSame('2025-01-15 10:30:00', $array['updated_at']);
    }

    public function testFromArrayCreatesInstance(): void
    {
        $data = [
            'projection_name' => 'user-profile',
            'last_position' => '100',
            'updated_at' => '2025-01-15 10:30:00',
        ];

        $checkpoint = ProjectionCheckpoint::fromArray($data);

        self::assertSame('user-profile', $checkpoint->projectionName);
        self::assertSame(100, $checkpoint->lastPosition);
    }
}
```
