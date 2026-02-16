# Memento Pattern Examples

## Document Editor with Undo/Redo

### DocumentMemento

**File:** `src/Domain/Document/Memento/DocumentMemento.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Document\Memento;

final readonly class DocumentMemento
{
    public function __construct(
        private string $content,
        private int $cursorPosition,
        private \DateTimeImmutable $createdAt
    ) {}

    public function content(): string
    {
        return $this->content;
    }

    public function cursorPosition(): int
    {
        return $this->cursorPosition;
    }

    public function createdAt(): \DateTimeImmutable
    {
        return $this->createdAt;
    }
}
```

---

### Document (Originator)

**File:** `src/Domain/Document/Document.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Document;

use Domain\Document\Memento\DocumentMemento;

final class Document
{
    private string $content;
    private int $cursorPosition;

    public function __construct(string $content = '', int $cursorPosition = 0)
    {
        $this->content = $content;
        $this->cursorPosition = $cursorPosition;
    }

    public function createMemento(): DocumentMemento
    {
        return new DocumentMemento(
            content: $this->content,
            cursorPosition: $this->cursorPosition,
            createdAt: new \DateTimeImmutable()
        );
    }

    public function restore(DocumentMemento $memento): void
    {
        $this->content = $memento->content();
        $this->cursorPosition = $memento->cursorPosition();
    }

    public function content(): string
    {
        return $this->content;
    }

    public function setContent(string $content): void
    {
        $this->content = $content;
    }

    public function cursorPosition(): int
    {
        return $this->cursorPosition;
    }

    public function setCursorPosition(int $position): void
    {
        $this->cursorPosition = $position;
    }
}
```

---

### DocumentHistory (Caretaker)

**File:** `src/Application/Document/DocumentHistory.php`

```php
<?php

declare(strict_types=1);

namespace Application\Document;

use Domain\Document\Memento\DocumentMemento;

final class DocumentHistory
{
    /**
     * @var array<DocumentMemento>
     */
    private array $mementos = [];
    private int $currentIndex = -1;

    public function save(DocumentMemento $memento): void
    {
        $this->mementos = array_slice($this->mementos, 0, $this->currentIndex + 1);
        $this->mementos[] = $memento;
        ++$this->currentIndex;
    }

    public function undo(): ?DocumentMemento
    {
        if ($this->currentIndex > 0) {
            --$this->currentIndex;

            return $this->mementos[$this->currentIndex];
        }

        return null;
    }

    public function redo(): ?DocumentMemento
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

    public function historySize(): int
    {
        return count($this->mementos);
    }
}
```

---

## Order Draft Management

### OrderDraftMemento

**File:** `src/Domain/Order/Memento/OrderDraftMemento.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Order\Memento;

final readonly class OrderDraftMemento
{
    /**
     * @param array<array{productId: string, quantity: int, price: int}> $items
     */
    public function __construct(
        private string $customerId,
        private array $items,
        private ?string $couponCode,
        private \DateTimeImmutable $createdAt
    ) {}

    public function customerId(): string
    {
        return $this->customerId;
    }

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

### OrderDraft (Originator)

**File:** `src/Domain/Order/OrderDraft.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Order;

use Domain\Order\Memento\OrderDraftMemento;

final class OrderDraft
{
    private string $customerId;
    private array $items = [];
    private ?string $couponCode = null;

    public function __construct(string $customerId)
    {
        $this->customerId = $customerId;
    }

    public function createMemento(): OrderDraftMemento
    {
        return new OrderDraftMemento(
            customerId: $this->customerId,
            items: $this->items,
            couponCode: $this->couponCode,
            createdAt: new \DateTimeImmutable()
        );
    }

    public function restore(OrderDraftMemento $memento): void
    {
        $this->customerId = $memento->customerId();
        $this->items = $memento->items();
        $this->couponCode = $memento->couponCode();
    }

    public function addItem(string $productId, int $quantity, int $price): void
    {
        $this->items[] = [
            'productId' => $productId,
            'quantity' => $quantity,
            'price' => $price,
        ];
    }

    public function applyCoupon(string $code): void
    {
        $this->couponCode = $code;
    }

    public function items(): array
    {
        return $this->items;
    }

    public function couponCode(): ?string
    {
        return $this->couponCode;
    }
}
```

---

### OrderDraftHistory (Caretaker with Limit)

**File:** `src/Application/Order/OrderDraftHistory.php`

```php
<?php

declare(strict_types=1);

namespace Application\Order;

use Domain\Order\Memento\OrderDraftMemento;

final class OrderDraftHistory
{
    private const MAX_HISTORY_SIZE = 50;

    /**
     * @var array<OrderDraftMemento>
     */
    private array $mementos = [];
    private int $currentIndex = -1;

    public function save(OrderDraftMemento $memento): void
    {
        $this->mementos = array_slice($this->mementos, 0, $this->currentIndex + 1);
        $this->mementos[] = $memento;

        if (count($this->mementos) > self::MAX_HISTORY_SIZE) {
            array_shift($this->mementos);
        } else {
            ++$this->currentIndex;
        }
    }

    public function undo(): ?OrderDraftMemento
    {
        if ($this->currentIndex > 0) {
            --$this->currentIndex;

            return $this->mementos[$this->currentIndex];
        }

        return null;
    }

    public function redo(): ?OrderDraftMemento
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

## Form State Management

### FormStateMemento

**File:** `src/Domain/Form/Memento/FormStateMemento.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Form\Memento;

final readonly class FormStateMemento
{
    /**
     * @param array<string, mixed> $fields
     */
    public function __construct(
        private array $fields,
        private int $currentStep,
        private bool $validated,
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

    public function isValidated(): bool
    {
        return $this->validated;
    }

    public function createdAt(): \DateTimeImmutable
    {
        return $this->createdAt;
    }
}
```

---

### MultiStepForm (Originator)

**File:** `src/Domain/Form/MultiStepForm.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Form;

use Domain\Form\Memento\FormStateMemento;

final class MultiStepForm
{
    private array $fields = [];
    private int $currentStep = 0;
    private bool $validated = false;

    public function createMemento(): FormStateMemento
    {
        return new FormStateMemento(
            fields: $this->fields,
            currentStep: $this->currentStep,
            validated: $this->validated,
            createdAt: new \DateTimeImmutable()
        );
    }

    public function restore(FormStateMemento $memento): void
    {
        $this->fields = $memento->fields();
        $this->currentStep = $memento->currentStep();
        $this->validated = $memento->isValidated();
    }

    public function setField(string $name, mixed $value): void
    {
        $this->fields[$name] = $value;
        $this->validated = false;
    }

    public function nextStep(): void
    {
        ++$this->currentStep;
    }

    public function previousStep(): void
    {
        if ($this->currentStep > 0) {
            --$this->currentStep;
        }
    }

    public function markAsValidated(): void
    {
        $this->validated = true;
    }

    public function fields(): array
    {
        return $this->fields;
    }

    public function currentStep(): int
    {
        return $this->currentStep;
    }
}
```

---

## Unit Tests

### DocumentHistoryTest

**File:** `tests/Unit/Application/Document/DocumentHistoryTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Application\Document;

use Application\Document\DocumentHistory;
use Domain\Document\Document;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(DocumentHistory::class)]
final class DocumentHistoryTest extends TestCase
{
    private DocumentHistory $history;
    private Document $document;

    protected function setUp(): void
    {
        $this->history = new DocumentHistory();
        $this->document = new Document(content: 'Initial');
    }

    public function testSavesMemento(): void
    {
        $this->history->save($this->document->createMemento());

        self::assertSame(1, $this->history->historySize());
    }

    public function testUndoRestoresPreviousState(): void
    {
        $this->history->save($this->document->createMemento());

        $this->document->setContent('Modified');
        $this->history->save($this->document->createMemento());

        $memento = $this->history->undo();
        self::assertNotNull($memento);

        $this->document->restore($memento);

        self::assertSame('Initial', $this->document->content());
    }

    public function testRedoRestoresNextState(): void
    {
        $this->history->save($this->document->createMemento());

        $this->document->setContent('Modified');
        $this->history->save($this->document->createMemento());

        $this->history->undo();
        $memento = $this->history->redo();

        self::assertNotNull($memento);
        $this->document->restore($memento);

        self::assertSame('Modified', $this->document->content());
    }

    public function testCannotUndoBeyondFirstState(): void
    {
        $this->history->save($this->document->createMemento());

        $memento = $this->history->undo();

        self::assertNull($memento);
        self::assertFalse($this->history->canUndo());
    }

    public function testCannotRedoBeyondLastState(): void
    {
        $this->history->save($this->document->createMemento());

        $memento = $this->history->redo();

        self::assertNull($memento);
        self::assertFalse($this->history->canRedo());
    }

    public function testClearRemovesAllHistory(): void
    {
        $this->history->save($this->document->createMemento());
        $this->history->save($this->document->createMemento());

        $this->history->clear();

        self::assertSame(0, $this->history->historySize());
        self::assertFalse($this->history->canUndo());
    }
}
```

---

### OrderDraftMementoTest

**File:** `tests/Unit/Domain/Order/Memento/OrderDraftMementoTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\Order\Memento;

use Domain\Order\Memento\OrderDraftMemento;
use Domain\Order\OrderDraft;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(OrderDraftMemento::class)]
#[CoversClass(OrderDraft::class)]
final class OrderDraftMementoTest extends TestCase
{
    public function testCreatesMemento(): void
    {
        $draft = new OrderDraft(customerId: 'user-123');
        $draft->addItem(productId: 'prod-1', quantity: 2, price: 1000);

        $memento = $draft->createMemento();

        self::assertSame('user-123', $memento->customerId());
        self::assertCount(1, $memento->items());
        self::assertNull($memento->couponCode());
    }

    public function testRestoresFromMemento(): void
    {
        $draft = new OrderDraft(customerId: 'user-123');
        $draft->addItem(productId: 'prod-1', quantity: 2, price: 1000);
        $draft->applyCoupon('SAVE10');

        $memento = $draft->createMemento();

        $newDraft = new OrderDraft(customerId: 'user-456');
        $newDraft->restore($memento);

        self::assertCount(1, $newDraft->items());
        self::assertSame('SAVE10', $newDraft->couponCode());
    }

    public function testMementoIsImmutable(): void
    {
        $items = [['productId' => 'prod-1', 'quantity' => 1, 'price' => 500]];
        $memento = new OrderDraftMemento(
            customerId: 'user-123',
            items: $items,
            couponCode: null,
            createdAt: new \DateTimeImmutable()
        );

        $items[] = ['productId' => 'prod-2', 'quantity' => 2, 'price' => 1000];

        self::assertCount(1, $memento->items());
    }
}
```
