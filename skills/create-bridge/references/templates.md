# Bridge Pattern Templates

## Implementor Interface

**File:** `src/Domain/{BoundedContext}/{Name}ImplementorInterface.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext};

interface {Name}ImplementorInterface
{
    public function {lowLevelOperation}({params}): {returnType};
}
```

---

## Abstraction

**File:** `src/Domain/{BoundedContext}/Abstract{Name}.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext};

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

**File:** `src/Domain/{BoundedContext}/{Type}{Name}.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext};

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

**File:** `src/Infrastructure/{BoundedContext}/{Platform}{Name}Implementor.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\{BoundedContext};

use Domain\{BoundedContext}\{Name}ImplementorInterface;

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

**File:** `src/Domain/Notification/NotificationImplementorInterface.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Notification;

use Domain\Notification\ValueObject\Message;

interface NotificationImplementorInterface
{
    public function sendMessage(Message $message): void;
}
```

**File:** `src/Domain/Notification/AbstractNotification.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Notification;

use Domain\Notification\ValueObject\Message;

abstract readonly class AbstractNotification
{
    public function __construct(
        protected NotificationImplementorInterface $implementor
    ) {}

    abstract public function send(Message $message): void;
}
```

**File:** `src/Domain/Notification/UrgentNotification.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Notification;

use Domain\Notification\ValueObject\Message;

final readonly class UrgentNotification extends AbstractNotification
{
    public function send(Message $message): void
    {
        $urgentMessage = $message->withPrefix('[URGENT] ');
        $this->implementor->sendMessage($urgentMessage);
    }
}
```

**File:** `src/Infrastructure/Notification/EmailNotificationImplementor.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Notification;

use Domain\Notification\NotificationImplementorInterface;
use Domain\Notification\ValueObject\Message;

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
