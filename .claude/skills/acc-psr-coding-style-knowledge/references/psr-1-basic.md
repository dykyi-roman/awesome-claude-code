# PSR-1: Basic Coding Standard

## Overview

PSR-1 is the basic coding standard that all PHP code MUST follow to ensure a high level of technical interoperability between shared PHP code.

## 1. Files

### 1.1 PHP Tags

PHP code MUST use the long `<?php ?>` tags or the short-echo `<?= ?>` tags.

```php
// CORRECT
<?php
// PHP code here

// CORRECT (short echo)
<?= $variable ?>

// INCORRECT - short tags
<? echo $variable; ?>
```

### 1.2 Character Encoding

PHP code MUST use only UTF-8 without BOM for PHP code.

```bash
# Check for BOM in files
file --mime-encoding src/*.php

# Remove BOM if present
sed -i '1s/^\xEF\xBB\xBF//' file.php
```

### 1.3 Side Effects

A file SHOULD declare new symbols (classes, functions, constants, etc.) and cause no side effects, OR it SHOULD execute logic with side effects, but SHOULD NOT do both.

**Side effects include:**
- Generating output
- Explicit use of `require` or `include`
- Connecting to external services
- Modifying ini settings
- Emitting errors or exceptions
- Modifying global or static variables
- Reading from or writing to a file

```php
// BAD: Declaration AND side effects
<?php
ini_set('error_reporting', E_ALL);  // Side effect

function foo(): void                 // Declaration
{
    // function body
}

echo 'Hello';                        // Side effect
```

```php
// GOOD: Side effects only (bootstrap file)
<?php
// bootstrap.php
ini_set('error_reporting', E_ALL);
require __DIR__ . '/vendor/autoload.php';
```

```php
// GOOD: Declarations only (class file)
<?php
// Foo.php
declare(strict_types=1);

namespace App;

final readonly class Foo
{
    public function bar(): string
    {
        return 'baz';
    }
}
```

## 2. Namespace and Class Names

### 2.1 Namespaces

Namespaces and classes MUST follow an "autoloading" PSR: [PSR-4].

```php
<?php

declare(strict_types=1);

namespace Vendor\Package\SubNamespace;

final readonly class ClassName
{
}
```

### 2.2 Class Names

Class names MUST be declared in `StudlyCaps` (PascalCase).

```php
// CORRECT
class UserRepository { }
class HttpClientFactory { }
class OAuth2Provider { }

// INCORRECT
class user_repository { }    // snake_case
class userRepository { }     // camelCase
class Userrepository { }     // Not StudlyCaps
```

## 3. Class Constants, Properties, and Methods

### 3.1 Constants

Class constants MUST be declared in all upper case with underscore separators.

```php
<?php

declare(strict_types=1);

namespace App\Domain;

final readonly class Db
{
    public const FETCH_ASSOC = 1;
    public const FETCH_NUM = 2;
    public const FETCH_OBJ = 3;
    public const DEFAULT_TIMEOUT_SECONDS = 30;
    public const MAX_RETRY_ATTEMPTS = 3;
}
```

### 3.2 Properties

This guide intentionally avoids any recommendation regarding the use of `$StudlyCaps`, `$camelCase`, or `$under_score` property names.

**Recommendation:** Use `camelCase` for consistency with method naming.

```php
<?php

declare(strict_types=1);

namespace App\Domain\Entity;

final readonly class User
{
    public function __construct(
        private string $firstName,    // camelCase recommended
        private string $lastName,
        private string $emailAddress,
    ) {
    }
}
```

### 3.3 Methods

Method names MUST be declared in `camelCase`.

```php
<?php

declare(strict_types=1);

namespace App\Domain\Entity;

final readonly class User
{
    // CORRECT
    public function getFullName(): string { }
    public function hasActiveSubscription(): bool { }
    public function sendWelcomeEmail(): void { }

    // INCORRECT
    public function GetFullName(): string { }     // PascalCase
    public function get_full_name(): string { }   // snake_case
    public function GETFULLNAME(): string { }     // UPPERCASE
}
```

## Detection Patterns

### Find Side Effects in Class Files

```bash
# Echo/print statements
grep -rn "^\s*echo\|^\s*print" --include="*.php" src/

# Header modifications
grep -rn "^\s*header\s*(" --include="*.php" src/

# Session operations
grep -rn "^\s*session_start\|^\s*session_" --include="*.php" src/

# ini_set calls
grep -rn "^\s*ini_set" --include="*.php" src/

# Direct output buffering
grep -rn "^\s*ob_start\|^\s*ob_end" --include="*.php" src/
```

### Find Invalid Class Names

```bash
# Lowercase start
grep -rn "^class [a-z]" --include="*.php" src/

# Contains underscore
grep -rn "^class [A-Za-z]*_" --include="*.php" src/

# All caps
grep -rn "^class [A-Z][A-Z]" --include="*.php" src/
```

### Find Invalid Method Names

```bash
# Starts with uppercase
grep -rn "function [A-Z][a-zA-Z]*\s*(" --include="*.php" src/

# Contains underscore (excluding magic methods)
grep -rn "function [a-z]*_[a-z]" --include="*.php" src/ | grep -v "__"
```

## Compliance Checklist

| Requirement | Check |
|-------------|-------|
| Uses `<?php` or `<?=` tags only | `grep -r "<?[^p=]" src/` |
| UTF-8 without BOM | `file --mime-encoding src/*.php` |
| No side effects in class files | Manual review or static analysis |
| StudlyCaps class names | `grep -rn "^class [a-z]" src/` |
| UPPER_CASE constants | Manual review |
| camelCase methods | `grep -rn "function [A-Z]" src/` |

## PHP-CS-Fixer Rules

```php
<?php

return [
    // PSR-1 rules
    'encoding' => true,
    'full_opening_tag' => true,
    'class_definition' => [
        'single_line' => false,
    ],
];
```

## PHP_CodeSniffer Rules

```xml
<rule ref="PSR1"/>
<rule ref="PSR1.Files.SideEffects"/>
<rule ref="PSR1.Classes.ClassDeclaration"/>
<rule ref="PSR1.Methods.CamelCapsMethodName"/>
```
