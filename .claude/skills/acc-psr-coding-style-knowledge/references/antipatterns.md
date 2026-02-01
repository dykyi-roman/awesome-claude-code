# PSR-1/PSR-12 Antipatterns

## Overview

This document catalogs common PSR coding style violations with examples and fixes.

## PSR-1 Antipatterns

### 1. Mixed Declarations and Side Effects

**Severity:** CRITICAL

```php
// BAD: Mixing declarations with side effects
<?php
namespace App\Domain;

error_reporting(E_ALL);           // Side effect
ini_set('display_errors', '1');   // Side effect

class Logger                       // Declaration
{
    public function log(string $message): void
    {
        echo $message;
    }
}

session_start();                   // Side effect
```

```php
// GOOD: Separate files
// bootstrap.php
<?php
error_reporting(E_ALL);
ini_set('display_errors', '1');
session_start();

// Logger.php
<?php
declare(strict_types=1);

namespace App\Domain;

final readonly class Logger
{
    public function __construct(
        private LogWriterInterface $writer,
    ) {
    }

    public function log(string $message): void
    {
        $this->writer->write($message);
    }
}
```

### 2. Non-StudlyCaps Class Names

**Severity:** CRITICAL

```php
// BAD: Various incorrect naming styles
class user_repository { }         // snake_case
class userRepository { }          // camelCase
class USERREPOSITORY { }          // UPPERCASE
class User_Repository { }         // Mixed with underscore
```

```php
// GOOD: StudlyCaps (PascalCase)
final readonly class UserRepository { }
final readonly class HttpClientFactory { }
final readonly class OAuth2TokenProvider { }
final readonly class XMLParser { }
```

### 3. Non-camelCase Method Names

**Severity:** CRITICAL

```php
// BAD: Incorrect method naming
final readonly class UserService
{
    public function Get_User(): User { }        // Snake_Case
    public function GetUser(): User { }         // PascalCase
    public function get_user(): User { }        // snake_case
    public function GETUSER(): User { }         // UPPERCASE
}
```

```php
// GOOD: camelCase
final readonly class UserService
{
    public function getUser(): User { }
    public function findByEmail(): ?User { }
    public function hasActiveSubscription(): bool { }
    public function isEmailVerified(): bool { }
}
```

### 4. Incorrect Constant Naming

**Severity:** WARNING

```php
// BAD: Incorrect constant naming
final readonly class HttpStatus
{
    public const ok = 200;                    // lowercase
    public const NotFound = 404;              // PascalCase
    public const internalServerError = 500;   // camelCase
}
```

```php
// GOOD: UPPER_CASE_WITH_UNDERSCORES
final readonly class HttpStatus
{
    public const OK = 200;
    public const NOT_FOUND = 404;
    public const INTERNAL_SERVER_ERROR = 500;
    public const TOO_MANY_REQUESTS = 429;
}
```

## PSR-12 Antipatterns

### 5. Tab Indentation

**Severity:** WARNING

```php
// BAD: Using tabs
final readonly class Example
{
→   public function method(): void
→   {
→   →   if ($condition) {
→   →   →   doSomething();
→   →   }
→   }
}
```

```php
// GOOD: Using 4 spaces
final readonly class Example
{
    public function method(): void
    {
        if ($condition) {
            doSomething();
        }
    }
}
```

### 6. Incorrect Keyword Case

**Severity:** WARNING

```php
// BAD: Uppercase keywords and long type names
final readonly class Example
{
    private Boolean $active = TRUE;
    private Integer $count = 0;
    private ?String $name = NULL;

    public function process(Array $items): Void
    {
        foreach ($items AS $item) {
            IF ($item === NULL) {
                CONTINUE;
            }
        }
    }
}
```

```php
// GOOD: Lowercase keywords and short type names
final readonly class Example
{
    private bool $active = true;
    private int $count = 0;
    private ?string $name = null;

    public function process(array $items): void
    {
        foreach ($items as $item) {
            if ($item === null) {
                continue;
            }
        }
    }
}
```

### 7. Incorrect Brace Placement

**Severity:** WARNING

```php
// BAD: Inconsistent brace placement
final readonly class Example {              // Brace on same line
    public function method(): void
    {
        if ($condition)
        {                                   // Brace on new line
            doSomething();
        }
        else                                // else on new line
        {
            doOther();
        }
    }
}
```

```php
// GOOD: Consistent PSR-12 brace placement
final readonly class Example
{
    public function method(): void
    {
        if ($condition) {
            doSomething();
        } else {
            doOther();
        }
    }
}
```

### 8. Missing Spaces in Control Structures

**Severity:** INFO

```php
// BAD: Missing/extra spaces
final readonly class Example
{
    public function method(): void
    {
        if($condition){                     // No space after if, no space before {
            for($i=0;$i<10;$i++){           // No spaces
                switch($value){             // No space after switch
                    case 1:break;           // No space after case value
                }
            }
        }
    }
}
```

```php
// GOOD: Proper spacing
final readonly class Example
{
    public function method(): void
    {
        if ($condition) {
            for ($i = 0; $i < 10; $i++) {
                switch ($value) {
                    case 1:
                        break;
                }
            }
        }
    }
}
```

### 9. Incorrect Import Statements

**Severity:** INFO

```php
// BAD: Unorganized imports
<?php

namespace App\Domain;

use App\Infrastructure\Repository\UserRepository;
use function array_map;
use App\Domain\ValueObject\Email;
use const PHP_EOL;
use App\Domain\Entity\User;
use function array_filter;

class Service { }
```

```php
// GOOD: Organized imports (class, function, const) alphabetically
<?php

declare(strict_types=1);

namespace App\Domain;

use App\Domain\Entity\User;
use App\Domain\ValueObject\Email;
use App\Infrastructure\Repository\UserRepository;

use function array_filter;
use function array_map;

use const PHP_EOL;

final readonly class Service { }
```

### 10. Trailing Whitespace

**Severity:** INFO

```php
// BAD: Trailing whitespace (shown as ·)
final readonly class Example·
{··
    public function method(): void····
    {·
        $value = 'test';··
    }··
}···
```

```php
// GOOD: No trailing whitespace
final readonly class Example
{
    public function method(): void
    {
        $value = 'test';
    }
}
```

### 11. Incorrect Operator Spacing

**Severity:** INFO

```php
// BAD: Inconsistent operator spacing
final readonly class Example
{
    public function calculate(int $a, int $b): int
    {
        $sum=$a+$b;                         // No spaces
        $diff = $a-$b;                      // Inconsistent
        $result=$sum*$diff/2;               // No spaces
        return$result;                      // No space after return
    }
}
```

```php
// GOOD: Consistent operator spacing
final readonly class Example
{
    public function calculate(int $a, int $b): int
    {
        $sum = $a + $b;
        $diff = $a - $b;
        $result = $sum * $diff / 2;

        return $result;
    }
}
```

### 12. Incorrect Closure Formatting

**Severity:** INFO

```php
// BAD: Incorrect closure formatting
$closure = function($arg1,$arg2)use($var1,$var2){
    return $arg1+$arg2+$var1+$var2;
};

$arrow = fn($a,$b)=>$a+$b;
```

```php
// GOOD: Proper closure formatting
$closure = function (int $arg1, int $arg2) use ($var1, $var2): int {
    return $arg1 + $arg2 + $var1 + $var2;
};

$arrow = fn(int $a, int $b): int => $a + $b;
```

## Summary Table

| # | Antipattern | PSR | Severity | Auto-fixable |
|---|-------------|-----|----------|--------------|
| 1 | Mixed declarations/side effects | PSR-1 | CRITICAL | No |
| 2 | Non-StudlyCaps class names | PSR-1 | CRITICAL | Yes |
| 3 | Non-camelCase method names | PSR-1 | CRITICAL | Yes |
| 4 | Incorrect constant naming | PSR-1 | WARNING | Yes |
| 5 | Tab indentation | PSR-12 | WARNING | Yes |
| 6 | Incorrect keyword case | PSR-12 | WARNING | Yes |
| 7 | Incorrect brace placement | PSR-12 | WARNING | Yes |
| 8 | Missing control structure spaces | PSR-12 | INFO | Yes |
| 9 | Unorganized imports | PSR-12 | INFO | Yes |
| 10 | Trailing whitespace | PSR-12 | INFO | Yes |
| 11 | Incorrect operator spacing | PSR-12 | INFO | Yes |
| 12 | Incorrect closure formatting | PSR-12 | INFO | Yes |

## Auto-Fix Commands

```bash
# PHP-CS-Fixer
php-cs-fixer fix src/ --rules=@PSR12

# PHP_CodeSniffer with phpcbf
phpcbf --standard=PSR12 src/

# Specific fixes
php-cs-fixer fix src/ --rules=class_definition
php-cs-fixer fix src/ --rules=no_trailing_whitespace
php-cs-fixer fix src/ --rules=ordered_imports
```
