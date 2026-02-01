# Decorator Pattern Templates

## Component Interface

**File:** `src/Domain/{BoundedContext}/{Name}Interface.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext};

interface {Name}Interface
{
    public function {operation}({params}): {returnType};
}
```

---

## Abstract Decorator

**File:** `src/Domain/{BoundedContext}/Decorator/Abstract{Name}Decorator.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext}\Decorator;

use Domain\{BoundedContext}\{Name}Interface;

abstract class Abstract{Name}Decorator implements {Name}Interface
{
    public function __construct(
        protected readonly {Name}Interface $wrapped
    ) {}

    public function {operation}({params}): {returnType}
    {
        return $this->wrapped->{operation}({args});
    }
}
```

---

## Concrete Decorator

**File:** `src/Domain/{BoundedContext}/Decorator/{Feature}{Name}Decorator.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext}\Decorator;

use Domain\{BoundedContext}\{Name}Interface;

final readonly class {Feature}{Name}Decorator extends Abstract{Name}Decorator
{
    public function __construct(
        {Name}Interface $wrapped,
        {additionalDependencies}
    ) {
        parent::__construct($wrapped);
    }

    public function {operation}({params}): {returnType}
    {
        {beforeBehavior}

        $result = parent::{operation}({args});

        {afterBehavior}

        return $result;
    }
}
```

---

## Order Service Interface

**File:** `src/Domain/Order/Service/OrderServiceInterface.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Order\Service;

use Domain\Order\Entity\Order;
use Domain\Order\ValueObject\OrderId;

interface OrderServiceInterface
{
    public function create(CreateOrderCommand $command): Order;

    public function findById(OrderId $id): ?Order;

    public function cancel(OrderId $id): void;
}
```

---

## Abstract Order Service Decorator

**File:** `src/Domain/Order/Decorator/AbstractOrderServiceDecorator.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Order\Decorator;

use Domain\Order\Entity\Order;
use Domain\Order\Service\OrderServiceInterface;
use Domain\Order\ValueObject\OrderId;

abstract class AbstractOrderServiceDecorator implements OrderServiceInterface
{
    public function __construct(
        protected readonly OrderServiceInterface $wrapped
    ) {}

    public function create(CreateOrderCommand $command): Order
    {
        return $this->wrapped->create($command);
    }

    public function findById(OrderId $id): ?Order
    {
        return $this->wrapped->findById($id);
    }

    public function cancel(OrderId $id): void
    {
        $this->wrapped->cancel($id);
    }
}
```

---

## Notifier Interface

**File:** `src/Domain/Notification/NotifierInterface.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Notification;

interface NotifierInterface
{
    public function send(Message $message): void;
}
```

---

## Abstract Notifier Decorator

**File:** `src/Domain/Notification/Decorator/AbstractNotifierDecorator.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Notification\Decorator;

use Domain\Notification\Message;
use Domain\Notification\NotifierInterface;

abstract class AbstractNotifierDecorator implements NotifierInterface
{
    public function __construct(
        protected readonly NotifierInterface $wrapped
    ) {}

    public function send(Message $message): void
    {
        $this->wrapped->send($message);
    }
}
```
