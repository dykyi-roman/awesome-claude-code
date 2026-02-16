# PSR-12: Extended Coding Style

## Overview

PSR-12 extends, expands and replaces PSR-2. It requires adherence to PSR-1 and includes additional formatting rules.

## 1. General

### 1.1 Basic Requirements

| Rule | Requirement |
|------|-------------|
| PSR-1 | Code MUST follow PSR-1 |
| File Length | Files SHOULD be ≤1000 lines |
| Line Length | Lines SHOULD be ≤120 characters |
| Blank Lines | MAY be added for readability |

### 1.2 Indentation

Code MUST use 4 spaces for indenting, not tabs.

```php
<?php

declare(strict_types=1);

namespace App\Domain;

final readonly class Example
{
    public function method(): void
    {
        if ($condition) {
            // 4 spaces indentation
            doSomething();
        }
    }
}
```

### 1.3 Keywords and Types

All PHP reserved keywords and types MUST be in lower case.

```php
// CORRECT
$value = true;
$nothing = null;
$enabled = false;
function process(int $id, string $name, bool $active): ?array { }

// INCORRECT
$value = TRUE;
$nothing = NULL;
$enabled = FALSE;
function process(Int $id, String $name, Bool $active): ?Array { }
```

Short form of type keywords MUST be used.

```php
// CORRECT
function process(int $id, bool $active): void { }

// INCORRECT
function process(integer $id, boolean $active): void { }
```

## 2. Files

### 2.1 File Structure

```php
<?php                                    // 1. Opening tag

declare(strict_types=1);                 // 2. declare statements (blank line before/after)

namespace Vendor\Package;                // 3. Namespace (blank line after)

use Vendor\Package\ClassA;               // 4. use imports (blank line after all imports)
use Vendor\Package\ClassB;
use function Vendor\Package\functionA;
use const Vendor\Package\CONST_A;

/**                                      // 5. Optional docblock
 * Class documentation.
 */
final readonly class ClassName           // 6. Class declaration
{
    // class body
}
                                         // 7. Single blank line at end of file
```

### 2.2 Import Statements

Import statements MUST be grouped by type and ordered alphabetically:

```php
<?php

declare(strict_types=1);

namespace App\Application\User;

// 1. Class imports (alphabetically)
use App\Domain\User\Entity\User;
use App\Domain\User\Repository\UserRepositoryInterface;
use App\Domain\User\ValueObject\Email;

// 2. Function imports (alphabetically)
use function array_filter;
use function array_map;

// 3. Constant imports (alphabetically)
use const PHP_EOL;
use const PHP_VERSION;
```

### 2.3 Compound Namespaces

Compound namespaces SHOULD NOT have more than two sub-namespaces:

```php
// CORRECT
use App\Domain\User\{Entity, Repository, ValueObject};

// AVOID - too deep
use App\Domain\User\Entity\{User, Admin, Guest};
```

## 3. Classes, Properties, and Methods

### 3.1 Extends and Implements

```php
<?php

declare(strict_types=1);

namespace App\Domain;

// Single line when short
final readonly class ClassName extends ParentClass implements InterfaceA
{
}

// Multi-line when long
final readonly class ClassName extends ParentClass implements
    InterfaceA,
    InterfaceB,
    InterfaceC
{
    // class body
}
```

### 3.2 Using Traits

```php
<?php

declare(strict_types=1);

namespace App\Domain;

final class ClassName
{
    use FirstTrait;
    use SecondTrait;
    use ThirdTrait {
        ThirdTrait::method insteadof SecondTrait;
        ThirdTrait::anotherMethod as private;
    }
}
```

### 3.3 Properties

```php
<?php

declare(strict_types=1);

namespace App\Domain;

final class Example
{
    // Visibility MUST be declared
    public string $public = 'value';
    protected string $protected = 'value';
    private string $private = 'value';

    // Type declarations
    private int $count;
    private ?string $name = null;
    private array $items = [];

    // Readonly properties (PHP 8.1+)
    public readonly string $immutable;

    // INCORRECT - missing visibility
    // string $invalid;
}
```

### 3.4 Methods

```php
<?php

declare(strict_types=1);

namespace App\Domain;

final readonly class Example
{
    // Standard method signature
    public function methodName(int $arg1, ?string $arg2 = null): bool
    {
        return true;
    }

    // Long argument list
    public function longMethodName(
        int $argument1,
        string $argument2,
        bool $argument3,
        ?array $argument4 = null,
    ): bool {
        return true;
    }

    // Abstract methods
    abstract protected function abstractMethod(): void;

    // Final methods
    final public function finalMethod(): void
    {
    }
}
```

### 3.5 Method and Function Arguments

```php
<?php

// Standard call
$foo->bar($arg1, $arg2, $arg3);

// Multi-line call
$foo->bar(
    $longArgument1,
    $longArgument2,
    $longArgument3,
);

// Mixed
$foo->bar(
    $firstArgument,
    $foo->bar(
        $nestedArgument,
    ),
    $lastArgument,
);
```

## 4. Control Structures

### 4.1 General Rules

- One space after control structure keyword
- NO space after opening parenthesis
- NO space before closing parenthesis
- One space between closing parenthesis and opening brace
- Structure body MUST be indented once
- Closing brace MUST be on the next line after the body

### 4.2 if, elseif, else

```php
<?php

if ($expr1) {
    // if body
} elseif ($expr2) {
    // elseif body
} else {
    // else body
}

// Long conditions
if (
    $expr1
    && $expr2
    && $expr3
) {
    // body
}
```

### 4.3 switch, case

```php
<?php

switch ($expr) {
    case 0:
        echo 'First case, with a break';
        break;
    case 1:
        echo 'Second case, which falls through';
        // no break - intentional fall-through
    case 2:
    case 3:
    case 4:
        echo 'Third case, return instead of break';
        return;
    default:
        echo 'Default case';
        break;
}
```

### 4.4 match (PHP 8.0+)

```php
<?php

$result = match ($expr) {
    0 => 'First',
    1, 2 => 'Second or third',
    default => 'Other',
};

// Multi-line conditions
$result = match (true) {
    $value < 0 => 'Negative',
    $value === 0 => 'Zero',
    $value > 0 => 'Positive',
};
```

### 4.5 while, do while

```php
<?php

while ($expr) {
    // body
}

do {
    // body
} while ($expr);
```

### 4.6 for, foreach

```php
<?php

for ($i = 0; $i < 10; $i++) {
    // body
}

foreach ($iterable as $key => $value) {
    // body
}
```

### 4.7 try, catch, finally

```php
<?php

try {
    // try body
} catch (FirstThrowableType $e) {
    // catch body
} catch (OtherThrowableType | AnotherThrowableType $e) {
    // multi-catch body
} finally {
    // finally body
}
```

## 5. Operators

### 5.1 Unary Operators

No space between operator and operand:

```php
<?php

$i++;
++$j;
$value = -$number;
$negated = !$bool;
```

### 5.2 Binary Operators

One space on each side:

```php
<?php

// Arithmetic
$sum = $a + $b;
$diff = $a - $b;
$product = $a * $b;

// Comparison
$equal = $a === $b;
$less = $a < $b;

// Logical
$and = $a && $b;
$or = $a || $b;

// Assignment
$value = 1;
$value += 1;

// String
$full = $first . ' ' . $last;

// Null coalescing
$value = $a ?? $b;
$value ??= $default;
```

### 5.3 Ternary Operators

```php
<?php

// Short form
$result = $condition ? $valueIfTrue : $valueIfFalse;

// Multi-line
$result = $veryLongCondition
    ? $veryLongValueIfTrue
    : $veryLongValueIfFalse;
```

## 6. Closures

```php
<?php

// Standard closure
$closure = function (int $arg1, int $arg2): int {
    return $arg1 + $arg2;
};

// With use
$closure = function (int $arg) use ($var1, &$var2): int {
    return $arg + $var1 + $var2;
};

// Long signature
$closure = function (
    int $argument1,
    string $argument2,
) use (
    $var1,
    $var2,
): bool {
    return true;
};

// Arrow function (PHP 7.4+)
$fn = fn(int $a, int $b): int => $a + $b;
```

## 7. Anonymous Classes

```php
<?php

// Simple
$instance = new class {
    public function method(): void
    {
    }
};

// With inheritance
$instance = new class extends SomeClass implements SomeInterface {
    use SomeTrait;

    private int $value;

    public function method(): void
    {
    }
};

// As argument
$foo->bar(new class implements SomeInterface {
    public function method(): void
    {
    }
});
```

## PHP-CS-Fixer Full Configuration

```php
<?php

declare(strict_types=1);

use PhpCsFixer\Config;
use PhpCsFixer\Finder;

$finder = Finder::create()
    ->in([__DIR__ . '/src', __DIR__ . '/tests'])
    ->name('*.php');

return (new Config())
    ->setRiskyAllowed(true)
    ->setRules([
        '@PSR12' => true,
        '@PSR12:risky' => true,
        'array_syntax' => ['syntax' => 'short'],
        'binary_operator_spaces' => true,
        'blank_line_before_statement' => [
            'statements' => ['return', 'throw', 'try'],
        ],
        'cast_spaces' => ['space' => 'none'],
        'class_attributes_separation' => [
            'elements' => ['method' => 'one'],
        ],
        'concat_space' => ['spacing' => 'one'],
        'declare_strict_types' => true,
        'final_class' => true,
        'no_unused_imports' => true,
        'ordered_imports' => [
            'sort_algorithm' => 'alpha',
            'imports_order' => ['class', 'function', 'const'],
        ],
        'single_quote' => true,
        'trailing_comma_in_multiline' => [
            'elements' => ['arguments', 'arrays', 'parameters'],
        ],
    ])
    ->setFinder($finder);
```
