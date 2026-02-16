# PSR-20 Clock Templates

## Adjustable Clock (Testing)

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Clock;

use DateInterval;
use DateTimeImmutable;
use Psr\Clock\ClockInterface;

final class AdjustableClock implements ClockInterface
{
    private DateTimeImmutable $currentTime;

    public function __construct(
        ?DateTimeImmutable $startTime = null,
    ) {
        $this->currentTime = $startTime ?? new DateTimeImmutable();
    }

    public function now(): DateTimeImmutable
    {
        return $this->currentTime;
    }

    public function advance(DateInterval $interval): void
    {
        $this->currentTime = $this->currentTime->add($interval);
    }

    public function rewind(DateInterval $interval): void
    {
        $this->currentTime = $this->currentTime->sub($interval);
    }

    public function advanceSeconds(int $seconds): void
    {
        $this->currentTime = $this->currentTime->modify("+{$seconds} seconds");
    }

    public function advanceMinutes(int $minutes): void
    {
        $this->currentTime = $this->currentTime->modify("+{$minutes} minutes");
    }

    public function advanceHours(int $hours): void
    {
        $this->currentTime = $this->currentTime->modify("+{$hours} hours");
    }

    public function advanceDays(int $days): void
    {
        $this->currentTime = $this->currentTime->modify("+{$days} days");
    }

    public function setTo(DateTimeImmutable $time): void
    {
        $this->currentTime = $time;
    }

    public function reset(): void
    {
        $this->currentTime = new DateTimeImmutable();
    }
}
```

## Callback Clock

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Clock;

use DateTimeImmutable;
use Psr\Clock\ClockInterface;

final readonly class CallbackClock implements ClockInterface
{
    /** @var callable(): DateTimeImmutable */
    private $callback;

    public function __construct(callable $callback)
    {
        $this->callback = $callback;
    }

    public function now(): DateTimeImmutable
    {
        return ($this->callback)();
    }
}

// Usage
$clock = new CallbackClock(fn() => new DateTimeImmutable('2024-01-15'));
```

## Fixed Offset Clock

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Clock;

use DateTimeImmutable;
use DateTimeZone;
use Psr\Clock\ClockInterface;

final readonly class FixedOffsetClock implements ClockInterface
{
    public function __construct(
        private ClockInterface $baseClock,
        private string $targetTimezone,
    ) {
    }

    public function now(): DateTimeImmutable
    {
        return $this->baseClock->now()
            ->setTimezone(new DateTimeZone($this->targetTimezone));
    }

    public static function utc(ClockInterface $clock): self
    {
        return new self($clock, 'UTC');
    }

    public static function fromOffset(ClockInterface $clock, string $offset): self
    {
        return new self($clock, $offset);
    }
}
```

## Sequence Clock (Testing)

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Clock;

use DateTimeImmutable;
use Psr\Clock\ClockInterface;
use RuntimeException;

final class SequenceClock implements ClockInterface
{
    private int $index = 0;

    /** @var array<DateTimeImmutable> */
    private array $times;

    public function __construct(DateTimeImmutable ...$times)
    {
        if (empty($times)) {
            throw new RuntimeException('At least one time must be provided');
        }

        $this->times = $times;
    }

    public function now(): DateTimeImmutable
    {
        if ($this->index >= count($this->times)) {
            return $this->times[count($this->times) - 1];
        }

        return $this->times[$this->index++];
    }

    public function reset(): void
    {
        $this->index = 0;
    }

    public static function fromStrings(string ...$times): self
    {
        return new self(...array_map(
            fn(string $time) => new DateTimeImmutable($time),
            $times,
        ));
    }
}

// Usage in tests
$clock = SequenceClock::fromStrings(
    '2024-01-01 00:00:00',
    '2024-01-01 00:05:00',
    '2024-01-01 00:10:00',
);

$first = $clock->now();  // 2024-01-01 00:00:00
$second = $clock->now(); // 2024-01-01 00:05:00
$third = $clock->now();  // 2024-01-01 00:10:00
```

## Clock Decorator with Logging

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Clock;

use DateTimeImmutable;
use Psr\Clock\ClockInterface;
use Psr\Log\LoggerInterface;

final readonly class LoggingClock implements ClockInterface
{
    public function __construct(
        private ClockInterface $clock,
        private LoggerInterface $logger,
    ) {
    }

    public function now(): DateTimeImmutable
    {
        $now = $this->clock->now();

        $this->logger->debug('Clock accessed', [
            'time' => $now->format('Y-m-d H:i:s.u'),
            'timezone' => $now->getTimezone()->getName(),
        ]);

        return $now;
    }
}
```

## Business Hours Clock

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Clock;

use DateTimeImmutable;
use Psr\Clock\ClockInterface;

final readonly class BusinessHoursClock implements ClockInterface
{
    public function __construct(
        private ClockInterface $baseClock,
        private int $startHour = 9,
        private int $endHour = 17,
        private array $workDays = [1, 2, 3, 4, 5], // Mon-Fri
    ) {
    }

    public function now(): DateTimeImmutable
    {
        return $this->baseClock->now();
    }

    public function isBusinessHours(): bool
    {
        $now = $this->now();
        $hour = (int) $now->format('G');
        $dayOfWeek = (int) $now->format('N');

        return in_array($dayOfWeek, $this->workDays, true)
            && $hour >= $this->startHour
            && $hour < $this->endHour;
    }

    public function nextBusinessHour(): DateTimeImmutable
    {
        $current = $this->now();

        while (!$this->isBusinessTime($current)) {
            $current = $current->modify('+1 hour')->setTime(
                (int) $current->modify('+1 hour')->format('G'),
                0,
            );
        }

        return $current;
    }

    private function isBusinessTime(DateTimeImmutable $time): bool
    {
        $hour = (int) $time->format('G');
        $dayOfWeek = (int) $time->format('N');

        return in_array($dayOfWeek, $this->workDays, true)
            && $hour >= $this->startHour
            && $hour < $this->endHour;
    }
}
```

## Clock Provider (Service Locator)

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Clock;

use Psr\Clock\ClockInterface;
use RuntimeException;

final class ClockProvider
{
    private static ?ClockInterface $clock = null;

    public static function set(ClockInterface $clock): void
    {
        self::$clock = $clock;
    }

    public static function get(): ClockInterface
    {
        if (self::$clock === null) {
            self::$clock = new SystemClock();
        }

        return self::$clock;
    }

    public static function reset(): void
    {
        self::$clock = null;
    }

    public static function freeze(string $at): void
    {
        self::$clock = FrozenClock::at($at);
    }
}

// Usage in tests
ClockProvider::freeze('2024-01-15 10:30:00');
// ... run tests ...
ClockProvider::reset();
```
