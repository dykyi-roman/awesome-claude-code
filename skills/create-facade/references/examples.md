# Facade Pattern Examples

## Order Facade

**File:** `src/{architecture-path}/Facade/OrderFacade.php`

```php
<?php

declare(strict_types=1);

namespace Facade;

use Repository\InventoryRepositoryInterface;
use Notification\NotificationServiceInterface;
use Entity\Order;
use Repository\OrderRepositoryInterface;
use ValueObject\CreateOrderCommand;
use ValueObject\OrderId;
use Payment\PaymentServiceInterface;
use Shipping\ShippingServiceInterface;

final readonly class OrderFacade
{
    public function __construct(
        private InventoryRepositoryInterface $inventoryRepository,
        private PaymentServiceInterface $paymentService,
        private ShippingServiceInterface $shippingService,
        private OrderRepositoryInterface $orderRepository,
        private NotificationServiceInterface $notificationService
    ) {}

    public function placeOrder(CreateOrderCommand $command): Order
    {
        $inventory = $this->inventoryRepository->reserve(
            productId: $command->productId,
            quantity: $command->quantity
        );

        $payment = $this->paymentService->charge(
            amount: $command->amount,
            token: $command->paymentToken
        );

        $shipment = $this->shippingService->schedule(
            address: $command->shippingAddress,
            productId: $command->productId,
            quantity: $command->quantity
        );

        $order = Order::create(
            customerId: $command->customerId,
            items: $command->items,
            payment: $payment,
            shipment: $shipment
        );

        $this->orderRepository->save($order);

        $this->notificationService->sendOrderConfirmation($order);

        return $order;
    }

    public function cancelOrder(OrderId $orderId): void
    {
        $order = $this->orderRepository->findById($orderId);

        $this->shippingService->cancel($order->shipmentId());

        $this->paymentService->refund(
            transactionId: $order->paymentId(),
            amount: $order->totalAmount()
        );

        $this->inventoryRepository->release($order->items());

        $order->markAsCancelled();
        $this->orderRepository->save($order);

        $this->notificationService->sendOrderCancellation($order);
    }

    public function trackOrder(OrderId $orderId): array
    {
        $order = $this->orderRepository->findById($orderId);

        $shipmentStatus = $this->shippingService->getStatus($order->shipmentId());
        $paymentStatus = $this->paymentService->getStatus($order->paymentId());

        return [
            'order' => $order,
            'shipment' => $shipmentStatus,
            'payment' => $paymentStatus,
        ];
    }
}
```

---

## Notification Facade

**File:** `src/{architecture-path}/Facade/NotificationFacade.php`

```php
<?php

declare(strict_types=1);

namespace Facade;

use Notification\EmailServiceInterface;
use Exception\NotificationException;
use Notification\PushNotificationServiceInterface;
use Notification\SmsServiceInterface;
use ValueObject\Message;
use ValueObject\Recipient;

final readonly class NotificationFacade
{
    public function __construct(
        private EmailServiceInterface $emailService,
        private SmsServiceInterface $smsService,
        private PushNotificationServiceInterface $pushService
    ) {}

    public function sendMultiChannel(Recipient $recipient, Message $message): void
    {
        $failures = [];

        if ($recipient->hasEmail()) {
            try {
                $this->emailService->send(
                    to: $recipient->email(),
                    subject: $message->subject(),
                    body: $message->body()
                );
            } catch (\Throwable $e) {
                $failures[] = 'email: ' . $e->getMessage();
            }
        }

        if ($recipient->hasPhone()) {
            try {
                $this->smsService->send(
                    phone: $recipient->phone(),
                    text: $message->shortText()
                );
            } catch (\Throwable $e) {
                $failures[] = 'sms: ' . $e->getMessage();
            }
        }

        if ($recipient->hasPushToken()) {
            try {
                $this->pushService->send(
                    token: $recipient->pushToken(),
                    title: $message->title(),
                    body: $message->body()
                );
            } catch (\Throwable $e) {
                $failures[] = 'push: ' . $e->getMessage();
            }
        }

        if (count($failures) === 3) {
            throw new NotificationException(
                'All notification channels failed: ' . implode(', ', $failures)
            );
        }
    }

    public function sendCriticalAlert(Recipient $recipient, Message $message): void
    {
        $this->emailService->sendUrgent($recipient->email(), $message);
        $this->smsService->sendUrgent($recipient->phone(), $message);
        $this->pushService->sendHighPriority($recipient->pushToken(), $message);
    }

    public function sendBulk(array $recipients, Message $message): array
    {
        $results = [];

        foreach ($recipients as $recipient) {
            try {
                $this->sendMultiChannel($recipient, $message);
                $results[$recipient->id()] = 'success';
            } catch (\Throwable $e) {
                $results[$recipient->id()] = 'failed: ' . $e->getMessage();
            }
        }

        return $results;
    }
}
```

---

## Report Facade

**File:** `src/{architecture-path}/Facade/ReportFacade.php`

```php
<?php

declare(strict_types=1);

namespace Facade;

use Report\DataFetcherInterface;
use Enum\ReportFormat;
use ValueObject\ReportCriteria;
use Report\CsvGeneratorInterface;
use Report\ExcelGeneratorInterface;
use Report\PdfGeneratorInterface;
use Storage\StorageInterface;

final readonly class ReportFacade
{
    public function __construct(
        private DataFetcherInterface $dataFetcher,
        private PdfGeneratorInterface $pdfGenerator,
        private ExcelGeneratorInterface $excelGenerator,
        private CsvGeneratorInterface $csvGenerator,
        private StorageInterface $storage
    ) {}

    public function generate(ReportCriteria $criteria, ReportFormat $format): string
    {
        $data = $this->dataFetcher->fetch($criteria);

        $content = match ($format) {
            ReportFormat::Pdf => $this->pdfGenerator->generate($data),
            ReportFormat::Excel => $this->excelGenerator->generate($data),
            ReportFormat::Csv => $this->csvGenerator->generate($data),
        };

        $filename = $this->buildFilename($criteria, $format);

        $this->storage->store($filename, $content);

        return $filename;
    }

    public function generateAndEmail(
        ReportCriteria $criteria,
        ReportFormat $format,
        string $recipientEmail
    ): void {
        $filename = $this->generate($criteria, $format);

        $fileUrl = $this->storage->getPublicUrl($filename);

        $this->emailService->send(
            to: $recipientEmail,
            subject: 'Report: ' . $criteria->reportType(),
            body: "Your report is ready: {$fileUrl}"
        );
    }

    private function buildFilename(ReportCriteria $criteria, ReportFormat $format): string
    {
        return sprintf(
            'reports/%s_%s.%s',
            $criteria->reportType(),
            date('Y-m-d_His'),
            $format->extension()
        );
    }
}
```

---

## User Registration Facade

**File:** `src/{architecture-path}/Facade/UserRegistrationFacade.php`

```php
<?php

declare(strict_types=1);

namespace Facade;

use Notification\NotificationServiceInterface;
use Entity\User;
use Repository\UserRepositoryInterface;
use Service\PasswordHasherInterface;
use ValueObject\Email;
use ValueObject\RegistrationCommand;
use Security\TokenGeneratorInterface;

final readonly class UserRegistrationFacade
{
    public function __construct(
        private UserRepositoryInterface $userRepository,
        private PasswordHasherInterface $passwordHasher,
        private TokenGeneratorInterface $tokenGenerator,
        private NotificationServiceInterface $notificationService
    ) {}

    public function register(RegistrationCommand $command): User
    {
        $existingUser = $this->userRepository->findByEmail($command->email);

        if ($existingUser !== null) {
            throw new \DomainException('User already exists');
        }

        $hashedPassword = $this->passwordHasher->hash($command->password);

        $verificationToken = $this->tokenGenerator->generate();

        $user = User::create(
            email: $command->email,
            hashedPassword: $hashedPassword,
            name: $command->name,
            verificationToken: $verificationToken
        );

        $this->userRepository->save($user);

        $this->notificationService->sendWelcomeEmail(
            recipient: $command->email,
            name: $command->name,
            verificationToken: $verificationToken
        );

        return $user;
    }

    public function verifyEmail(string $token): void
    {
        $user = $this->userRepository->findByVerificationToken($token);

        if ($user === null) {
            throw new \DomainException('Invalid verification token');
        }

        $user->markAsVerified();

        $this->userRepository->save($user);

        $this->notificationService->sendEmailVerifiedConfirmation($user->email());
    }
}
```

---

## Unit Tests

### OrderFacadeTest

**File:** `tests/Unit/Facade/OrderFacadeTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Facade;

use Facade\OrderFacade;
use Repository\InventoryRepositoryInterface;
use Notification\NotificationServiceInterface;
use Entity\Order;
use Repository\OrderRepositoryInterface;
use ValueObject\CreateOrderCommand;
use Payment\PaymentServiceInterface;
use Shipping\ShippingServiceInterface;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(OrderFacade::class)]
final class OrderFacadeTest extends TestCase
{
    public function testPlaceOrderCoordinatesAllSubsystems(): void
    {
        $inventoryRepository = $this->createMock(InventoryRepositoryInterface::class);
        $paymentService = $this->createMock(PaymentServiceInterface::class);
        $shippingService = $this->createMock(ShippingServiceInterface::class);
        $orderRepository = $this->createMock(OrderRepositoryInterface::class);
        $notificationService = $this->createMock(NotificationServiceInterface::class);

        $command = $this->createCommand();

        $inventoryRepository->expects($this->once())
            ->method('reserve');

        $paymentService->expects($this->once())
            ->method('charge');

        $shippingService->expects($this->once())
            ->method('schedule');

        $orderRepository->expects($this->once())
            ->method('save');

        $notificationService->expects($this->once())
            ->method('sendOrderConfirmation');

        $facade = new OrderFacade(
            $inventoryRepository,
            $paymentService,
            $shippingService,
            $orderRepository,
            $notificationService
        );

        $order = $facade->placeOrder($command);

        self::assertInstanceOf(Order::class, $order);
    }

    public function testCancelOrderRevertsAllOperations(): void
    {
        $inventoryRepository = $this->createMock(InventoryRepositoryInterface::class);
        $paymentService = $this->createMock(PaymentServiceInterface::class);
        $shippingService = $this->createMock(ShippingServiceInterface::class);
        $orderRepository = $this->createMock(OrderRepositoryInterface::class);
        $notificationService = $this->createMock(NotificationServiceInterface::class);

        $order = $this->createOrder();

        $orderRepository->expects($this->once())
            ->method('findById')
            ->willReturn($order);

        $shippingService->expects($this->once())
            ->method('cancel');

        $paymentService->expects($this->once())
            ->method('refund');

        $inventoryRepository->expects($this->once())
            ->method('release');

        $orderRepository->expects($this->once())
            ->method('save');

        $notificationService->expects($this->once())
            ->method('sendOrderCancellation');

        $facade = new OrderFacade(
            $inventoryRepository,
            $paymentService,
            $shippingService,
            $orderRepository,
            $notificationService
        );

        $facade->cancelOrder($order->id());

        $this->expectNotToPerformAssertions();
    }
}
```

---

### NotificationFacadeTest

**File:** `tests/Unit/Facade/NotificationFacadeTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Facade;

use Facade\NotificationFacade;
use Notification\EmailServiceInterface;
use Notification\PushNotificationServiceInterface;
use Notification\SmsServiceInterface;
use ValueObject\Message;
use ValueObject\Recipient;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(NotificationFacade::class)]
final class NotificationFacadeTest extends TestCase
{
    public function testSendMultiChannelCallsAllServices(): void
    {
        $emailService = $this->createMock(EmailServiceInterface::class);
        $smsService = $this->createMock(SmsServiceInterface::class);
        $pushService = $this->createMock(PushNotificationServiceInterface::class);

        $recipient = $this->createRecipientWithAllChannels();
        $message = $this->createMessage();

        $emailService->expects($this->once())
            ->method('send');

        $smsService->expects($this->once())
            ->method('send');

        $pushService->expects($this->once())
            ->method('send');

        $facade = new NotificationFacade($emailService, $smsService, $pushService);

        $facade->sendMultiChannel($recipient, $message);

        $this->expectNotToPerformAssertions();
    }

    public function testSendMultiChannelSkipsUnavailableChannels(): void
    {
        $emailService = $this->createMock(EmailServiceInterface::class);
        $smsService = $this->createMock(SmsServiceInterface::class);
        $pushService = $this->createMock(PushNotificationServiceInterface::class);

        $recipient = $this->createRecipientWithEmailOnly();
        $message = $this->createMessage();

        $emailService->expects($this->once())
            ->method('send');

        $smsService->expects($this->never())
            ->method('send');

        $pushService->expects($this->never())
            ->method('send');

        $facade = new NotificationFacade($emailService, $smsService, $pushService);

        $facade->sendMultiChannel($recipient, $message);

        $this->expectNotToPerformAssertions();
    }
}
```
