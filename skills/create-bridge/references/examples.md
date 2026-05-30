# Bridge Pattern Examples

## Report Bridge

**File:** `src/{architecture-path}/ReportImplementorInterface.php`

```php
<?php

declare(strict_types=1);

namespace Report;

interface ReportImplementorInterface
{
    public function generate(array $data): string;

    public function getExtension(): string;
}
```

**File:** `src/{architecture-path}/AbstractReport.php`

```php
<?php

declare(strict_types=1);

namespace Report;

abstract readonly class AbstractReport
{
    public function __construct(
        protected ReportImplementorInterface $implementor
    ) {}

    abstract public function create(array $data): string;
}
```

**File:** `src/{architecture-path}/SalesReport.php`

```php
<?php

declare(strict_types=1);

namespace Report;

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

**File:** `src/{architecture-path}/PdfReportImplementor.php`

```php
<?php

declare(strict_types=1);

namespace Report;

use Report\ReportImplementorInterface;
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

**File:** `src/{architecture-path}/ExcelReportImplementor.php`

```php
<?php

declare(strict_types=1);

namespace Report;

use Report\ReportImplementorInterface;
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

**File:** `src/{architecture-path}/PaymentImplementorInterface.php`

```php
<?php

declare(strict_types=1);

namespace Payment;

use ValueObject\Amount;
use ValueObject\PaymentToken;
use ValueObject\TransactionId;

interface PaymentImplementorInterface
{
    public function processCharge(Amount $amount, PaymentToken $token): TransactionId;

    public function processRefund(TransactionId $id, Amount $amount): void;
}
```

**File:** `src/{architecture-path}/AbstractPayment.php`

```php
<?php

declare(strict_types=1);

namespace Payment;

use ValueObject\Amount;
use ValueObject\PaymentToken;
use ValueObject\TransactionId;

abstract readonly class AbstractPayment
{
    public function __construct(
        protected PaymentImplementorInterface $implementor
    ) {}

    abstract public function charge(Amount $amount, PaymentToken $token): TransactionId;

    abstract public function refund(TransactionId $id, Amount $amount): void;
}
```

**File:** `src/{architecture-path}/CreditCardPayment.php`

```php
<?php

declare(strict_types=1);

namespace Payment;

use ValueObject\Amount;
use ValueObject\PaymentToken;
use ValueObject\TransactionId;

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

**File:** `tests/Unit/SalesReportTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Report;

use Report\ReportImplementorInterface;
use Report\SalesReport;
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
