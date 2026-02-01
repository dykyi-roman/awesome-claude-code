# PSR-14 Event Dispatcher Templates

## Priority Listener Provider

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Event;

use Psr\EventDispatcher\ListenerProviderInterface;

final class PriorityListenerProvider implements ListenerProviderInterface
{
    /** @var array<class-string, array<int, array<callable>>> */
    private array $listeners = [];

    public function getListenersForEvent(object $event): iterable
    {
        $eventClass = $event::class;
        $listeners = $this->getListenersForClass($eventClass);

        foreach (class_parents($eventClass) as $parent) {
            $listeners = array_merge_recursive(
                $listeners,
                $this->getListenersForClass($parent),
            );
        }

        foreach (class_implements($eventClass) as $interface) {
            $listeners = array_merge_recursive(
                $listeners,
                $this->getListenersForClass($interface),
            );
        }

        krsort($listeners);

        foreach ($listeners as $priorityListeners) {
            yield from $priorityListeners;
        }
    }

    /** @param class-string $eventClass */
    public function addListener(
        string $eventClass,
        callable $listener,
        int $priority = 0,
    ): void {
        $this->listeners[$eventClass][$priority][] = $listener;
    }

    /** @return array<int, array<callable>> */
    private function getListenersForClass(string $class): array
    {
        return $this->listeners[$class] ?? [];
    }
}
```

## Async Event Dispatcher

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Event;

use Psr\EventDispatcher\EventDispatcherInterface;

final readonly class AsyncEventDispatcher implements EventDispatcherInterface
{
    public function __construct(
        private EventDispatcherInterface $syncDispatcher,
        private MessageBusInterface $messageBus,
    ) {
    }

    public function dispatch(object $event): object
    {
        if ($event instanceof AsyncEventInterface) {
            $this->messageBus->dispatch(new EventMessage($event));

            return $event;
        }

        return $this->syncDispatcher->dispatch($event);
    }
}

interface AsyncEventInterface
{
}

final readonly class EventMessage
{
    public function __construct(
        public object $event,
    ) {
    }
}
```

## Container-Aware Listener Provider

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Event;

use Psr\Container\ContainerInterface;
use Psr\EventDispatcher\ListenerProviderInterface;

final class ContainerListenerProvider implements ListenerProviderInterface
{
    /** @var array<class-string, array<array{service: string, method: string}>> */
    private array $listeners = [];

    public function __construct(
        private readonly ContainerInterface $container,
    ) {
    }

    public function getListenersForEvent(object $event): iterable
    {
        $eventClass = $event::class;

        foreach ($this->listeners[$eventClass] ?? [] as $listenerConfig) {
            $service = $this->container->get($listenerConfig['service']);

            yield [$service, $listenerConfig['method']];
        }
    }

    /** @param class-string $eventClass */
    public function addListener(
        string $eventClass,
        string $serviceId,
        string $method = '__invoke',
    ): void {
        $this->listeners[$eventClass][] = [
            'service' => $serviceId,
            'method' => $method,
        ];
    }
}
```

## Aggregate Listener Provider

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Event;

use Psr\EventDispatcher\ListenerProviderInterface;

final readonly class AggregateListenerProvider implements ListenerProviderInterface
{
    /** @var ListenerProviderInterface[] */
    private array $providers;

    public function __construct(ListenerProviderInterface ...$providers)
    {
        $this->providers = $providers;
    }

    public function getListenersForEvent(object $event): iterable
    {
        foreach ($this->providers as $provider) {
            yield from $provider->getListenersForEvent($event);
        }
    }
}
```

## Logging Event Dispatcher

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Event;

use Psr\EventDispatcher\EventDispatcherInterface;
use Psr\Log\LoggerInterface;

final readonly class LoggingEventDispatcher implements EventDispatcherInterface
{
    public function __construct(
        private EventDispatcherInterface $dispatcher,
        private LoggerInterface $logger,
    ) {
    }

    public function dispatch(object $event): object
    {
        $eventClass = $event::class;

        $this->logger->debug('Dispatching event', [
            'event' => $eventClass,
        ]);

        $startTime = microtime(true);
        $result = $this->dispatcher->dispatch($event);
        $duration = microtime(true) - $startTime;

        $this->logger->info('Event dispatched', [
            'event' => $eventClass,
            'duration_ms' => round($duration * 1000, 2),
        ]);

        return $result;
    }
}
```

## Event Subscriber

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Event;

interface EventSubscriberInterface
{
    /** @return array<class-string, string|array{method: string, priority?: int}> */
    public static function getSubscribedEvents(): array;
}

final readonly class UserEventSubscriber implements EventSubscriberInterface
{
    public function __construct(
        private EmailServiceInterface $emailService,
        private LoggerInterface $logger,
    ) {
    }

    public static function getSubscribedEvents(): array
    {
        return [
            UserCreated::class => ['onUserCreated', 'priority' => 10],
            UserDeleted::class => 'onUserDeleted',
        ];
    }

    public function onUserCreated(UserCreated $event): void
    {
        $this->emailService->sendWelcome($event->email);
    }

    public function onUserDeleted(UserDeleted $event): void
    {
        $this->logger->info('User deleted', ['id' => $event->userId]);
    }
}

// Registration helper
function registerSubscriber(
    ListenerProvider $provider,
    EventSubscriberInterface $subscriber,
): void {
    foreach ($subscriber::getSubscribedEvents() as $eventClass => $config) {
        $method = is_array($config) ? $config['method'] : $config;
        $provider->addListener($eventClass, [$subscriber, $method]);
    }
}
```
