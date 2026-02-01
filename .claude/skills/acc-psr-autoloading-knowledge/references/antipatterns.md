# PSR-4 Autoloading Antipatterns

## Overview

Common PSR-4 autoloading mistakes and how to fix them.

## 1. Namespace-Path Mismatch

**Severity:** CRITICAL

```php
// File: src/Domain/User/Entity/User.php

// BAD: Namespace doesn't match path
<?php

namespace App\User\Entity;  // Missing "Domain"

final readonly class User { }
```

```php
// GOOD: Namespace matches path
<?php

declare(strict_types=1);

namespace App\Domain\User\Entity;

final readonly class User { }
```

**Detection:**
```bash
# Find files where namespace doesn't match path
for f in $(find src -name "*.php"); do
    ns=$(grep -m1 "^namespace" "$f" | sed 's/namespace //;s/;//')
    path_ns="App\\$(dirname ${f#src/} | tr '/' '\\')"
    [ "$ns" != "$path_ns" ] && echo "Mismatch: $f ($ns vs $path_ns)"
done
```

## 2. Class Name vs Filename Mismatch

**Severity:** CRITICAL

```php
// File: src/Domain/User/Entity/UserEntity.php

// BAD: Class name doesn't match filename
<?php

namespace App\Domain\User\Entity;

final readonly class User { }  // Should be UserEntity
```

```php
// GOOD: Class name matches filename
<?php

declare(strict_types=1);

namespace App\Domain\User\Entity;

final readonly class UserEntity { }

// OR rename file to User.php
```

**Detection:**
```bash
# Find class/filename mismatches
for f in $(find src -name "*.php"); do
    filename=$(basename "$f" .php)
    if ! grep -q "^\(class\|interface\|trait\|enum\) $filename" "$f"; then
        echo "Mismatch: $f (expected class $filename)"
    fi
done
```

## 3. Case Sensitivity Issues

**Severity:** CRITICAL (on Linux/Unix)

```php
// File: src/Domain/user/Entity/User.php  (lowercase 'user')

// BAD: Directory case doesn't match namespace
<?php

namespace App\Domain\User\Entity;  // PascalCase 'User'

final readonly class User { }
```

**Fix:** Rename directory to match namespace case.

```bash
# Rename directory
mv src/Domain/user src/Domain/User
```

**Detection:**
```bash
# Find case mismatches (on case-insensitive systems)
find src -type d | while read dir; do
    expected=$(echo "$dir" | sed 's/src/App/' | tr '/' '\\')
    # Compare with grep from files in that directory
done
```

## 4. Missing Trailing Backslash in composer.json

**Severity:** CRITICAL

```json
// BAD: Missing trailing backslash
{
    "autoload": {
        "psr-4": {
            "App": "src/"
        }
    }
}
```

```json
// GOOD: Include trailing backslash
{
    "autoload": {
        "psr-4": {
            "App\\": "src/"
        }
    }
}
```

**Detection:**
```bash
# Check composer.json for missing backslashes
grep -o '"[^"]*":' composer.json | grep -v '\\\\'
```

## 5. Incorrect Path Separator

**Severity:** WARNING

```json
// BAD: Backslash in path (Windows-only)
{
    "autoload": {
        "psr-4": {
            "App\\": "src\\"
        }
    }
}
```

```json
// GOOD: Forward slash (cross-platform)
{
    "autoload": {
        "psr-4": {
            "App\\": "src/"
        }
    }
}
```

## 6. Multiple Classes in One File

**Severity:** CRITICAL

```php
// File: src/Domain/User/User.php

// BAD: Multiple classes in one file
<?php

namespace App\Domain\User;

final readonly class User { }

final readonly class UserFactory { }  // Should be in separate file

class UserBuilder { }  // Should be in separate file
```

```php
// GOOD: One class per file

// File: src/Domain/User/User.php
<?php
namespace App\Domain\User;
final readonly class User { }

// File: src/Domain/User/UserFactory.php
<?php
namespace App\Domain\User;
final readonly class UserFactory { }

// File: src/Domain/User/UserBuilder.php
<?php
namespace App\Domain\User;
final readonly class UserBuilder { }
```

**Detection:**
```bash
# Find files with multiple class definitions
grep -l "^class\|^interface\|^trait\|^enum" src/*.php | while read f; do
    count=$(grep -c "^class\|^interface\|^trait\|^enum" "$f")
    [ "$count" -gt 1 ] && echo "Multiple classes in: $f ($count)"
done
```

## 7. Missing Namespace Declaration

**Severity:** CRITICAL

```php
// File: src/Domain/User/Entity/User.php

// BAD: No namespace
<?php

class User { }  // Will be in global namespace
```

```php
// GOOD: Proper namespace
<?php

declare(strict_types=1);

namespace App\Domain\User\Entity;

final readonly class User { }
```

**Detection:**
```bash
# Find files without namespace
grep -rL "^namespace" --include="*.php" src/
```

## 8. Namespace Without Class

**Severity:** WARNING

```php
// File: src/Domain/User/functions.php

// BAD: Namespace but no class (PSR-4 doesn't autoload)
<?php

namespace App\Domain\User;

function createUser(): User { }  // Won't be autoloaded
```

```php
// GOOD: Use classmap or files autoload for functions
// composer.json
{
    "autoload": {
        "psr-4": {
            "App\\": "src/"
        },
        "files": [
            "src/Domain/User/functions.php"
        ]
    }
}
```

## 9. Incorrect Subdirectory Mapping

**Severity:** WARNING

```json
// PROBLEMATIC: Overlapping mappings
{
    "autoload": {
        "psr-4": {
            "App\\": "src/",
            "App\\Domain\\": "domain/"
        }
    }
}
```

This can cause issues because `App\Domain\User\User` could be loaded from either:
- `src/Domain/User/User.php`
- `domain/User/User.php`

```json
// BETTER: Non-overlapping or clear priority
{
    "autoload": {
        "psr-4": {
            "App\\": "src/"
        }
    }
}
// With structure: src/Domain/User/User.php
```

## 10. Tests in Main Autoload

**Severity:** WARNING

```json
// BAD: Tests in main autoload
{
    "autoload": {
        "psr-4": {
            "App\\": "src/",
            "App\\Tests\\": "tests/"
        }
    }
}
```

```json
// GOOD: Tests in autoload-dev
{
    "autoload": {
        "psr-4": {
            "App\\": "src/"
        }
    },
    "autoload-dev": {
        "psr-4": {
            "App\\Tests\\": "tests/"
        }
    }
}
```

## 11. Absolute vs Relative Paths

**Severity:** INFO

```json
// BAD: Absolute path
{
    "autoload": {
        "psr-4": {
            "App\\": "/var/www/project/src/"
        }
    }
}
```

```json
// GOOD: Relative path (from composer.json location)
{
    "autoload": {
        "psr-4": {
            "App\\": "src/"
        }
    }
}
```

## Summary Table

| # | Antipattern | Severity | Auto-fixable |
|---|-------------|----------|--------------|
| 1 | Namespace-path mismatch | CRITICAL | Partially |
| 2 | Class name vs filename mismatch | CRITICAL | Manual |
| 3 | Case sensitivity issues | CRITICAL | Manual |
| 4 | Missing trailing backslash | CRITICAL | Yes |
| 5 | Incorrect path separator | WARNING | Yes |
| 6 | Multiple classes per file | CRITICAL | Manual |
| 7 | Missing namespace | CRITICAL | Manual |
| 8 | Namespace without class | WARNING | N/A |
| 9 | Overlapping mappings | WARNING | Manual |
| 10 | Tests in main autoload | WARNING | Yes |
| 11 | Absolute paths | INFO | Yes |

## Quick Fix Commands

```bash
# Regenerate autoload
composer dump-autoload

# Validate composer.json
composer validate --strict

# Check for errors
composer dump-autoload --strict 2>&1 | grep -i error

# Optimize (generates classmap)
composer dump-autoload --optimize
```
