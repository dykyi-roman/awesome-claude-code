# Adapter Pattern Templates

## Target Interface

**File:** `src/{architecture-path}/{Name}Interface.php`

```php
<?php

declare(strict_types=1);

namespace {BoundedContext};

interface {Name}Interface
{
    public function {operation}({params}): {returnType};
}
```

---

## Adapter

**File:** `src/{architecture-path}/Adapter/{Provider}{Name}Adapter.php`

```php
<?php

declare(strict_types=1);

namespace Adapter;

use {BoundedContext}\{Name}Interface;

final readonly class {Provider}{Name}Adapter implements {Name}Interface
{
    public function __construct(
        private {Adaptee} $adaptee
    ) {}

    public function {operation}({params}): {returnType}
    {
        {translateParams}

        $result = $this->adaptee->{adapteeMethod}({adapteeParams});

        {convertResult}

        return {returnValue};
    }
}
```

---

## Payment Gateway Interface

**File:** `src/{architecture-path}/PaymentGatewayInterface.php`

```php
<?php

declare(strict_types=1);

namespace Payment;

use ValueObject\Amount;
use ValueObject\PaymentToken;
use ValueObject\TransactionId;

interface PaymentGatewayInterface
{
    public function charge(Amount $amount, PaymentToken $token): TransactionId;

    public function refund(TransactionId $transactionId, Amount $amount): void;

    public function getStatus(TransactionId $transactionId): PaymentStatus;
}
```

---

## Stripe Adapter Template

**File:** `src/{architecture-path}/Adapter/StripePaymentGatewayAdapter.php`

```php
<?php

declare(strict_types=1);

namespace Adapter;

use Exception\PaymentException;
use Payment\PaymentGatewayInterface;
use Payment\PaymentStatus;
use ValueObject\Amount;
use ValueObject\PaymentToken;
use ValueObject\TransactionId;
use Stripe\StripeClient;

final readonly class StripePaymentGatewayAdapter implements PaymentGatewayInterface
{
    public function __construct(
        private StripeClient $stripe
    ) {}

    public function charge(Amount $amount, PaymentToken $token): TransactionId
    {
        try {
            $charge = $this->stripe->charges->create([
                'amount' => $amount->toCents(),
                'currency' => $amount->currency()->code(),
                'source' => $token->value(),
            ]);

            return new TransactionId($charge->id);
        } catch (\Stripe\Exception\ApiErrorException $e) {
            throw new PaymentException(
                message: 'Payment charge failed: ' . $e->getMessage(),
                previous: $e
            );
        }
    }

    public function refund(TransactionId $transactionId, Amount $amount): void
    {
        try {
            $this->stripe->refunds->create([
                'charge' => $transactionId->value(),
                'amount' => $amount->toCents(),
            ]);
        } catch (\Stripe\Exception\ApiErrorException $e) {
            throw new PaymentException(
                message: 'Payment refund failed: ' . $e->getMessage(),
                previous: $e
            );
        }
    }

    public function getStatus(TransactionId $transactionId): PaymentStatus
    {
        try {
            $charge = $this->stripe->charges->retrieve($transactionId->value());

            return match ($charge->status) {
                'succeeded' => PaymentStatus::Completed,
                'pending' => PaymentStatus::Pending,
                'failed' => PaymentStatus::Failed,
                default => PaymentStatus::Unknown,
            };
        } catch (\Stripe\Exception\ApiErrorException $e) {
            throw new PaymentException(
                message: 'Failed to retrieve payment status: ' . $e->getMessage(),
                previous: $e
            );
        }
    }
}
```

---

## Storage Interface

**File:** `src/{architecture-path}/StorageInterface.php`

```php
<?php

declare(strict_types=1);

namespace Storage;

interface StorageInterface
{
    public function store(string $path, string $contents): void;

    public function retrieve(string $path): string;

    public function delete(string $path): void;

    public function exists(string $path): bool;
}
```

---

## AWS S3 Adapter Template

**File:** `src/{architecture-path}/Adapter/S3StorageAdapter.php`

```php
<?php

declare(strict_types=1);

namespace Adapter;

use Aws\S3\S3Client;
use Exception\StorageException;
use Storage\StorageInterface;

final readonly class S3StorageAdapter implements StorageInterface
{
    public function __construct(
        private S3Client $s3Client,
        private string $bucket
    ) {}

    public function store(string $path, string $contents): void
    {
        try {
            $this->s3Client->putObject([
                'Bucket' => $this->bucket,
                'Key' => $path,
                'Body' => $contents,
            ]);
        } catch (\Aws\Exception\AwsException $e) {
            throw new StorageException(
                message: 'Failed to store file: ' . $e->getMessage(),
                previous: $e
            );
        }
    }

    public function retrieve(string $path): string
    {
        try {
            $result = $this->s3Client->getObject([
                'Bucket' => $this->bucket,
                'Key' => $path,
            ]);

            return (string) $result['Body'];
        } catch (\Aws\Exception\AwsException $e) {
            throw new StorageException(
                message: 'Failed to retrieve file: ' . $e->getMessage(),
                previous: $e
            );
        }
    }

    public function delete(string $path): void
    {
        try {
            $this->s3Client->deleteObject([
                'Bucket' => $this->bucket,
                'Key' => $path,
            ]);
        } catch (\Aws\Exception\AwsException $e) {
            throw new StorageException(
                message: 'Failed to delete file: ' . $e->getMessage(),
                previous: $e
            );
        }
    }

    public function exists(string $path): bool
    {
        try {
            return $this->s3Client->doesObjectExist($this->bucket, $path);
        } catch (\Aws\Exception\AwsException $e) {
            throw new StorageException(
                message: 'Failed to check file existence: ' . $e->getMessage(),
                previous: $e
            );
        }
    }
}
```
