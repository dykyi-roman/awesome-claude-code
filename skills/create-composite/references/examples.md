# Composite Pattern Examples

## Permission Composite

**File:** `src/Domain/Permission/PermissionComposite.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Permission;

final class PermissionComposite implements PermissionInterface
{
    private array $children = [];

    public function __construct(
        private readonly string $name
    ) {}

    public function add(PermissionInterface $permission): void
    {
        $this->children[] = $permission;
    }

    public function hasAccess(string $resource): bool
    {
        foreach ($this->children as $child) {
            if ($child->hasAccess($resource)) {
                return true;
            }
        }

        return false;
    }

    public function getName(): string
    {
        return $this->name;
    }
}
```

**File:** `src/Domain/Permission/Permission.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Permission;

final readonly class Permission implements PermissionInterface
{
    public function __construct(
        private string $name,
        private array $resources
    ) {}

    public function hasAccess(string $resource): bool
    {
        return in_array($resource, $this->resources, true);
    }

    public function getName(): string
    {
        return $this->name;
    }
}
```

---

## Price Rule Composite

**File:** `src/Domain/Pricing/PriceRuleComposite.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Pricing;

use Domain\Pricing\ValueObject\Price;

final class PriceRuleComposite implements PriceRuleInterface
{
    private array $rules = [];

    public function add(PriceRuleInterface $rule): void
    {
        $this->rules[] = $rule;
    }

    public function calculate(Price $basePrice): Price
    {
        $result = $basePrice;

        foreach ($this->rules as $rule) {
            $result = $rule->calculate($result);
        }

        return $result;
    }
}
```

**File:** `src/Domain/Pricing/DiscountRule.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Pricing;

use Domain\Pricing\ValueObject\Price;

final readonly class DiscountRule implements PriceRuleInterface
{
    public function __construct(
        private float $percentage
    ) {}

    public function calculate(Price $basePrice): Price
    {
        $discount = $basePrice->amount() * ($this->percentage / 100);
        return new Price($basePrice->amount() - $discount);
    }
}
```

---

## File System Composite

**File:** `src/Domain/FileSystem/Directory.php`

```php
<?php

declare(strict_types=1);

namespace Domain\FileSystem;

final class Directory implements FileSystemInterface
{
    private array $children = [];

    public function __construct(
        private readonly string $name
    ) {}

    public function add(FileSystemInterface $item): void
    {
        $this->children[] = $item;
    }

    public function getSize(): int
    {
        $totalSize = 0;

        foreach ($this->children as $child) {
            $totalSize += $child->getSize();
        }

        return $totalSize;
    }

    public function getName(): string
    {
        return $this->name;
    }

    public function getChildren(): array
    {
        return $this->children;
    }
}
```

**File:** `src/Domain/FileSystem/File.php`

```php
<?php

declare(strict_types=1);

namespace Domain\FileSystem;

final readonly class File implements FileSystemInterface
{
    public function __construct(
        private string $name,
        private int $size
    ) {}

    public function getSize(): int
    {
        return $this->size;
    }

    public function getName(): string
    {
        return $this->name;
    }
}
```

---

## Unit Tests

### MenuCompositeTest

**File:** `tests/Unit/Domain/Menu/MenuCompositeTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\Menu;

use Domain\Menu\MenuComposite;
use Domain\Menu\MenuItem;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(MenuComposite::class)]
final class MenuCompositeTest extends TestCase
{
    public function testRenderWithChildren(): void
    {
        $menu = new MenuComposite('Products');
        $menu->add(new MenuItem('Laptops', '/laptops'));
        $menu->add(new MenuItem('Phones', '/phones'));

        $result = $menu->render();

        self::assertStringContainsString('Products', $result);
        self::assertStringContainsString('Laptops', $result);
        self::assertStringContainsString('Phones', $result);
    }

    public function testNestedComposite(): void
    {
        $menu = new MenuComposite('Main');

        $submenu = new MenuComposite('Products');
        $submenu->add(new MenuItem('Laptops', '/laptops'));

        $menu->add($submenu);
        $menu->add(new MenuItem('About', '/about'));

        $result = $menu->render();

        self::assertStringContainsString('Main', $result);
        self::assertStringContainsString('Products', $result);
        self::assertStringContainsString('Laptops', $result);
    }
}
```

### PermissionCompositeTest

**File:** `tests/Unit/Domain/Permission/PermissionCompositeTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\Permission;

use Domain\Permission\Permission;
use Domain\Permission\PermissionComposite;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(PermissionComposite::class)]
final class PermissionCompositeTest extends TestCase
{
    public function testHasAccessReturnsTrueIfAnyChildHasAccess(): void
    {
        $composite = new PermissionComposite('Admin');
        $composite->add(new Permission('read', ['users', 'posts']));
        $composite->add(new Permission('write', ['posts']));

        self::assertTrue($composite->hasAccess('users'));
        self::assertTrue($composite->hasAccess('posts'));
        self::assertFalse($composite->hasAccess('settings'));
    }

    public function testNestedComposite(): void
    {
        $root = new PermissionComposite('Root');

        $admin = new PermissionComposite('Admin');
        $admin->add(new Permission('users', ['create', 'edit']));

        $editor = new PermissionComposite('Editor');
        $editor->add(new Permission('posts', ['create', 'edit']));

        $root->add($admin);
        $root->add($editor);

        self::assertTrue($root->hasAccess('create'));
        self::assertTrue($root->hasAccess('edit'));
    }
}
```
