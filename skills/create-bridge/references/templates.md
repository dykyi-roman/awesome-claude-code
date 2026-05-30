# Bridge Pattern Templates

## Implementor Interface

**File:** `src/{architecture-path}/{Name}ImplementorInterface.php`

```php
<?php

declare(strict_types=1);

namespace {BoundedContext};

interface {Name}ImplementorInterface
{
    public function {lowLevelOperation}({params}): {returnType};
}
```

---

## Abstraction

**File:** `src/{architecture-path}/Abstract{Name}.php`

```php
<?php

declare(strict_types=1);

namespace {BoundedContext};

abstract readonly class Abstract{Name}
{
    public function __construct(
        protected {Name}ImplementorInterface $implementor
    ) {}

    abstract public function {operation}({params}): {returnType};
}
```

---

## RefinedAbstraction

**File:** `src/{architecture-path}/{Type}{Name}.php`

```php
<?php

declare(strict_types=1);

namespace {BoundedContext};

final readonly class {Type}{Name} extends Abstract{Name}
{
    public function {operation}({params}): {returnType}
    {
        {preprocessing}
        return $this->implementor->{lowLevelOperation}({processedParams});
    }
}
```

---

## ConcreteImplementor

**File:** `src/{architecture-path}/{Platform}{Name}Implementor.php`

```php
<?php

declare(strict_types=1);

namespace {BoundedContext};

use {BoundedContext}\{Name}ImplementorInterface;

final readonly class {Platform}{Name}Implementor implements {Name}ImplementorInterface
{
    public function {lowLevelOperation}({params}): {returnType}
    {
        {platformSpecificImplementation}
    }
}
```

---

## Notification Bridge Example

**File:** `src/{architecture-path}/NotificationImplementorInterface.php`

```php
<?php

declare(strict_types=1);

namespace Notification;

use ValueObject\Message;

interface NotificationImplementorInterface
{
    public function sendMessage(Message $message): void;
}
```

**File:** `src/{architecture-path}/AbstractNotification.php`

```php
<?php

declare(strict_types=1);

namespace Notification;

use ValueObject\Message;

abstract readonly class AbstractNotification
{
    public function __construct(
        protected NotificationImplementorInterface $implementor
    ) {}

    abstract public function send(Message $message): void;
}
```

**File:** `src/{architecture-path}/UrgentNotification.php`

```php
<?php

declare(strict_types=1);

namespace Notification;

use ValueObject\Message;

final readonly class UrgentNotification extends AbstractNotification
{
    public function send(Message $message): void
    {
        $urgentMessage = $message->withPrefix('[URGENT] ');
        $this->implementor->sendMessage($urgentMessage);
    }
}
```

**File:** `src/{architecture-path}/EmailNotificationImplementor.php`

```php
<?php

declare(strict_types=1);

namespace Notification;

use Notification\NotificationImplementorInterface;
use ValueObject\Message;

final readonly class EmailNotificationImplementor implements NotificationImplementorInterface
{
    public function __construct(
        private \Swift_Mailer $mailer
    ) {}

    public function sendMessage(Message $message): void
    {
        $email = (new \Swift_Message($message->subject()))
            ->setFrom('noreply@example.com')
            ->setTo($message->recipient())
            ->setBody($message->body());

        $this->mailer->send($email);
    }
}
```
