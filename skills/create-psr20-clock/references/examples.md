# PSR-20 Clock Examples

## Domain Service with Clock

```php
<?php

declare(strict_types=1);

namespace App\Domain\Subscription\Service;

use App\Domain\Subscription\Entity\Subscription;
use App\Domain\Subscription\Event\SubscriptionExpiredEvent;
use App\Domain\Subscription\Repository\SubscriptionRepositoryInterface;
use Psr\Clock\ClockInterface;

final readonly class SubscriptionExpirationService
{
    public function __construct(
        private ClockInterface $clock,
        private SubscriptionRepositoryInterface $repository,
    ) {
    }

    public function isExpired(Subscription $subscription): bool
    {
        return $subscription->expiresAt() < $this->clock->now();
    }

    public function daysUntilExpiry(Subscription $subscription): int
    {
        $now = $this->clock->now();
        $expiresAt = $subscription->expiresAt();

        if ($expiresAt <= $now) {
            return 0;
        }

        $diff = $now->diff($expiresAt);

        return $diff->days;
    }

    public function getExpiredSubscriptions(): array
    {
        $now = $this->clock->now();

        return $this->repository->findExpiredBefore($now);
    }

    public function getExpiringWithinDays(int $days): array
    {
        $now = $this->clock->now();
        $threshold = $now->modify("+{$days} days");

        return $this->repository->findExpiringBetween($now, $threshold);
    }
}
```

## Testing Time-Dependent Logic

```php
<?php

declare(strict_types=1);

namespace App\Tests\Unit\Domain\Subscription;

use App\Domain\Subscription\Entity\Subscription;
use App\Domain\Subscription\Service\SubscriptionExpirationService;
use App\Infrastructure\Clock\FrozenClock;
use DateTimeImmutable;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(SubscriptionExpirationService::class)]
final class SubscriptionExpirationServiceTest extends TestCase
{
    public function test_subscription_is_not_expired(): void
    {
        $clock = FrozenClock::at('2024-01-15 10:00:00');
        $service = new SubscriptionExpirationService($clock, $this->createMock(SubscriptionRepositoryInterface::class));

        $subscription = new Subscription(
            expiresAt: new DateTimeImmutable('2024-02-15 10:00:00'),
        );

        self::assertFalse($service->isExpired($subscription));
    }

    public function test_subscription_is_expired(): void
    {
        $clock = FrozenClock::at('2024-03-15 10:00:00');
        $service = new SubscriptionExpirationService($clock, $this->createMock(SubscriptionRepositoryInterface::class));

        $subscription = new Subscription(
            expiresAt: new DateTimeImmutable('2024-02-15 10:00:00'),
        );

        self::assertTrue($service->isExpired($subscription));
    }

    public function test_days_until_expiry(): void
    {
        $clock = FrozenClock::at('2024-01-15 10:00:00');
        $service = new SubscriptionExpirationService($clock, $this->createMock(SubscriptionRepositoryInterface::class));

        $subscription = new Subscription(
            expiresAt: new DateTimeImmutable('2024-01-25 10:00:00'),
        );

        self::assertSame(10, $service->daysUntilExpiry($subscription));
    }

    public function test_days_until_expiry_when_expired(): void
    {
        $clock = FrozenClock::at('2024-02-15 10:00:00');
        $service = new SubscriptionExpirationService($clock, $this->createMock(SubscriptionRepositoryInterface::class));

        $subscription = new Subscription(
            expiresAt: new DateTimeImmutable('2024-01-15 10:00:00'),
        );

        self::assertSame(0, $service->daysUntilExpiry($subscription));
    }
}
```

## Cache Expiration with Clock

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Cache;

use DateInterval;
use DateTimeImmutable;
use Psr\Clock\ClockInterface;

final class CacheItem
{
    private ?DateTimeImmutable $expiresAt = null;

    public function __construct(
        private readonly ClockInterface $clock,
        private readonly string $key,
        private mixed $value = null,
        private bool $isHit = false,
    ) {
    }

    public function getKey(): string
    {
        return $this->key;
    }

    public function get(): mixed
    {
        return $this->value;
    }

    public function isHit(): bool
    {
        if (!$this->isHit) {
            return false;
        }

        if ($this->expiresAt === null) {
            return true;
        }

        return $this->clock->now() < $this->expiresAt;
    }

    public function set(mixed $value): static
    {
        $this->value = $value;
        $this->isHit = true;

        return $this;
    }

    public function expiresAt(?DateTimeImmutable $expiration): static
    {
        $this->expiresAt = $expiration;

        return $this;
    }

    public function expiresAfter(int|DateInterval|null $time): static
    {
        if ($time === null) {
            $this->expiresAt = null;
        } elseif (is_int($time)) {
            $this->expiresAt = $this->clock->now()->modify("+{$time} seconds");
        } else {
            $this->expiresAt = $this->clock->now()->add($time);
        }

        return $this;
    }
}
```

## Rate Limiting with Clock

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\RateLimiter;

use Psr\Clock\ClockInterface;

final class SlidingWindowRateLimiter
{
    /** @var array<string, array{timestamps: int[], windowStart: int}> */
    private array $windows = [];

    public function __construct(
        private readonly ClockInterface $clock,
        private readonly int $maxRequests,
        private readonly int $windowSizeSeconds,
    ) {
    }

    public function isAllowed(string $key): bool
    {
        $now = $this->clock->now()->getTimestamp();
        $windowStart = $now - $this->windowSizeSeconds;

        if (!isset($this->windows[$key])) {
            $this->windows[$key] = ['timestamps' => [], 'windowStart' => $windowStart];
        }

        // Remove old timestamps
        $this->windows[$key]['timestamps'] = array_filter(
            $this->windows[$key]['timestamps'],
            fn(int $timestamp) => $timestamp > $windowStart,
        );

        $currentCount = count($this->windows[$key]['timestamps']);

        if ($currentCount >= $this->maxRequests) {
            return false;
        }

        $this->windows[$key]['timestamps'][] = $now;

        return true;
    }

    public function getRemainingRequests(string $key): int
    {
        $now = $this->clock->now()->getTimestamp();
        $windowStart = $now - $this->windowSizeSeconds;

        if (!isset($this->windows[$key])) {
            return $this->maxRequests;
        }

        $recentRequests = array_filter(
            $this->windows[$key]['timestamps'],
            fn(int $timestamp) => $timestamp > $windowStart,
        );

        return max(0, $this->maxRequests - count($recentRequests));
    }
}
```

## Scheduled Task Runner

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Scheduler;

use Psr\Clock\ClockInterface;

final readonly class ScheduledTask
{
    public function __construct(
        public string $name,
        public string $cronExpression,
        public \Closure $handler,
    ) {
    }
}

final class TaskScheduler
{
    /** @var array<ScheduledTask> */
    private array $tasks = [];

    /** @var array<string, \DateTimeImmutable> */
    private array $lastRun = [];

    public function __construct(
        private readonly ClockInterface $clock,
    ) {
    }

    public function schedule(ScheduledTask $task): void
    {
        $this->tasks[$task->name] = $task;
    }

    public function runDueTasks(): void
    {
        $now = $this->clock->now();

        foreach ($this->tasks as $task) {
            if ($this->isDue($task, $now)) {
                ($task->handler)();
                $this->lastRun[$task->name] = $now;
            }
        }
    }

    public function getNextRunTime(string $taskName): ?\DateTimeImmutable
    {
        if (!isset($this->tasks[$taskName])) {
            return null;
        }

        $task = $this->tasks[$taskName];
        $now = $this->clock->now();

        // Simplified: calculate next run based on cron expression
        return $this->calculateNextRun($task->cronExpression, $now);
    }

    private function isDue(ScheduledTask $task, \DateTimeImmutable $now): bool
    {
        // Implementation would check cron expression against current time
        return true;
    }

    private function calculateNextRun(string $cron, \DateTimeImmutable $from): \DateTimeImmutable
    {
        // Implementation would parse cron and calculate next occurrence
        return $from->modify('+1 hour');
    }
}
```

## DI Container Configuration

```php
<?php

// Symfony services.yaml
services:
    Psr\Clock\ClockInterface:
        class: App\Infrastructure\Clock\SystemClock
        arguments:
            $timezone: 'UTC'

    App\Infrastructure\Clock\SystemClock:
        arguments:
            $timezone: 'UTC'

    # For testing (override in test environment)
    # Psr\Clock\ClockInterface:
    #     class: App\Infrastructure\Clock\FrozenClock
    #     arguments:
    #         $frozenAt: !service { class: DateTimeImmutable, arguments: ['2024-01-15 10:00:00'] }
```

```php
<?php

// Laravel AppServiceProvider
use App\Infrastructure\Clock\SystemClock;
use Psr\Clock\ClockInterface;

public function register(): void
{
    $this->app->singleton(ClockInterface::class, function () {
        return new SystemClock('UTC');
    });
}

// For testing
public function register(): void
{
    $this->app->singleton(ClockInterface::class, function () {
        return FrozenClock::at('2024-01-15 10:00:00');
    });
}
```
