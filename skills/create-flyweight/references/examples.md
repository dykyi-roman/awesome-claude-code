# Flyweight Pattern Examples

## Currency Flyweight (Complete)

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
        'CHF' => 'Fr',
        'CAD' => 'C$',
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

    public function convert(float $amount, CurrencyInterface $targetCurrency): float
    {
        return $amount;
    }
}
```

---

## Icon Flyweight

**File:** `src/Domain/UI/IconFlyweight.php`

```php
<?php

declare(strict_types=1);

namespace Domain\UI;

final readonly class IconFlyweight implements IconInterface
{
    private const ICONS = [
        'home' => '<svg>...</svg>',
        'user' => '<svg>...</svg>',
        'settings' => '<svg>...</svg>',
    ];

    public function __construct(
        private string $name
    ) {}

    public function render(array $attributes): string
    {
        $svg = self::ICONS[$this->name] ?? '';

        $attrs = '';
        foreach ($attributes as $key => $value) {
            $attrs .= " {$key}=\"{$value}\"";
        }

        return str_replace('<svg', "<svg{$attrs}", $svg);
    }

    public function getName(): string
    {
        return $this->name;
    }
}
```

**File:** `src/Domain/UI/Factory/IconFlyweightFactory.php`

```php
<?php

declare(strict_types=1);

namespace Domain\UI\Factory;

use Domain\UI\IconFlyweight;
use Domain\UI\IconInterface;

final class IconFlyweightFactory
{
    private array $flyweights = [];

    public function getIcon(string $name): IconInterface
    {
        if (!isset($this->flyweights[$name])) {
            $this->flyweights[$name] = new IconFlyweight($name);
        }

        return $this->flyweights[$name];
    }

    public function getCount(): int
    {
        return count($this->flyweights);
    }
}
```

---

## Tax Rule Flyweight

**File:** `src/Domain/Tax/TaxRuleFlyweight.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Tax;

final readonly class TaxRuleFlyweight implements TaxRuleInterface
{
    private const RATES = [
        'US-CA' => 0.0725,
        'US-NY' => 0.0400,
        'US-TX' => 0.0625,
        'GB' => 0.20,
        'DE' => 0.19,
    ];

    public function __construct(
        private string $region
    ) {}

    public function calculate(float $amount): float
    {
        $rate = self::RATES[$this->region] ?? 0.0;
        return $amount * $rate;
    }

    public function getRegion(): string
    {
        return $this->region;
    }

    public function getRate(): float
    {
        return self::RATES[$this->region] ?? 0.0;
    }
}
```

**File:** `src/Domain/Tax/Factory/TaxRuleFlyweightFactory.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Tax\Factory;

use Domain\Tax\TaxRuleFlyweight;
use Domain\Tax\TaxRuleInterface;

final class TaxRuleFlyweightFactory
{
    private array $flyweights = [];

    public function getTaxRule(string $region): TaxRuleInterface
    {
        if (!isset($this->flyweights[$region])) {
            $this->flyweights[$region] = new TaxRuleFlyweight($region);
        }

        return $this->flyweights[$region];
    }

    public function getCount(): int
    {
        return count($this->flyweights);
    }
}
```

---

## Unit Tests

### CurrencyFlyweightFactoryTest

**File:** `tests/Unit/Domain/Money/Factory/CurrencyFlyweightFactoryTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\Money\Factory;

use Domain\Money\Factory\CurrencyFlyweightFactory;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(CurrencyFlyweightFactory::class)]
final class CurrencyFlyweightFactoryTest extends TestCase
{
    public function testReturnsSameInstanceForSameCurrency(): void
    {
        $factory = new CurrencyFlyweightFactory();

        $usd1 = $factory->getCurrency('USD');
        $usd2 = $factory->getCurrency('USD');

        self::assertSame($usd1, $usd2);
    }

    public function testCountTracksCreatedFlyweights(): void
    {
        $factory = new CurrencyFlyweightFactory();

        self::assertSame(0, $factory->getCount());

        $factory->getCurrency('USD');
        self::assertSame(1, $factory->getCount());

        $factory->getCurrency('EUR');
        self::assertSame(2, $factory->getCount());

        $factory->getCurrency('USD');
        self::assertSame(2, $factory->getCount());
    }

    public function testCurrencyCodeIsCaseInsensitive(): void
    {
        $factory = new CurrencyFlyweightFactory();

        $usd1 = $factory->getCurrency('usd');
        $usd2 = $factory->getCurrency('USD');

        self::assertSame($usd1, $usd2);
        self::assertSame(1, $factory->getCount());
    }
}
```

---

### IconFlyweightFactoryTest

**File:** `tests/Unit/Domain/UI/Factory/IconFlyweightFactoryTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\UI\Factory;

use Domain\UI\Factory\IconFlyweightFactory;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(IconFlyweightFactory::class)]
final class IconFlyweightFactoryTest extends TestCase
{
    public function testReturnsSameIconInstance(): void
    {
        $factory = new IconFlyweightFactory();

        $home1 = $factory->getIcon('home');
        $home2 = $factory->getIcon('home');

        self::assertSame($home1, $home2);
    }

    public function testDifferentIconsAreDifferentInstances(): void
    {
        $factory = new IconFlyweightFactory();

        $home = $factory->getIcon('home');
        $user = $factory->getIcon('user');

        self::assertNotSame($home, $user);
    }

    public function testMemoryOptimization(): void
    {
        $factory = new IconFlyweightFactory();

        for ($i = 0; $i < 1000; $i++) {
            $factory->getIcon('home');
        }

        self::assertSame(1, $factory->getCount());
    }
}
```

---

### TaxRuleFlyweightTest

**File:** `tests/Unit/Domain/Tax/TaxRuleFlyweightTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\Tax;

use Domain\Tax\TaxRuleFlyweight;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(TaxRuleFlyweight::class)]
final class TaxRuleFlyweightTest extends TestCase
{
    public function testCalculateReturnsTaxAmount(): void
    {
        $taxRule = new TaxRuleFlyweight('US-CA');

        $tax = $taxRule->calculate(100.00);

        self::assertEqualsWithDelta(7.25, $tax, 0.01);
    }

    public function testGetRateReturnsCorrectRate(): void
    {
        $taxRule = new TaxRuleFlyweight('GB');

        $rate = $taxRule->getRate();

        self::assertSame(0.20, $rate);
    }

    public function testUnknownRegionReturnsZeroRate(): void
    {
        $taxRule = new TaxRuleFlyweight('UNKNOWN');

        $rate = $taxRule->getRate();
        $tax = $taxRule->calculate(100.00);

        self::assertSame(0.0, $rate);
        self::assertSame(0.0, $tax);
    }
}
```
