# Facade Pattern Templates

## Generic Facade

**File:** `src/{architecture-path}/Facade/{Name}Facade.php`

```php
<?php

declare(strict_types=1);

namespace Facade;

final readonly class {Name}Facade
{
    public function __construct(
        private {SubsystemA}Interface $subsystemA,
        private {SubsystemB}Interface $subsystemB,
        private {SubsystemC}Interface $subsystemC
    ) {}

    public function {operation}({params}): {returnType}
    {
        $resultA = $this->subsystemA->{methodA}({paramsA});
        $resultB = $this->subsystemB->{methodB}($resultA);
        $resultC = $this->subsystemC->{methodC}($resultB);

        return $resultC;
    }
}
```

---

## Order Facade Template

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
            $command->productId,
            $command->quantity
        );

        $payment = $this->paymentService->charge(
            $command->amount,
            $command->paymentToken
        );

        $shipment = $this->shippingService->schedule(
            $command->shippingAddress,
            $command->productId,
            $command->quantity
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
        $this->paymentService->refund($order->paymentId(), $order->totalAmount());
        $this->inventoryRepository->release($order->items());

        $order->markAsCancelled();
        $this->orderRepository->save($order);

        $this->notificationService->sendOrderCancellation($order);
    }
}
```

---

## Notification Facade Template

**File:** `src/{architecture-path}/Facade/NotificationFacade.php`

```php
<?php

declare(strict_types=1);

namespace Facade;

use Notification\EmailServiceInterface;
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
        if ($recipient->hasEmail()) {
            $this->emailService->send(
                $recipient->email(),
                $message->subject(),
                $message->body()
            );
        }

        if ($recipient->hasPhone()) {
            $this->smsService->send(
                $recipient->phone(),
                $message->shortText()
            );
        }

        if ($recipient->hasPushToken()) {
            $this->pushService->send(
                $recipient->pushToken(),
                $message->title(),
                $message->body()
            );
        }
    }

    public function sendCriticalAlert(Recipient $recipient, Message $message): void
    {
        $this->emailService->sendUrgent($recipient->email(), $message);
        $this->smsService->sendUrgent($recipient->phone(), $message);
        $this->pushService->sendHighPriority($recipient->pushToken(), $message);
    }
}
```

---

## Report Facade Template

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

## Export Facade Template

**File:** `src/{architecture-path}/Facade/ExportFacade.php`

```php
<?php

declare(strict_types=1);

namespace Facade;

use Export\DataTransformerInterface;
use Enum\ExportFormat;
use Export\FormatterInterface;
use Export\QueryBuilderInterface;
use ValueObject\ExportCriteria;
use Storage\StorageInterface;

final readonly class ExportFacade
{
    public function __construct(
        private QueryBuilderInterface $queryBuilder,
        private DataTransformerInterface $dataTransformer,
        private FormatterInterface $formatter,
        private StorageInterface $storage
    ) {}

    public function export(ExportCriteria $criteria, ExportFormat $format): string
    {
        $query = $this->queryBuilder->build($criteria);

        $rawData = $query->execute();

        $transformedData = $this->dataTransformer->transform($rawData);

        $formatted = $this->formatter->format($transformedData, $format);

        $path = sprintf('exports/%s_%s.%s', $criteria->entityType(), time(), $format->value);

        $this->storage->store($path, $formatted);

        return $path;
    }
}
```
