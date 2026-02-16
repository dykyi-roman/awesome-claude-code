# Flyweight Pattern Templates

## Flyweight Interface

**File:** `src/Domain/{BoundedContext}/{Name}Interface.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext};

interface {Name}Interface
{
    public function {operation}(string $extrinsicState): {returnType};
}
```

---

## ConcreteFlyweight

**File:** `src/Domain/{BoundedContext}/{Name}Flyweight.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext};

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

**File:** `src/Domain/{BoundedContext}/Factory/{Name}FlyweightFactory.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext}\Factory;

use Domain\{BoundedContext}\{Name}Flyweight;
use Domain\{BoundedContext}\{Name}Interface;

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

**File:** `src/Domain/Money/CurrencyInterface.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Money;

interface CurrencyInterface
{
    public function format(float $amount): string;

    public function getCode(): string;

    public function getSymbol(): string;
}
```

**File:** `src/Domain/Money/CurrencyFlyweight.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Money;

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

**File:** `src/Domain/Money/Factory/CurrencyFlyweightFactory.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Money\Factory;

use Domain\Money\CurrencyFlyweight;
use Domain\Money\CurrencyInterface;

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
