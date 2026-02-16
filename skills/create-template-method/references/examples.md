# Template Method Pattern Examples

## Data Import Templates

### CsvDataImporterTemplate

**File:** `src/Domain/Import/Template/CsvDataImporterTemplate.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Import\Template;

use Domain\Import\ValueObject\ImportResult;
use Domain\Import\Exception\ImportValidationException;

final readonly class CsvDataImporterTemplate extends AbstractDataImporterTemplate
{
    private const DELIMITER = ',';
    private const ENCLOSURE = '"';
    private const ESCAPE = '\\';

    protected function parse(string $content): array
    {
        $lines = str_getcsv($content, "\n");
        $data = [];

        foreach ($lines as $line) {
            $row = str_getcsv($line, self::DELIMITER, self::ENCLOSURE, self::ESCAPE);
            if (!empty($row)) {
                $data[] = $row;
            }
        }

        return $data;
    }

    protected function normalize(array $data): array
    {
        if (empty($data)) {
            return [];
        }

        $headers = array_shift($data);
        $normalized = [];

        foreach ($data as $row) {
            if (count($row) === count($headers)) {
                $normalized[] = array_combine($headers, $row);
            }
        }

        return $normalized;
    }

    protected function getFormatName(): string
    {
        return 'CSV';
    }

    protected function validateFormat(string $content): void
    {
        parent::validateFormat($content);

        if (!str_contains($content, self::DELIMITER)) {
            throw new ImportValidationException('Invalid CSV format: no delimiter found');
        }
    }
}
```

---

### JsonDataImporterTemplate

**File:** `src/Domain/Import/Template/JsonDataImporterTemplate.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Import\Template;

use Domain\Import\Exception\ImportValidationException;

final readonly class JsonDataImporterTemplate extends AbstractDataImporterTemplate
{
    protected function parse(string $content): array
    {
        $data = json_decode($content, true);

        if (json_last_error() !== JSON_ERROR_NONE) {
            throw new ImportValidationException('Invalid JSON: ' . json_last_error_msg());
        }

        return is_array($data) ? $data : [$data];
    }

    protected function normalize(array $data): array
    {
        return array_map(
            fn(array $item): array => array_map('strval', $item),
            $data
        );
    }

    protected function getFormatName(): string
    {
        return 'JSON';
    }

    protected function validateFormat(string $content): void
    {
        parent::validateFormat($content);

        $trimmed = trim($content);
        if (!str_starts_with($trimmed, '{') && !str_starts_with($trimmed, '[')) {
            throw new ImportValidationException('Invalid JSON format');
        }
    }
}
```

---

### XmlDataImporterTemplate

**File:** `src/Domain/Import/Template/XmlDataImporterTemplate.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Import\Template;

use Domain\Import\Exception\ImportValidationException;

final readonly class XmlDataImporterTemplate extends AbstractDataImporterTemplate
{
    private const DEFAULT_ROOT = 'items';
    private const DEFAULT_ITEM = 'item';

    protected function parse(string $content): array
    {
        libxml_use_internal_errors(true);

        $xml = simplexml_load_string($content);

        if ($xml === false) {
            $errors = libxml_get_errors();
            libxml_clear_errors();

            throw new ImportValidationException('Invalid XML: ' . $errors[0]->message);
        }

        return json_decode(json_encode($xml), true);
    }

    protected function normalize(array $data): array
    {
        if (isset($data[self::DEFAULT_ITEM])) {
            $items = $data[self::DEFAULT_ITEM];

            return is_array($items) && isset($items[0]) ? $items : [$items];
        }

        return [$data];
    }

    protected function getFormatName(): string
    {
        return 'XML';
    }

    protected function validateFormat(string $content): void
    {
        parent::validateFormat($content);

        if (!str_starts_with(trim($content), '<?xml')) {
            throw new ImportValidationException('Invalid XML format: missing XML declaration');
        }
    }
}
```

---

## Report Generation Templates

### PdfReportGeneratorTemplate

**File:** `src/Application/Report/PdfReportGeneratorTemplate.php`

```php
<?php

declare(strict_types=1);

namespace Application\Report;

use Domain\Report\Template\AbstractReportGeneratorTemplate;
use Domain\Report\ValueObject\ReportData;

final readonly class PdfReportGeneratorTemplate extends AbstractReportGeneratorTemplate
{
    protected function generateHeader(ReportData $data): string
    {
        return sprintf(
            "%%PDF-1.4\n" .
            "Title: %s\n" .
            "Date: %s\n" .
            "---\n",
            $data->title(),
            $data->generatedAt()->format('Y-m-d H:i:s')
        );
    }

    protected function generateBody(ReportData $data): string
    {
        $body = '';

        foreach ($data->sections() as $section) {
            $body .= sprintf(
                "\nSection: %s\n%s\n",
                $section->title(),
                $section->content()
            );
        }

        return $body;
    }

    protected function generateFooter(ReportData $data): string
    {
        return sprintf(
            "\n---\nPage 1 of 1\nGenerated by %s\n",
            $data->author()
        );
    }

    protected function getFormat(): string
    {
        return 'PDF';
    }
}
```

---

### ExcelReportGeneratorTemplate

**File:** `src/Application/Report/ExcelReportGeneratorTemplate.php`

```php
<?php

declare(strict_types=1);

namespace Application\Report;

use Domain\Report\Template\AbstractReportGeneratorTemplate;
use Domain\Report\ValueObject\ReportData;

final readonly class ExcelReportGeneratorTemplate extends AbstractReportGeneratorTemplate
{
    protected function generateHeader(ReportData $data): string
    {
        return sprintf(
            "Title,%s\nDate,%s\n\n",
            $data->title(),
            $data->generatedAt()->format('Y-m-d')
        );
    }

    protected function generateBody(ReportData $data): string
    {
        $body = '';

        foreach ($data->sections() as $section) {
            $body .= sprintf("%s\n", $section->title());

            foreach ($section->rows() as $row) {
                $body .= implode(',', $row) . "\n";
            }

            $body .= "\n";
        }

        return $body;
    }

    protected function getFormat(): string
    {
        return 'Excel';
    }
}
```

---

## Order Processing Templates

### StandardOrderProcessorTemplate

**File:** `src/Domain/Order/Template/StandardOrderProcessorTemplate.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Order\Template;

use Domain\Order\Entity\Order;

final readonly class StandardOrderProcessorTemplate extends AbstractOrderProcessorTemplate
{
    private const STANDARD_SHIPPING_DAYS = 5;

    protected function calculatePricing(Order $order): void
    {
        // Standard pricing calculation
        $total = 0;

        foreach ($order->items() as $item) {
            $total += $item->price()->cents() * $item->quantity();
        }

        $order->setTotal($total);
    }

    protected function scheduleShipping(Order $order): void
    {
        $estimatedDelivery = (new \DateTimeImmutable())
            ->modify(sprintf('+%d days', self::STANDARD_SHIPPING_DAYS));

        $order->setEstimatedDelivery($estimatedDelivery);
    }

    protected function getProcessingType(): string
    {
        return 'standard';
    }
}
```

---

### ExpressOrderProcessorTemplate

**File:** `src/Domain/Order/Template/ExpressOrderProcessorTemplate.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Order\Template;

use Domain\Order\Entity\Order;

final readonly class ExpressOrderProcessorTemplate extends AbstractOrderProcessorTemplate
{
    private const EXPRESS_SHIPPING_DAYS = 1;
    private const EXPRESS_FEE_PERCENT = 20;

    protected function calculatePricing(Order $order): void
    {
        $subtotal = 0;

        foreach ($order->items() as $item) {
            $subtotal += $item->price()->cents() * $item->quantity();
        }

        $expressFee = (int) ($subtotal * self::EXPRESS_FEE_PERCENT / 100);
        $total = $subtotal + $expressFee;

        $order->setTotal($total);
    }

    protected function scheduleShipping(Order $order): void
    {
        $estimatedDelivery = (new \DateTimeImmutable())
            ->modify(sprintf('+%d day', self::EXPRESS_SHIPPING_DAYS));

        $order->setEstimatedDelivery($estimatedDelivery);
        $order->markAsExpressShipping();
    }

    protected function applyDiscounts(Order $order): void
    {
        // Express orders don't get discounts
    }

    protected function getProcessingType(): string
    {
        return 'express';
    }
}
```

---

### InternationalOrderProcessorTemplate

**File:** `src/Domain/Order/Template/InternationalOrderProcessorTemplate.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Order\Template;

use Domain\Order\Entity\Order;

final readonly class InternationalOrderProcessorTemplate extends AbstractOrderProcessorTemplate
{
    private const INTERNATIONAL_SHIPPING_DAYS = 14;
    private const CUSTOMS_FEE_PERCENT = 10;

    protected function calculatePricing(Order $order): void
    {
        $subtotal = 0;

        foreach ($order->items() as $item) {
            $subtotal += $item->price()->cents() * $item->quantity();
        }

        $customsFee = (int) ($subtotal * self::CUSTOMS_FEE_PERCENT / 100);
        $total = $subtotal + $customsFee;

        $order->setTotal($total);
        $order->setCustomsFee($customsFee);
    }

    protected function scheduleShipping(Order $order): void
    {
        $estimatedDelivery = (new \DateTimeImmutable())
            ->modify(sprintf('+%d days', self::INTERNATIONAL_SHIPPING_DAYS));

        $order->setEstimatedDelivery($estimatedDelivery);
        $order->markAsInternational();
    }

    protected function beforeProcessing(Order $order): void
    {
        $order->validateInternationalAddress();
    }

    protected function getProcessingType(): string
    {
        return 'international';
    }
}
```

---

## Unit Tests

### CsvDataImporterTemplateTest

**File:** `tests/Unit/Domain/Import/Template/CsvDataImporterTemplateTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\Import\Template;

use Domain\Import\Template\CsvDataImporterTemplate;
use Domain\Import\Exception\ImportValidationException;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(CsvDataImporterTemplate::class)]
final class CsvDataImporterTemplateTest extends TestCase
{
    private CsvDataImporterTemplate $importer;

    protected function setUp(): void
    {
        $this->importer = new CsvDataImporterTemplate();
    }

    public function testImportsCsvData(): void
    {
        $csv = "name,email,age\nJohn,john@example.com,30\nJane,jane@example.com,25";

        $result = $this->importer->execute($csv);

        self::assertSame(2, $result->imported());
        self::assertSame('CSV', $result->format());
    }

    public function testThrowsExceptionForEmptyContent(): void
    {
        $this->expectException(ImportValidationException::class);
        $this->expectExceptionMessage('Content cannot be empty');

        $this->importer->execute('');
    }

    public function testThrowsExceptionForInvalidFormat(): void
    {
        $this->expectException(ImportValidationException::class);
        $this->expectExceptionMessage('Invalid CSV format');

        $this->importer->execute('no delimiter here');
    }
}
```

---

### StandardOrderProcessorTemplateTest

**File:** `tests/Unit/Domain/Order/Template/StandardOrderProcessorTemplateTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\Order\Template;

use Domain\Order\Template\StandardOrderProcessorTemplate;
use Domain\Order\Entity\Order;
use Domain\Order\ValueObject\OrderItem;
use Domain\Shared\ValueObject\Money;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(StandardOrderProcessorTemplate::class)]
final class StandardOrderProcessorTemplateTest extends TestCase
{
    private StandardOrderProcessorTemplate $processor;

    protected function setUp(): void
    {
        $this->processor = new StandardOrderProcessorTemplate();
    }

    public function testProcessesStandardOrder(): void
    {
        $order = new Order(
            id: '123',
            items: [
                new OrderItem(price: Money::cents(1000), quantity: 2),
                new OrderItem(price: Money::cents(500), quantity: 1),
            ]
        );

        $result = $this->processor->process($order);

        self::assertSame('standard', $result->type());
        self::assertSame(2500, $order->total()->cents());
    }

    public function testSetsEstimatedDelivery(): void
    {
        $order = new Order(
            id: '123',
            items: [new OrderItem(price: Money::cents(1000), quantity: 1)]
        );

        $this->processor->process($order);

        $estimatedDays = $order->estimatedDelivery()->diff(new \DateTimeImmutable())->days;

        self::assertSame(5, $estimatedDays);
    }
}
```
