# Bridge Pattern Examples

## Report Bridge

**File:** `src/Domain/Report/ReportImplementorInterface.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Report;

interface ReportImplementorInterface
{
    public function generate(array $data): string;

    public function getExtension(): string;
}
```

**File:** `src/Domain/Report/AbstractReport.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Report;

abstract readonly class AbstractReport
{
    public function __construct(
        protected ReportImplementorInterface $implementor
    ) {}

    abstract public function create(array $data): string;
}
```

**File:** `src/Domain/Report/SalesReport.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Report;

final readonly class SalesReport extends AbstractReport
{
    public function create(array $data): string
    {
        $processedData = $this->calculateTotals($data);
        return $this->implementor->generate($processedData);
    }

    private function calculateTotals(array $data): array
    {
        $total = array_sum(array_column($data, 'amount'));
        return array_merge($data, ['total' => $total]);
    }
}
```

**File:** `src/Infrastructure/Report/PdfReportImplementor.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Report;

use Domain\Report\ReportImplementorInterface;
use Dompdf\Dompdf;

final readonly class PdfReportImplementor implements ReportImplementorInterface
{
    public function __construct(
        private Dompdf $pdf
    ) {}

    public function generate(array $data): string
    {
        $html = '<html><body>';
        $html .= '<h1>Sales Report</h1>';
        $html .= '<table border="1">';

        foreach ($data as $key => $value) {
            $html .= "<tr><td>{$key}</td><td>{$value}</td></tr>";
        }

        $html .= '</table></body></html>';

        $this->pdf->loadHtml($html);
        $this->pdf->render();

        return $this->pdf->output();
    }

    public function getExtension(): string
    {
        return 'pdf';
    }
}
```

**File:** `src/Infrastructure/Report/ExcelReportImplementor.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Report;

use Domain\Report\ReportImplementorInterface;
use PhpOffice\PhpSpreadsheet\Spreadsheet;
use PhpOffice\PhpSpreadsheet\Writer\Xlsx;

final readonly class ExcelReportImplementor implements ReportImplementorInterface
{
    public function generate(array $data): string
    {
        $spreadsheet = new Spreadsheet();
        $sheet = $spreadsheet->getActiveSheet();

        $row = 1;
        foreach ($data as $key => $value) {
            $sheet->setCellValue("A{$row}", $key);
            $sheet->setCellValue("B{$row}", $value);
            $row++;
        }

        $writer = new Xlsx($spreadsheet);

        ob_start();
        $writer->save('php://output');
        return ob_get_clean();
    }

    public function getExtension(): string
    {
        return 'xlsx';
    }
}
```

---

## Payment Bridge

**File:** `src/Domain/Payment/PaymentImplementorInterface.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Payment;

use Domain\Payment\ValueObject\Amount;
use Domain\Payment\ValueObject\PaymentToken;
use Domain\Payment\ValueObject\TransactionId;

interface PaymentImplementorInterface
{
    public function processCharge(Amount $amount, PaymentToken $token): TransactionId;

    public function processRefund(TransactionId $id, Amount $amount): void;
}
```

**File:** `src/Domain/Payment/AbstractPayment.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Payment;

use Domain\Payment\ValueObject\Amount;
use Domain\Payment\ValueObject\PaymentToken;
use Domain\Payment\ValueObject\TransactionId;

abstract readonly class AbstractPayment
{
    public function __construct(
        protected PaymentImplementorInterface $implementor
    ) {}

    abstract public function charge(Amount $amount, PaymentToken $token): TransactionId;

    abstract public function refund(TransactionId $id, Amount $amount): void;
}
```

**File:** `src/Domain/Payment/CreditCardPayment.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Payment;

use Domain\Payment\ValueObject\Amount;
use Domain\Payment\ValueObject\PaymentToken;
use Domain\Payment\ValueObject\TransactionId;

final readonly class CreditCardPayment extends AbstractPayment
{
    public function charge(Amount $amount, PaymentToken $token): TransactionId
    {
        $this->validateAmount($amount);
        return $this->implementor->processCharge($amount, $token);
    }

    public function refund(TransactionId $id, Amount $amount): void
    {
        $this->implementor->processRefund($id, $amount);
    }

    private function validateAmount(Amount $amount): void
    {
        if ($amount->isNegative()) {
            throw new \DomainException('Amount must be positive');
        }
    }
}
```

---

## Unit Tests

### SalesReportTest

**File:** `tests/Unit/Domain/Report/SalesReportTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\Report;

use Domain\Report\ReportImplementorInterface;
use Domain\Report\SalesReport;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(SalesReport::class)]
final class SalesReportTest extends TestCase
{
    public function testCreateDelegatesToImplementor(): void
    {
        $implementor = $this->createMock(ReportImplementorInterface::class);

        $data = [
            ['amount' => 100],
            ['amount' => 200],
        ];

        $implementor->expects($this->once())
            ->method('generate')
            ->willReturn('report content');

        $report = new SalesReport($implementor);

        $result = $report->create($data);

        self::assertSame('report content', $result);
    }

    public function testSwitchImplementor(): void
    {
        $pdfImplementor = $this->createMock(ReportImplementorInterface::class);
        $excelImplementor = $this->createMock(ReportImplementorInterface::class);

        $data = [['amount' => 100]];

        $pdfImplementor->method('generate')->willReturn('pdf content');
        $excelImplementor->method('generate')->willReturn('excel content');

        $pdfReport = new SalesReport($pdfImplementor);
        $excelReport = new SalesReport($excelImplementor);

        self::assertSame('pdf content', $pdfReport->create($data));
        self::assertSame('excel content', $excelReport->create($data));
    }
}
```
