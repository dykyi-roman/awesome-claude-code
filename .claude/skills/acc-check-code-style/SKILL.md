---
name: acc-check-code-style
description: Analyzes PHP code for style issues. Checks PSR-12 compliance, formatting consistency, whitespace usage, line length.
---

# Code Style Check

Analyze PHP code for style consistency and PSR-12 compliance.

## Detection Patterns

### 1. PSR-12 Violations

```php
// BAD: Opening brace on same line for class
class User {
}

// GOOD: Opening brace on new line
class User
{
}

// BAD: Opening brace on new line for methods
public function getName()
{
}

// GOOD: Opening brace on same line for control structures
if ($condition) {
}

// BAD: No space after keywords
if($condition) {}
foreach($items as $item) {}

// GOOD: Space after keywords
if ($condition) {}
foreach ($items as $item) {}
```

### 2. Line Length

```php
// BAD: Exceeds 120 characters
$result = $this->veryLongServiceName->processWithManyParameters($parameter1, $parameter2, $parameter3, $parameter4, $parameter5);

// GOOD: Broken into multiple lines
$result = $this->veryLongServiceName->processWithManyParameters(
    $parameter1,
    $parameter2,
    $parameter3,
    $parameter4,
    $parameter5
);
```

### 3. Indentation

```php
// BAD: Mixed tabs and spaces
class User
{
	private string $name;  // Tab
    private int $age;      // Spaces
}

// GOOD: Consistent 4 spaces
class User
{
    private string $name;
    private int $age;
}
```

### 4. Blank Lines

```php
// BAD: No blank line after namespace
namespace App\Service;
use App\Repository;

// GOOD: Blank line after namespace
namespace App\Service;

use App\Repository;

// BAD: No blank line between methods
public function getName(): string
{
    return $this->name;
}
public function setName(string $name): void
{
    $this->name = $name;
}

// GOOD: Blank line between methods
public function getName(): string
{
    return $this->name;
}

public function setName(string $name): void
{
    $this->name = $name;
}
```

### 5. Trailing Whitespace

```php
// BAD: Trailing spaces at end of line
$name = 'John';
$age = 25;

// GOOD: No trailing whitespace
$name = 'John';
$age = 25;
```

### 6. Use Statement Ordering

```php
// BAD: Unordered use statements
use App\Service\OrderService;
use App\Entity\User;
use Symfony\Component\HttpFoundation\Request;
use App\Repository\UserRepository;

// GOOD: Grouped and alphabetized
use App\Entity\User;
use App\Repository\UserRepository;
use App\Service\OrderService;
use Symfony\Component\HttpFoundation\Request;
```

### 7. Array Syntax

```php
// BAD: Long array syntax
$items = array(1, 2, 3);
$config = array(
    'key' => 'value',
);

// GOOD: Short array syntax
$items = [1, 2, 3];
$config = [
    'key' => 'value',
];
```

### 8. Operator Spacing

```php
// BAD: Inconsistent spacing
$sum=$a+$b;
$name = $first.$last;
$condition = $a>$b;

// GOOD: Consistent spacing
$sum = $a + $b;
$name = $first . $last;
$condition = $a > $b;
```

### 9. Comma Spacing

```php
// BAD: No space after comma
$result = calculate($a,$b,$c);
$array = [1,2,3];

// GOOD: Space after comma
$result = calculate($a, $b, $c);
$array = [1, 2, 3];
```

### 10. Return Type Declaration

```php
// BAD: Space before colon
public function getName() : string {}

// GOOD: No space before colon
public function getName(): string {}

// BAD: No space after colon
public function getName():string {}

// GOOD: Space after colon
public function getName(): string {}
```

## Grep Patterns

```bash
# Opening brace on same line for class
Grep: "class\s+\w+\s*\{" --glob "**/*.php"

# No space after if/foreach/while
Grep: "(if|foreach|while|for|switch)\(" --glob "**/*.php"

# Lines over 120 chars (needs manual check)
Grep: "^.{121,}$" --glob "**/*.php"

# array() instead of []
Grep: "array\s*\(" --glob "**/*.php"

# Missing space around operators
Grep: "[^ ]==[^ ]|[^ ]!=[^ ]" --glob "**/*.php"
```

## Severity Classification

| Pattern | Severity |
|---------|----------|
| Mixed tabs/spaces | 🟠 Major |
| PSR-12 brace placement | 🟡 Minor |
| Line length > 120 | 🟡 Minor |
| Operator spacing | 🟢 Suggestion |
| Use statement order | 🟢 Suggestion |

## Automated Fixing

Most style issues can be automatically fixed:

```bash
# PHP-CS-Fixer
php-cs-fixer fix --rules=@PSR12

# PHP_CodeSniffer
phpcbf --standard=PSR12 src/
```

## Output Format

```markdown
### Style Issue: [Description]

**Severity:** 🟠/🟡/🟢
**Location:** `file.php:line`
**Rule:** PSR-12 / Project Standard

**Issue:**
[Description of the style violation]

**Current:**
```php
if($condition){
```

**Suggested:**
```php
if ($condition) {
```

**Auto-fix:**
Run `php-cs-fixer fix --rules=@PSR12`
```
