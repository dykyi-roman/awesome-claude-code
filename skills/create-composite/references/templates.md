# Composite Pattern Templates

## Component Interface

**File:** `src/{architecture-path}/{Name}Interface.php`

```php
<?php

declare(strict_types=1);

namespace {BoundedContext};

interface {Name}Interface
{
    public function {operation}(): {returnType};
}
```

---

## Leaf

**File:** `src/{architecture-path}/{Name}.php`

```php
<?php

declare(strict_types=1);

namespace {BoundedContext};

final readonly class {Name} implements {Name}Interface
{
    public function __construct(
        private string $data
    ) {}

    public function {operation}(): {returnType}
    {
        return {leafBehavior};
    }
}
```

---

## Composite

**File:** `src/{architecture-path}/{Name}Composite.php`

```php
<?php

declare(strict_types=1);

namespace {BoundedContext};

final class {Name}Composite implements {Name}Interface
{
    private array $children = [];

    public function add({Name}Interface $child): void
    {
        $this->children[] = $child;
    }

    public function remove({Name}Interface $child): void
    {
        $this->children = array_filter(
            $this->children,
            fn($c) => $c !== $child
        );
    }

    public function {operation}(): {returnType}
    {
        $result = {initialValue};

        foreach ($this->children as $child) {
            $result {combineOperation} $child->{operation}();
        }

        return $result;
    }

    public function getChildren(): array
    {
        return $this->children;
    }
}
```

---

## Menu Interface

**File:** `src/{architecture-path}/MenuItemInterface.php`

```php
<?php

declare(strict_types=1);

namespace Menu;

interface MenuItemInterface
{
    public function render(int $level = 0): string;

    public function getName(): string;
}
```

---

## Menu Item (Leaf)

**File:** `src/{architecture-path}/MenuItem.php`

```php
<?php

declare(strict_types=1);

namespace Menu;

final readonly class MenuItem implements MenuItemInterface
{
    public function __construct(
        private string $name,
        private string $url
    ) {}

    public function render(int $level = 0): string
    {
        $indent = str_repeat('  ', $level);
        return "{$indent}<li><a href=\"{$this->url}\">{$this->name}</a></li>\n";
    }

    public function getName(): string
    {
        return $this->name;
    }
}
```

---

## Menu Composite

**File:** `src/{architecture-path}/MenuComposite.php`

```php
<?php

declare(strict_types=1);

namespace Menu;

final class MenuComposite implements MenuItemInterface
{
    private array $children = [];

    public function __construct(
        private readonly string $name
    ) {}

    public function add(MenuItemInterface $item): void
    {
        $this->children[] = $item;
    }

    public function remove(MenuItemInterface $item): void
    {
        $this->children = array_filter(
            $this->children,
            fn($child) => $child !== $item
        );
    }

    public function render(int $level = 0): string
    {
        $indent = str_repeat('  ', $level);
        $html = "{$indent}<li>{$this->name}\n";
        $html .= "{$indent}  <ul>\n";

        foreach ($this->children as $child) {
            $html .= $child->render($level + 2);
        }

        $html .= "{$indent}  </ul>\n";
        $html .= "{$indent}</li>\n";

        return $html;
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
