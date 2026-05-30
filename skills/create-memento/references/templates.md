# Memento Pattern Templates

## Basic Memento

**File:** `src/{architecture-path}/Memento/{Name}Memento.php`

```php
<?php

declare(strict_types=1);

namespace Memento;

final readonly class {Name}Memento
{
    public function __construct(
        private {StateType} $state,
        private \DateTimeImmutable $createdAt
    ) {}

    public function state(): {StateType}
    {
        return $this->state;
    }

    public function createdAt(): \DateTimeImmutable
    {
        return $this->createdAt;
    }
}
```

---

## Originator (Domain Object)

**File:** `src/{architecture-path}/{Name}.php`

```php
<?php

declare(strict_types=1);

namespace {BoundedContext};

use Memento\{Name}Memento;

final class {Name}
{
    private {StateType} $state;

    public function __construct({StateType} $state)
    {
        $this->state = $state;
    }

    public function createMemento(): {Name}Memento
    {
        return new {Name}Memento(
            state: $this->state,
            createdAt: new \DateTimeImmutable()
        );
    }

    public function restore({Name}Memento $memento): void
    {
        $this->state = $memento->state();
    }

    public function state(): {StateType}
    {
        return $this->state;
    }

    public function setState({StateType} $state): void
    {
        $this->state = $state;
    }
}
```

---

## Caretaker (History Manager)

**File:** `src/{architecture-path}/{Name}History.php`

```php
<?php

declare(strict_types=1);

namespace {BoundedContext};

use Memento\{Name}Memento;

final class {Name}History
{
    /**
     * @var array<{Name}Memento>
     */
    private array $mementos = [];
    private int $currentIndex = -1;

    public function save({Name}Memento $memento): void
    {
        $this->mementos = array_slice($this->mementos, 0, $this->currentIndex + 1);
        $this->mementos[] = $memento;
        ++$this->currentIndex;
    }

    public function undo(): ?{Name}Memento
    {
        if ($this->currentIndex > 0) {
            --$this->currentIndex;

            return $this->mementos[$this->currentIndex];
        }

        return null;
    }

    public function redo(): ?{Name}Memento
    {
        if ($this->currentIndex < count($this->mementos) - 1) {
            ++$this->currentIndex;

            return $this->mementos[$this->currentIndex];
        }

        return null;
    }

    public function canUndo(): bool
    {
        return $this->currentIndex > 0;
    }

    public function canRedo(): bool
    {
        return $this->currentIndex < count($this->mementos) - 1;
    }

    public function clear(): void
    {
        $this->mementos = [];
        $this->currentIndex = -1;
    }
}
```

---

## Limited History Caretaker

**File:** `src/{architecture-path}/{Name}LimitedHistory.php`

```php
<?php

declare(strict_types=1);

namespace {BoundedContext};

use Memento\{Name}Memento;

final class {Name}LimitedHistory
{
    /**
     * @var array<{Name}Memento>
     */
    private array $mementos = [];
    private int $currentIndex = -1;

    public function __construct(
        private readonly int $maxSize = 50
    ) {}

    public function save({Name}Memento $memento): void
    {
        $this->mementos = array_slice($this->mementos, 0, $this->currentIndex + 1);
        $this->mementos[] = $memento;

        if (count($this->mementos) > $this->maxSize) {
            array_shift($this->mementos);
        } else {
            ++$this->currentIndex;
        }
    }

    public function undo(): ?{Name}Memento
    {
        if ($this->currentIndex > 0) {
            --$this->currentIndex;

            return $this->mementos[$this->currentIndex];
        }

        return null;
    }

    public function redo(): ?{Name}Memento
    {
        if ($this->currentIndex < count($this->mementos) - 1) {
            ++$this->currentIndex;

            return $this->mementos[$this->currentIndex];
        }

        return null;
    }
}
```

---

## Document Memento

**File:** `src/{architecture-path}/Memento/DocumentMemento.php`

```php
<?php

declare(strict_types=1);

namespace Memento;

final readonly class DocumentMemento
{
    public function __construct(
        private string $content,
        private \DateTimeImmutable $createdAt
    ) {}

    public function content(): string
    {
        return $this->content;
    }

    public function createdAt(): \DateTimeImmutable
    {
        return $this->createdAt;
    }
}
```

---

## Document (Originator)

**File:** `src/{architecture-path}/Document.php`

```php
<?php

declare(strict_types=1);

namespace Document;

use Memento\DocumentMemento;

final class Document
{
    private string $content;

    public function __construct(string $content = '')
    {
        $this->content = $content;
    }

    public function createMemento(): DocumentMemento
    {
        return new DocumentMemento(
            content: $this->content,
            createdAt: new \DateTimeImmutable()
        );
    }

    public function restore(DocumentMemento $memento): void
    {
        $this->content = $memento->content();
    }

    public function content(): string
    {
        return $this->content;
    }

    public function setContent(string $content): void
    {
        $this->content = $content;
    }
}
```

---

## Order Draft Memento

**File:** `src/{architecture-path}/Memento/OrderDraftMemento.php`

```php
<?php

declare(strict_types=1);

namespace Memento;

final readonly class OrderDraftMemento
{
    /**
     * @param array<array{productId: string, quantity: int}> $items
     */
    public function __construct(
        private array $items,
        private ?string $couponCode,
        private \DateTimeImmutable $createdAt
    ) {}

    public function items(): array
    {
        return $this->items;
    }

    public function couponCode(): ?string
    {
        return $this->couponCode;
    }

    public function createdAt(): \DateTimeImmutable
    {
        return $this->createdAt;
    }
}
```

---

## Form State Memento

**File:** `src/{architecture-path}/Memento/FormStateMemento.php`

```php
<?php

declare(strict_types=1);

namespace Memento;

final readonly class FormStateMemento
{
    /**
     * @param array<string, mixed> $fields
     */
    public function __construct(
        private array $fields,
        private int $currentStep,
        private \DateTimeImmutable $createdAt
    ) {}

    public function fields(): array
    {
        return $this->fields;
    }

    public function currentStep(): int
    {
        return $this->currentStep;
    }

    public function createdAt(): \DateTimeImmutable
    {
        return $this->createdAt;
    }
}
```
