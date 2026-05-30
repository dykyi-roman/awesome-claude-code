# Flyweight Pattern Templates

## Flyweight Interface

**File:** `src/{architecture-path}/{Name}Interface.php`

```php
<?php

declare(strict_types=1);

namespace {BoundedContext};

interface {Name}Interface
{
    public function {operation}(string $extrinsicState): {returnType};
}
```

---

## ConcreteFlyweight

**File:** `src/{architecture-path}/{Name}Flyweight.php`

```php
<?php

declare(strict_types=1);

namespace {BoundedContext};

final readonly class {Name}Flyweight implements {Name}Interface
{
    public function __construct(
        private string $intrinsicState
    ) {}

    public function {operation}(string $extrinsicState): {returnType}
    {
        return {combineIntrinsicAndExtrinsic};
    }

    public function getIntrinsicState(): string
    {
        return $this->intrinsicState;
    }
}
```

---

## FlyweightFactory

**File:** `src/{architecture-path}/Factory/{Name}FlyweightFactory.php`

```php
<?php

declare(strict_types=1);

namespace Factory;

use {BoundedContext}\4;
use {BoundedContext}\4;

final class {Name}FlyweightFactory
{
    private array $flyweights = [];

    public function getFlyweight(string $key): {Name}Interface
    {
        if (!isset($this->flyweights[$key])) {
            $this->flyweights[$key] = new {Name}Flyweight($key);
        }

        return $this->flyweights[$key];
    }

    public function getCount(): int
    {
        return count($this->flyweights);
    }

    public function clear(): void
    {
        $this->flyweights = [];
    }
}
```

---

## Currency Flyweight Example

**File:** `src/{architecture-path}/CurrencyInterface.php`

```php
<?php

declare(strict_types=1);

namespace Money;

interface CurrencyInterface
{
    public function format(float $amount): string;

    public function getCode(): string;

    public function getSymbol(): string;
}
```

**File:** `src/{architecture-path}/CurrencyFlyweight.php`

```php
<?php

declare(strict_types=1);

namespace Money;

final readonly class CurrencyFlyweight implements CurrencyInterface
{
    private const SYMBOLS = [
        'USD' => '$',
        'EUR' => '€',
        'GBP' => '£',
        'JPY' => '¥',
    ];

    public function __construct(
        private string $code
    ) {}

    public function format(float $amount): string
    {
        return $this->getSymbol() . number_format($amount, 2);
    }

    public function getCode(): string
    {
        return $this->code;
    }

    public function getSymbol(): string
    {
        return self::SYMBOLS[$this->code] ?? $this->code;
    }
}
```

**File:** `src/{architecture-path}/Factory/CurrencyFlyweightFactory.php`

```php
<?php

declare(strict_types=1);

namespace Factory;

use Money\4;
use Money\4;

final class CurrencyFlyweightFactory
{
    private array $flyweights = [];

    public function getCurrency(string $code): CurrencyInterface
    {
        $code = strtoupper($code);

        if (!isset($this->flyweights[$code])) {
            $this->flyweights[$code] = new CurrencyFlyweight($code);
        }

        return $this->flyweights[$code];
    }

    public function getCount(): int
    {
        return count($this->flyweights);
    }
}
```
