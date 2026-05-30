# PSR-14 Event Dispatcher Examples

## Domain Events in DDD

```php
<?php

declare(strict_types=1);

namespace Handler;

use Command\CreateUserCommand;
use Entity\User;
use Repository\UserRepositoryInterface;
use ValueObject\Email;
use Psr\EventDispatcher\EventDispatcherInterface;

final readonly class CreateUserHandler
{
    public function __construct(
        private UserRepositoryInterface $repository,
        private EventDispatcherInterface $eventDispatcher,
    ) {
    }

    public function __invoke(CreateUserCommand $command): void
    {
        $user = User::create(
            Email::fromString($command->email),
            $command->name,
        );

        $this->repository->save($user);

        foreach ($user->pullEvents() as $event) {
            $this->eventDispatcher->dispatch($event);
        }
    }
}
```

## Event Listeners

```php
<?php

declare(strict_types=1);

namespace Listener;

use Event\UserCreated;
use Psr\Log\LoggerInterface;

final readonly class LogUserCreationListener
{
    public function __construct(
        private LoggerInterface $logger,
    ) {
    }

    public function __invoke(UserCreated $event): void
    {
        $this->logger->info('New user created', [
            'user_id' => $event->userId->toString(),
            'email' => $event->email,
            'occurred_at' => $event->occurredAt->format('c'),
        ]);
    }
}

final readonly class SendWelcomeEmailListener
{
    public function __construct(
        private MailerInterface $mailer,
    ) {
    }

    public function __invoke(UserCreated $event): void
    {
        $this->mailer->send(
            to: $event->email,
            subject: 'Welcome to our platform!',
            template: 'emails/welcome.html.twig',
            context: ['user_id' => $event->userId->toString()],
        );
    }
}

final readonly class CreateUserProfileListener
{
    public function __construct(
        private ProfileRepositoryInterface $profileRepository,
    ) {
    }

    public function __invoke(UserCreated $event): void
    {
        $profile = UserProfile::createDefault($event->userId);
        $this->profileRepository->save($profile);
    }
}
```

## Service Provider Registration

```php
<?php

declare(strict_types=1);

namespace Event;

use Psr\Container\ContainerInterface;

final readonly class EventServiceProvider
{
    public function register(ContainerInterface $container): void
    {
        $provider = $container->get(ListenerProvider::class);

        // User events
        $provider->addListener(
            UserCreated::class,
            $container->get(LogUserCreationListener::class),
        );
        $provider->addListener(
            UserCreated::class,
            $container->get(SendWelcomeEmailListener::class),
        );
        $provider->addListener(
            UserCreated::class,
            $container->get(CreateUserProfileListener::class),
        );

        // Order events
        $provider->addListener(
            OrderPlaced::class,
            $container->get(ProcessPaymentListener::class),
        );
        $provider->addListener(
            OrderPlaced::class,
            $container->get(NotifyWarehouseListener::class),
        );
    }
}
```

## Testing Events

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\User;

use Command\CreateUserCommand;
use Handler\CreateUserHandler;
use Event\UserCreated;
use Event\EventDispatcher;
use Event\ListenerProvider;
use PHPUnit\Framework\TestCase;

final class CreateUserHandlerTest extends TestCase
{
    public function test_it_dispatches_user_created_event(): void
    {
        $provider = new ListenerProvider();
        $dispatcher = new EventDispatcher($provider);
        $repository = new InMemoryUserRepository();

        $dispatchedEvents = [];
        $provider->addListener(UserCreated::class, function ($event) use (&$dispatchedEvents) {
            $dispatchedEvents[] = $event;
        });

        $handler = new CreateUserHandler($repository, $dispatcher);

        ($handler)(new CreateUserCommand('test@example.com', 'John'));

        self::assertCount(1, $dispatchedEvents);
        self::assertInstanceOf(UserCreated::class, $dispatchedEvents[0]);
        self::assertSame('test@example.com', $dispatchedEvents[0]->email);
    }
}
```

## CQRS with Events

```php
<?php

declare(strict_types=1);

namespace Handler;

use Command\PlaceOrderCommand;
use Entity\Order;
use Event\OrderPlaced;
use Psr\EventDispatcher\EventDispatcherInterface;

final readonly class PlaceOrderHandler
{
    public function __construct(
        private OrderRepositoryInterface $orderRepository,
        private EventDispatcherInterface $eventDispatcher,
    ) {
    }

    public function __invoke(PlaceOrderCommand $command): void
    {
        $order = Order::place(
            $command->customerId,
            $command->items,
        );

        $this->orderRepository->save($order);

        // Dispatch domain events
        foreach ($order->pullEvents() as $event) {
            $this->eventDispatcher->dispatch($event);
        }
    }
}
```
