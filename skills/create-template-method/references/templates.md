# Template Method Pattern Templates

## Abstract Template Class

**File:** `src/Domain/{BoundedContext}/Template/Abstract{Name}Template.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext}\Template;

abstract readonly class Abstract{Name}Template
{
    public function execute({InputType} $input): {OutputType}
    {
        $this->beforeExecution($input);
        $this->validate($input);

        $data = $this->extract($input);
        $transformed = $this->transform($data);
        $result = $this->load($transformed);

        $this->afterExecution($result);

        return $result;
    }

    abstract protected function extract({InputType} $input): array;

    abstract protected function transform(array $data): array;

    abstract protected function load(array $data): {OutputType};

    protected function validate({InputType} $input): void
    {
        // Default validation logic
    }

    protected function beforeExecution({InputType} $input): void
    {
        // Hook method - optional override
    }

    protected function afterExecution({OutputType} $result): void
    {
        // Hook method - optional override
    }
}
```

---

## Concrete Template Class

**File:** `src/Domain/{BoundedContext}/Template/{Variant}{Name}Template.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext}\Template;

final readonly class {Variant}{Name}Template extends Abstract{Name}Template
{
    protected function extract({InputType} $input): array
    {
        // Variant-specific extraction logic
    }

    protected function transform(array $data): array
    {
        // Variant-specific transformation logic
    }

    protected function load(array $data): {OutputType}
    {
        // Variant-specific loading logic
    }

    protected function validate({InputType} $input): void
    {
        parent::validate($input);

        // Additional variant-specific validation
    }
}
```

---

## Abstract Data Importer Template

**File:** `src/Domain/Import/Template/AbstractDataImporterTemplate.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Import\Template;

use Domain\Import\ValueObject\ImportResult;
use Domain\Import\Exception\ImportValidationException;

abstract readonly class AbstractDataImporterTemplate
{
    public function execute(string $content): ImportResult
    {
        $this->beforeImport($content);
        $this->validateFormat($content);

        $rawData = $this->parse($content);
        $this->validateData($rawData);

        $normalizedData = $this->normalize($rawData);
        $transformedData = $this->transform($normalizedData);

        $result = $this->import($transformedData);

        $this->afterImport($result);

        return $result;
    }

    abstract protected function parse(string $content): array;

    abstract protected function normalize(array $data): array;

    abstract protected function getFormatName(): string;

    protected function validateFormat(string $content): void
    {
        if (empty($content)) {
            throw new ImportValidationException('Content cannot be empty');
        }
    }

    protected function validateData(array $data): void
    {
        if (empty($data)) {
            throw new ImportValidationException('No data to import');
        }
    }

    protected function transform(array $data): array
    {
        return $data;
    }

    protected function import(array $data): ImportResult
    {
        return new ImportResult(
            imported: count($data),
            format: $this->getFormatName()
        );
    }

    protected function beforeImport(string $content): void
    {
        // Hook method - optional override
    }

    protected function afterImport(ImportResult $result): void
    {
        // Hook method - optional override
    }
}
```

---

## Abstract Report Generator Template

**File:** `src/Domain/Report/Template/AbstractReportGeneratorTemplate.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Report\Template;

use Domain\Report\ValueObject\ReportData;
use Domain\Report\ValueObject\GeneratedReport;

abstract readonly class AbstractReportGeneratorTemplate
{
    public function generate(ReportData $data): GeneratedReport
    {
        $this->beforeGeneration($data);

        $this->validateData($data);
        $header = $this->generateHeader($data);
        $body = $this->generateBody($data);
        $footer = $this->generateFooter($data);

        $content = $this->assembleContent($header, $body, $footer);
        $result = $this->finalize($content, $data);

        $this->afterGeneration($result);

        return $result;
    }

    abstract protected function generateHeader(ReportData $data): string;

    abstract protected function generateBody(ReportData $data): string;

    abstract protected function getFormat(): string;

    protected function validateData(ReportData $data): void
    {
        // Default validation
    }

    protected function generateFooter(ReportData $data): string
    {
        return '';
    }

    protected function assembleContent(string $header, string $body, string $footer): string
    {
        return $header . $body . $footer;
    }

    protected function finalize(string $content, ReportData $data): GeneratedReport
    {
        return new GeneratedReport(
            content: $content,
            format: $this->getFormat(),
            generatedAt: new \DateTimeImmutable()
        );
    }

    protected function beforeGeneration(ReportData $data): void
    {
        // Hook method - optional override
    }

    protected function afterGeneration(GeneratedReport $result): void
    {
        // Hook method - optional override
    }
}
```

---

## Abstract Order Processor Template

**File:** `src/Domain/Order/Template/AbstractOrderProcessorTemplate.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Order\Template;

use Domain\Order\Entity\Order;
use Domain\Order\ValueObject\ProcessingResult;

abstract readonly class AbstractOrderProcessorTemplate
{
    public function process(Order $order): ProcessingResult
    {
        $this->beforeProcessing($order);

        $this->validateOrder($order);
        $this->reserveInventory($order);
        $this->calculatePricing($order);
        $this->applyDiscounts($order);
        $this->processPayment($order);
        $this->scheduleShipping($order);

        $result = $this->finalizeOrder($order);

        $this->afterProcessing($result);

        return $result;
    }

    abstract protected function calculatePricing(Order $order): void;

    abstract protected function scheduleShipping(Order $order): void;

    abstract protected function getProcessingType(): string;

    protected function validateOrder(Order $order): void
    {
        // Default validation
    }

    protected function reserveInventory(Order $order): void
    {
        // Default inventory reservation
    }

    protected function applyDiscounts(Order $order): void
    {
        // Hook method - optional override
    }

    protected function processPayment(Order $order): void
    {
        // Default payment processing
    }

    protected function finalizeOrder(Order $order): ProcessingResult
    {
        return new ProcessingResult(
            orderId: $order->id(),
            type: $this->getProcessingType(),
            processedAt: new \DateTimeImmutable()
        );
    }

    protected function beforeProcessing(Order $order): void
    {
        // Hook method - optional override
    }

    protected function afterProcessing(ProcessingResult $result): void
    {
        // Hook method - optional override
    }
}
```
