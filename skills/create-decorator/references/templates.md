# Decorator Pattern Templates

## Component Interface

**File:** `src/{architecture-path}/{Name}Interface.php`

```php
<?php

declare(strict_types=1);

namespace {BoundedContext};

interface {Name}Interface
{
    public function {operation}({params}): {returnType};
}
```

---

## Abstract Decorator

**File:** `src/{architecture-path}/Decorator/Abstract{Name}Decorator.php`

```php
<?php

declare(strict_types=1);

namespace Decorator;

use {BoundedContext}\{Name}Interface;

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

**File:** `src/{architecture-path}/Decorator/{Feature}{Name}Decorator.php`

```php
<?php

declare(strict_types=1);

namespace Decorator;

use {BoundedContext}\{Name}Interface;

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

**File:** `src/{architecture-path}/Service/OrderServiceInterface.php`

```php
<?php

declare(strict_types=1);

namespace Service;

use Entity\Order;
use ValueObject\OrderId;

interface OrderServiceInterface
{
    public function create(CreateOrderCommand $command): Order;

    public function findById(OrderId $id): ?Order;

    public function cancel(OrderId $id): void;
}
```

---

## Abstract Order Service Decorator

**File:** `src/{architecture-path}/Decorator/AbstractOrderServiceDecorator.php`

```php
<?php

declare(strict_types=1);

namespace Decorator;

use Entity\Order;
use Service\OrderServiceInterface;
use ValueObject\OrderId;

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

**File:** `src/{architecture-path}/NotifierInterface.php`

```php
<?php

declare(strict_types=1);

namespace Notification;

interface NotifierInterface
{
    public function send(Message $message): void;
}
```

---

## Abstract Notifier Decorator

**File:** `src/{architecture-path}/Decorator/AbstractNotifierDecorator.php`

```php
<?php

declare(strict_types=1);

namespace Decorator;

use Notification\Message;
use Notification\NotifierInterface;

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
