# Mediator Pattern Templates

## Concrete Mediator (Order Workflow)

```php
<?php

declare(strict_types=1);

namespace App\{Context}\Application\Mediator;

use App\{Context}\Application\Mediator\Colleague\ColleagueInterface;
use App\{Context}\Application\Mediator\Colleague\{Colleague1};
use App\{Context}\Application\Mediator\Colleague\{Colleague2};
use App\{Context}\Application\Mediator\Colleague\{Colleague3};

final class {Name}MediatorImpl implements {Name}Mediator
{
    /** @var array<string, ColleagueInterface> */
    private array $colleagues = [];

    public function register(ColleagueInterface $colleague): void
    {
        $this->colleagues[$colleague->getName()] = $colleague;
        $colleague->setMediator($this);
    }

    public function notify(ColleagueInterface $sender, string $event, mixed $data = null): void
    {
        match ($event) {
            'order_placed' => $this->onOrderPlaced($sender, $data),
            'payment_received' => $this->onPaymentReceived($sender, $data),
            'inventory_reserved' => $this->onInventoryReserved($sender, $data),
            'shipment_created' => $this->onShipmentCreated($sender, $data),
            default => null,
        };
    }

    public function send(string $request, mixed $data = null): mixed
    {
        return match ($request) {
            'check_inventory' => $this->getColleague('inventory')->handle($data),
            'process_payment' => $this->getColleague('payment')->handle($data),
            'create_shipment' => $this->getColleague('shipping')->handle($data),
            default => throw new UnknownRequestException($request),
        };
    }

    private function onOrderPlaced(ColleagueInterface $sender, mixed $data): void
    {
        $inventoryResult = $this->getColleague('inventory')->handle([
            'action' => 'reserve',
            'order' => $data,
        ]);

        if ($inventoryResult->isSuccess()) {
            $this->getColleague('payment')->handle([
                'action' => 'charge',
                'order' => $data,
            ]);
        }
    }

    private function onPaymentReceived(ColleagueInterface $sender, mixed $data): void
    {
        $this->getColleague('shipping')->handle([
            'action' => 'create',
            'order' => $data['order'],
            'transaction' => $data['transaction'],
        ]);

        $this->getColleague('notification')->handle([
            'action' => 'send',
            'template' => 'order_confirmed',
            'recipient' => $data['order']->customerId,
        ]);
    }

    private function onInventoryReserved(ColleagueInterface $sender, mixed $data): void
    {
        // Inventory reserved, continue workflow
    }

    private function onShipmentCreated(ColleagueInterface $sender, mixed $data): void
    {
        $this->getColleague('notification')->handle([
            'action' => 'send',
            'template' => 'order_shipped',
            'recipient' => $data['order']->customerId,
            'tracking' => $data['tracking'],
        ]);
    }

    private function getColleague(string $name): ColleagueInterface
    {
        if (!isset($this->colleagues[$name])) {
            throw new ColleagueNotFoundException($name);
        }

        return $this->colleagues[$name];
    }
}
```

## Concrete Colleague

```php
<?php

declare(strict_types=1);

namespace App\{Context}\Application\Mediator\Colleague;

final class InventoryColleague extends AbstractColleague
{
    public function __construct(
        private readonly InventoryService $inventoryService,
    ) {}

    public function getName(): string
    {
        return 'inventory';
    }

    public function handle(mixed $data): InventoryResult
    {
        return match ($data['action']) {
            'reserve' => $this->reserve($data['order']),
            'release' => $this->release($data['order']),
            'check' => $this->check($data['products']),
            default => throw new UnknownActionException($data['action']),
        };
    }

    private function reserve(Order $order): InventoryResult
    {
        $result = $this->inventoryService->reserve($order);

        if ($result->isSuccess()) {
            $this->notify('inventory_reserved', [
                'order' => $order,
                'reservation' => $result->reservation,
            ]);
        }

        return $result;
    }

    private function release(Order $order): InventoryResult
    {
        return $this->inventoryService->release($order);
    }

    private function check(array $products): InventoryResult
    {
        return $this->inventoryService->checkAvailability($products);
    }
}
```

## Command Bus Mediator

```php
<?php

declare(strict_types=1);

namespace App\Shared\Application\Bus;

interface CommandBus
{
    public function dispatch(Command $command): mixed;
}

final class SyncCommandBus implements CommandBus
{
    /** @var array<class-string<Command>, callable> */
    private array $handlers = [];

    public function register(string $commandClass, callable $handler): void
    {
        $this->handlers[$commandClass] = $handler;
    }

    public function dispatch(Command $command): mixed
    {
        $commandClass = get_class($command);

        if (!isset($this->handlers[$commandClass])) {
            throw new NoHandlerException($commandClass);
        }

        return ($this->handlers[$commandClass])($command);
    }
}
```

## Event Mediator

```php
<?php

declare(strict_types=1);

namespace App\Shared\Application\Event;

interface EventMediator
{
    public function publish(DomainEvent $event): void;
    public function subscribe(string $eventClass, callable $handler): void;
}

final class SyncEventMediator implements EventMediator
{
    /** @var array<string, array<callable>> */
    private array $handlers = [];

    public function subscribe(string $eventClass, callable $handler): void
    {
        $this->handlers[$eventClass][] = $handler;
    }

    public function publish(DomainEvent $event): void
    {
        $eventClass = get_class($event);

        foreach ($this->handlers[$eventClass] ?? [] as $handler) {
            $handler($event);
        }

        foreach (class_parents($event) as $parent) {
            foreach ($this->handlers[$parent] ?? [] as $handler) {
                $handler($event);
            }
        }
    }
}
```

## Chat Room Mediator

```php
<?php

declare(strict_types=1);

namespace App\Chat\Application\Mediator;

final class ChatRoomMediator implements ChatMediator
{
    /** @var array<string, UserColleague> */
    private array $users = [];

    public function register(UserColleague $user): void
    {
        $this->users[$user->getName()] = $user;
        $user->setMediator($this);
    }

    public function sendMessage(UserColleague $sender, string $message): void
    {
        foreach ($this->users as $user) {
            if ($user !== $sender) {
                $user->receive($sender->getName(), $message);
            }
        }
    }

    public function sendPrivateMessage(
        UserColleague $sender,
        string $recipient,
        string $message,
    ): void {
        if (!isset($this->users[$recipient])) {
            throw new UserNotFoundException($recipient);
        }

        $this->users[$recipient]->receive($sender->getName(), $message);
    }
}
```

## Unit Test Template

```php
<?php

declare(strict_types=1);

namespace Tests\{Context}\Application\Mediator;

use App\{Context}\Application\Mediator\{Name}Mediator;
use App\{Context}\Application\Mediator\{Name}MediatorImpl;
use App\{Context}\Application\Mediator\Colleague\InventoryColleague;
use App\{Context}\Application\Mediator\Colleague\PaymentColleague;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass({Name}MediatorImpl::class)]
final class {Name}MediatorTest extends TestCase
{
    private {Name}Mediator $mediator;
    private InventoryColleague $inventory;
    private PaymentColleague $payment;

    protected function setUp(): void
    {
        $this->mediator = new {Name}MediatorImpl();

        $this->inventory = new InventoryColleague(
            $this->createMock(InventoryService::class),
        );

        $this->payment = new PaymentColleague(
            $this->createMock(PaymentGateway::class),
        );

        $this->mediator->register($this->inventory);
        $this->mediator->register($this->payment);
    }

    public function testRegistersColleagues(): void
    {
        $colleague = $this->createMock(ColleagueInterface::class);
        $colleague->method('getName')->willReturn('test');

        $this->mediator->register($colleague);

        $colleague->expects($this->once())
            ->method('setMediator')
            ->with($this->mediator);
    }

    public function testNotifiesColleaguesOnEvent(): void
    {
        $order = $this->createMock(Order::class);

        $this->inventory->expects($this->once())
            ->method('handle')
            ->with($this->callback(function ($data) use ($order) {
                return $data['action'] === 'reserve'
                    && $data['order'] === $order;
            }));

        $this->mediator->notify($this->inventory, 'order_placed', $order);
    }

    public function testSendsDelegatesRequestToCorrectColleague(): void
    {
        $expectedResult = new InventoryResult(true);

        $this->inventory->expects($this->once())
            ->method('handle')
            ->willReturn($expectedResult);

        $result = $this->mediator->send('check_inventory', ['products' => []]);

        $this->assertSame($expectedResult, $result);
    }

    public function testThrowsOnUnknownRequest(): void
    {
        $this->expectException(UnknownRequestException::class);

        $this->mediator->send('unknown_request');
    }
}
```

## Form Mediator

```php
<?php

declare(strict_types=1);

namespace App\Shared\Infrastructure\Form;

/**
 * Mediator for form field interactions.
 */
final class FormMediator implements FormMediatorInterface
{
    /** @var array<string, FormFieldInterface> */
    private array $fields = [];

    public function register(FormFieldInterface $field): void
    {
        $this->fields[$field->getName()] = $field;
        $field->setMediator($this);
    }

    public function notify(FormFieldInterface $sender, string $event, mixed $data = null): void
    {
        match ($event) {
            'value_changed' => $this->onValueChanged($sender, $data),
            'validation_failed' => $this->onValidationFailed($sender, $data),
            'focus_lost' => $this->onFocusLost($sender),
            default => null,
        };
    }

    private function onValueChanged(FormFieldInterface $sender, mixed $value): void
    {
        // Update dependent fields
        if ($sender->getName() === 'country') {
            $this->fields['state']?->updateOptions(
                $this->getStatesForCountry($value),
            );
            $this->fields['city']?->clear();
        }

        if ($sender->getName() === 'shipping_same_as_billing') {
            if ($value === true) {
                $this->copyBillingToShipping();
            }
        }
    }

    private function onValidationFailed(FormFieldInterface $sender, array $errors): void
    {
        // Highlight related fields
        $this->fields['submit']?->disable();
    }

    private function onFocusLost(FormFieldInterface $sender): void
    {
        // Trigger field validation
        $sender->validate();
    }

    private function copyBillingToShipping(): void
    {
        $billingFields = ['street', 'city', 'state', 'zip', 'country'];

        foreach ($billingFields as $field) {
            $billingValue = $this->fields["billing_$field"]?->getValue();
            $this->fields["shipping_$field"]?->setValue($billingValue);
        }
    }

    private function getStatesForCountry(string $country): array
    {
        // Return states for country
        return [];
    }
}
```

## Workflow Mediator

```php
<?php

declare(strict_types=1);

namespace App\Workflow\Application\Mediator;

/**
 * Mediator for workflow step coordination.
 */
final class WorkflowMediator implements WorkflowMediatorInterface
{
    /** @var array<string, WorkflowStepInterface> */
    private array $steps = [];

    private ?string $currentStep = null;

    public function register(WorkflowStepInterface $step): void
    {
        $this->steps[$step->getName()] = $step;
        $step->setMediator($this);
    }

    public function start(string $firstStep): void
    {
        if (!isset($this->steps[$firstStep])) {
            throw new StepNotFoundException($firstStep);
        }

        $this->currentStep = $firstStep;
        $this->steps[$firstStep]->enter();
    }

    public function notify(WorkflowStepInterface $sender, string $event, mixed $data = null): void
    {
        match ($event) {
            'completed' => $this->onStepCompleted($sender, $data),
            'failed' => $this->onStepFailed($sender, $data),
            'cancelled' => $this->onStepCancelled($sender),
            default => null,
        };
    }

    private function onStepCompleted(WorkflowStepInterface $step, mixed $result): void
    {
        $nextStep = $step->getNextStep($result);

        if ($nextStep === null) {
            // Workflow completed
            $this->onWorkflowCompleted($result);
            return;
        }

        if (!isset($this->steps[$nextStep])) {
            throw new StepNotFoundException($nextStep);
        }

        $step->exit();
        $this->currentStep = $nextStep;
        $this->steps[$nextStep]->enter($result);
    }

    private function onStepFailed(WorkflowStepInterface $step, \Throwable $error): void
    {
        // Handle failure - retry, compensate, or abort
        $compensation = $step->getCompensation();

        if ($compensation !== null && isset($this->steps[$compensation])) {
            $this->steps[$compensation]->enter(['error' => $error]);
        }
    }

    private function onStepCancelled(WorkflowStepInterface $step): void
    {
        // Roll back workflow
        $this->rollback($step);
    }

    private function onWorkflowCompleted(mixed $result): void
    {
        // Notify completion
    }

    private function rollback(WorkflowStepInterface $fromStep): void
    {
        // Execute compensations in reverse order
    }
}
```

## Notification Hub Mediator

```php
<?php

declare(strict_types=1);

namespace App\Notification\Application\Mediator;

/**
 * Mediator for notification channel coordination.
 */
final class NotificationHubMediator implements NotificationMediator
{
    /** @var array<string, NotificationChannel> */
    private array $channels = [];

    /** @var array<string, array<string>> */
    private array $preferences = [];

    public function register(NotificationChannel $channel): void
    {
        $this->channels[$channel->getName()] = $channel;
        $channel->setMediator($this);
    }

    public function setUserPreferences(string $userId, array $channels): void
    {
        $this->preferences[$userId] = $channels;
    }

    public function send(Notification $notification): void
    {
        $channels = $this->getChannelsForUser($notification->recipientId);

        foreach ($channels as $channelName) {
            $channel = $this->channels[$channelName] ?? null;

            if ($channel === null) {
                continue;
            }

            if (!$channel->supports($notification)) {
                continue;
            }

            try {
                $channel->send($notification);
            } catch (ChannelException $e) {
                $this->onChannelFailed($channel, $notification, $e);
            }
        }
    }

    public function notify(NotificationChannel $sender, string $event, mixed $data = null): void
    {
        match ($event) {
            'sent' => $this->onNotificationSent($sender, $data),
            'failed' => $this->onNotificationFailed($sender, $data),
            'bounced' => $this->onNotificationBounced($sender, $data),
            default => null,
        };
    }

    private function getChannelsForUser(string $userId): array
    {
        return $this->preferences[$userId] ?? ['email'];
    }

    private function onChannelFailed(
        NotificationChannel $channel,
        Notification $notification,
        ChannelException $error,
    ): void {
        // Try fallback channel
        $fallback = $channel->getFallback();

        if ($fallback !== null && isset($this->channels[$fallback])) {
            $this->channels[$fallback]->send($notification);
        }
    }

    private function onNotificationSent(NotificationChannel $channel, mixed $data): void
    {
        // Log successful delivery
    }

    private function onNotificationFailed(NotificationChannel $channel, mixed $data): void
    {
        // Handle failure
    }

    private function onNotificationBounced(NotificationChannel $channel, mixed $data): void
    {
        // Update user preferences
    }
}
```

## Dialog Mediator

```php
<?php

declare(strict_types=1);

namespace App\Shared\Infrastructure\Dialog;

/**
 * Mediator for dialog component interactions.
 */
final class DialogMediator implements DialogMediatorInterface
{
    private ?DialogInterface $currentDialog = null;

    /** @var array<string, DialogInterface> */
    private array $dialogs = [];

    public function register(DialogInterface $dialog): void
    {
        $this->dialogs[$dialog->getName()] = $dialog;
        $dialog->setMediator($this);
    }

    public function show(string $dialogName, array $data = []): void
    {
        if ($this->currentDialog !== null) {
            $this->currentDialog->hide();
        }

        if (!isset($this->dialogs[$dialogName])) {
            throw new DialogNotFoundException($dialogName);
        }

        $this->currentDialog = $this->dialogs[$dialogName];
        $this->currentDialog->show($data);
    }

    public function notify(DialogInterface $sender, string $event, mixed $data = null): void
    {
        match ($event) {
            'confirmed' => $this->onConfirmed($sender, $data),
            'cancelled' => $this->onCancelled($sender),
            'closed' => $this->onClosed($sender),
            default => null,
        };
    }

    private function onConfirmed(DialogInterface $dialog, mixed $result): void
    {
        $dialog->hide();
        $this->currentDialog = null;

        // Handle confirmation result
    }

    private function onCancelled(DialogInterface $dialog): void
    {
        $dialog->hide();
        $this->currentDialog = null;
    }

    private function onClosed(DialogInterface $dialog): void
    {
        $this->currentDialog = null;
    }
}
```

## Game Object Mediator

```php
<?php

declare(strict_types=1);

namespace App\Game\Application\Mediator;

/**
 * Mediator for game object interactions.
 */
final class GameWorldMediator implements GameMediator
{
    /** @var array<string, GameObjectInterface> */
    private array $objects = [];

    public function register(GameObjectInterface $object): void
    {
        $this->objects[$object->getId()] = $object;
        $object->setMediator($this);
    }

    public function notify(GameObjectInterface $sender, string $event, mixed $data = null): void
    {
        match ($event) {
            'collision' => $this->onCollision($sender, $data),
            'damage' => $this->onDamage($sender, $data),
            'death' => $this->onDeath($sender),
            'item_pickup' => $this->onItemPickup($sender, $data),
            default => null,
        };
    }

    private function onCollision(GameObjectInterface $object, CollisionData $data): void
    {
        $other = $this->objects[$data->otherId] ?? null;

        if ($other === null) {
            return;
        }

        // Handle collision between objects
        if ($object instanceof Player && $other instanceof Enemy) {
            $object->takeDamage($other->getContactDamage());
        }

        if ($object instanceof Projectile && $other instanceof Enemy) {
            $other->takeDamage($object->getDamage());
            $this->unregister($object);
        }
    }

    private function onDamage(GameObjectInterface $object, DamageData $data): void
    {
        // Update UI, play effects
    }

    private function onDeath(GameObjectInterface $object): void
    {
        $this->unregister($object);

        if ($object instanceof Player) {
            $this->onGameOver();
        }

        if ($object instanceof Enemy) {
            $this->spawnLoot($object->getPosition());
        }
    }

    private function onItemPickup(GameObjectInterface $object, ItemData $data): void
    {
        if ($object instanceof Player) {
            $object->addToInventory($data->item);
            $this->unregister($this->objects[$data->itemId]);
        }
    }

    private function unregister(GameObjectInterface $object): void
    {
        unset($this->objects[$object->getId()]);
    }

    private function onGameOver(): void
    {
        // Handle game over
    }

    private function spawnLoot(Position $position): void
    {
        // Spawn loot items
    }
}
```
