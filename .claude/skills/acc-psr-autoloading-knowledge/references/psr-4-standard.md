# PSR-4: Autoloader Standard

## Overview

PSR-4 describes a specification for autoloading classes from file paths. It is fully interoperable with any other autoloading specification, including PSR-0.

## Specification

### 1. Terminology

**Class** refers to classes, interfaces, traits, and other similar structures.

**Fully Qualified Class Name (FQCN)** has the following form:

```
\<NamespaceName>(\<SubNamespaceNames>)*\<ClassName>
```

1. The FQCN MUST have a top-level namespace name ("vendor namespace")
2. The FQCN MAY have one or more sub-namespace names
3. The FQCN MUST have a terminating class name
4. Underscores have no special meaning
5. Alphabetic characters MAY be any combination of case
6. All class names MUST be referenced case-sensitively

### 2. Autoloading

When loading a file that corresponds to a FQCN:

1. A contiguous series of one or more leading namespace and sub-namespace names (not including the leading namespace separator) in the FQCN ("namespace prefix") corresponds to at least one "base directory"

2. The contiguous sub-namespace names after the "namespace prefix" correspond to a subdirectory within a "base directory", in which the namespace separators represent directory separators

3. The terminating class name corresponds to a file name ending in `.php`. The file name MUST match the case of the terminating class name

### 3. Examples

| FQCN | Namespace Prefix | Base Directory | Resulting File Path |
|------|------------------|----------------|---------------------|
| `\Acme\Log\Writer\File_Writer` | `Acme\Log\Writer` | `./acme-log-writer/lib/` | `./acme-log-writer/lib/File_Writer.php` |
| `\Aura\Web\Response\Status` | `Aura\Web` | `/path/to/aura-web/src/` | `/path/to/aura-web/src/Response/Status.php` |
| `\Symfony\Core\Request` | `Symfony\Core` | `./vendor/Symfony/Core/` | `./vendor/Symfony/Core/Request.php` |
| `\Zend\Acl` | `Zend` | `/usr/includes/Zend/` | `/usr/includes/Zend/Acl.php` |

## Implementation

### Simple Autoloader

```php
<?php

declare(strict_types=1);

spl_autoload_register(function (string $class): void {
    // Namespace prefix => Base directory
    $prefixes = [
        'App\\' => __DIR__ . '/src/',
        'App\\Tests\\' => __DIR__ . '/tests/',
    ];

    foreach ($prefixes as $prefix => $baseDir) {
        $len = strlen($prefix);

        if (strncmp($prefix, $class, $len) !== 0) {
            continue;
        }

        $relativeClass = substr($class, $len);
        $file = $baseDir . str_replace('\\', '/', $relativeClass) . '.php';

        if (file_exists($file)) {
            require $file;
            return;
        }
    }
});
```

### Composer Autoloader

Composer generates an optimized PSR-4 autoloader automatically:

```json
{
    "autoload": {
        "psr-4": {
            "App\\": "src/"
        }
    }
}
```

After running `composer dump-autoload`, the autoloader is available at:

```php
<?php

require __DIR__ . '/vendor/autoload.php';
```

## Rules Summary

| Rule | Description |
|------|-------------|
| Case Sensitivity | Class name case MUST match file name case |
| Extension | File MUST end with `.php` |
| Directory Separator | Namespace separator `\` maps to directory separator `/` |
| Underscores | Have no special meaning (unlike PSR-0) |
| Trailing Slash | Namespace prefix SHOULD end with `\` |

## Differences from PSR-0

| Feature | PSR-0 | PSR-4 |
|---------|-------|-------|
| Underscores | Converted to directory separators | No special meaning |
| PEAR-style | Supported | Not supported |
| Directory Structure | Must mirror full namespace | Can map any prefix to any directory |
| Status | Deprecated | Current standard |

### Migration Example

```php
// PSR-0: Underscores become directories
// Class: Vendor_Package_ClassName
// File: Vendor/Package/ClassName.php

// PSR-4: Underscores are literal
// Class: Vendor\Package\Class_Name
// File: Class_Name.php (relative to base directory)
```

## Best Practices

### 1. Use Meaningful Namespace Prefixes

```php
// GOOD: Clear vendor and package identification
namespace Acme\Blog\Entity;
namespace MyCompany\SharedKernel\ValueObject;

// AVOID: Generic or unclear prefixes
namespace App\Stuff;
namespace Code\Things;
```

### 2. Match Namespace Depth to Directory Depth

```php
// Namespace: App\Domain\User\Entity
// Directory: src/Domain/User/Entity/
// File:      User.php

// The directory structure should mirror the namespace structure
```

### 3. One Class Per File

```php
// GOOD: One class per file
// File: src/Domain/User/Entity/User.php
namespace App\Domain\User\Entity;

final readonly class User { }

// AVOID: Multiple classes in one file
// This breaks PSR-4 autoloading
```

### 4. Class Name Matches Filename

```php
// File: EmailAddress.php
// GOOD
final readonly class EmailAddress { }

// BAD
final readonly class Email { }  // Name doesn't match file
```

## Testing Autoload Configuration

```php
<?php

// Test script to verify PSR-4 autoloading
declare(strict_types=1);

require __DIR__ . '/vendor/autoload.php';

$classesToTest = [
    \App\Domain\User\Entity\User::class,
    \App\Domain\User\ValueObject\Email::class,
    \App\Application\User\Command\CreateUserCommand::class,
];

foreach ($classesToTest as $class) {
    if (class_exists($class) || interface_exists($class) || trait_exists($class)) {
        echo "✓ {$class}\n";
    } else {
        echo "✗ {$class} - NOT FOUND\n";
    }
}
```
