# Persistence Layer

Detailed patterns for Eloquent ORM, migrations, transactions, and database strategies in Laravel.

## Eloquent ORM: Models, Relationships, Scopes

### Clean Eloquent Model

```php
<?php

declare(strict_types=1);

namespace Model;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;
use Illuminate\Database\Eloquent\Builder;

final class OrderModel extends Model
{
    use HasUuids;

    protected $table = 'orders';
    protected $fillable = ['id', 'customer_id', 'status', 'total_cents', 'currency'];

    /** @return BelongsTo<CustomerModel, self> */
    public function customer(): BelongsTo
    {
        return $this->belongsTo(CustomerModel::class, 'customer_id');
    }

    /** @return HasMany<OrderLineModel> */
    public function lines(): HasMany
    {
        return $this->hasMany(OrderLineModel::class, 'order_id');
    }

    /** @param Builder<self> $query */
    public function scopeConfirmed(Builder $query): void
    {
        $query->where('status', 'confirmed');
    }

    /** @param Builder<self> $query */
    public function scopeForCustomer(Builder $query, string $customerId): void
    {
        $query->where('customer_id', $customerId);
    }
}
```

### Detection Patterns

```bash
# Models with business logic (should be in Domain)
Grep: "public function (calculate|validate|process|approve|reject|verify)" --glob "**/Models/**/*.php"

# Oversized models (God Model risk)
Grep: "class.*extends Model" --glob "**/*.php"

# Models without strict types
Grep: "class.*extends Model" --glob "**/*.php" -B 5
```

## Migration Best Practices

### Proper Migration

```php
<?php

declare(strict_types=1);

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('orders', static function (Blueprint $table): void {
            $table->uuid('id')->primary();
            $table->uuid('customer_id');
            $table->string('status', 32)->default('draft');
            $table->bigInteger('total_cents')->default(0);
            $table->string('currency', 3)->default('USD');
            $table->timestamps();

            $table->foreign('customer_id')
                ->references('id')
                ->on('customers')
                ->cascadeOnDelete();

            $table->index(['customer_id', 'status']);
            $table->index('created_at');
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('orders');
    }
};
```

### Migration Rules

| Rule | Reason |
|------|--------|
| Always define `down()` | Rollback support |
| Use UUID primary keys | Distributed-friendly |
| Add foreign keys | Referential integrity |
| Add indexes for query patterns | Performance |
| Use `bigInteger` for money | Avoid floating point |
| String columns with max length | Prevent data overflow |

## Database Transactions

### Transaction in Repository

```php
<?php

declare(strict_types=1);

namespace Persistence\Eloquent;

use Entity\Order;
use Illuminate\Support\Facades\DB;

final readonly class EloquentOrderRepository implements OrderRepositoryInterface
{
    public function save(Order $order): void
    {
        DB::transaction(function () use ($order): void {
            $data = $this->mapper->toPersistence($order);

            OrderModel::updateOrCreate(
                ['id' => $data['id']],
                $data,
            );

            foreach ($order->lines() as $line) {
                OrderLineModel::updateOrCreate(
                    ['id' => $line->id()->value()],
                    $this->lineMapper->toPersistence($line),
                );
            }
        });
    }
}
```

### Transaction at Application Layer

```php
<?php

declare(strict_types=1);

namespace UseCase;

use Repository\OrderRepositoryInterface;
use Repository\PaymentRepositoryInterface;
use Persistence\TransactionManagerInterface;

final readonly class ProcessPaymentUseCase
{
    public function __construct(
        private OrderRepositoryInterface $orders,
        private PaymentRepositoryInterface $payments,
        private TransactionManagerInterface $transaction,
    ) {}

    public function execute(ProcessPaymentCommand $command): void
    {
        $this->transaction->run(function () use ($command): void {
            $order = $this->orders->findById($command->orderId);
            $payment = $order->processPayment($command->paymentMethod);

            $this->orders->save($order);
            $this->payments->save($payment);
        });
    }
}
```

### Transaction Manager Interface

```php
<?php

declare(strict_types=1);

namespace Persistence;

interface TransactionManagerInterface
{
    /** @template T
     *  @param callable(): T $callback
     *  @return T */
    public function run(callable $callback): mixed;
}
```

## Query Builder vs Eloquent

### When to Use Each

| Use Case | Query Builder | Eloquent |
|----------|---------------|----------|
| Read-optimized queries | Preferred | Overhead |
| Complex joins/aggregates | Preferred | Awkward |
| CRUD with relationships | Overhead | Preferred |
| Domain model hydration | N/A | Via mapper |
| Reporting / analytics | Preferred | Too heavy |

### Read Model with Query Builder

```php
<?php

declare(strict_types=1);

namespace ReadModel;

use DTO\OrderDetailsDTO;
use ReadModel\OrderReadModelInterface;
use Illuminate\Database\ConnectionInterface;

final readonly class DatabaseOrderReadModel implements OrderReadModelInterface
{
    public function __construct(
        private ConnectionInterface $db,
    ) {}

    public function findById(string $orderId): ?OrderDetailsDTO
    {
        $row = $this->db->table('orders')
            ->join('customers', 'orders.customer_id', '=', 'customers.id')
            ->where('orders.id', $orderId)
            ->select([
                'orders.id',
                'orders.status',
                'orders.total_cents',
                'orders.currency',
                'customers.name as customer_name',
                'orders.created_at',
            ])
            ->first();

        if ($row === null) {
            return null;
        }

        return new OrderDetailsDTO(
            id: $row->id,
            status: $row->status,
            totalCents: (int) $row->total_cents,
            currency: $row->currency,
            customerName: $row->customer_name,
            createdAt: new \DateTimeImmutable($row->created_at),
        );
    }
}
```

## Read/Write Database Splitting

### Configuration

```php
// config/database.php
'mysql' => [
    'read' => [
        'host' => [env('DB_READ_HOST_1'), env('DB_READ_HOST_2')],
    ],
    'write' => [
        'host' => [env('DB_WRITE_HOST')],
    ],
    'sticky' => true, // Read from write after writing in same request
    'driver' => 'mysql',
    'database' => env('DB_DATABASE'),
],
```

### Force Write Connection

```php
// When read-after-write consistency is needed
$order = OrderModel::on('mysql::write')->find($orderId);
```

## Keeping Eloquent Out of Domain

### Detection Patterns

```bash
# Eloquent in Domain layer (CRITICAL)
Grep: "extends Model" --glob "**/Domain/**/*.php"
Grep: "use Illuminate\\Database" --glob "**/Domain/**/*.php"
Grep: "->save\(\)|->delete\(\)|->find\(" --glob "**/Domain/**/*.php"

# Repository implementations should be in Infrastructure
Grep: "implements.*RepositoryInterface" --glob "**/Domain/**/*.php"

# Good: Repository pattern used (folder placement varies by architecture)
Grep: "interface.*RepositoryInterface" --glob "**/Domain/**/*.php"
```

### Separation Rules

| Layer | Allowed | Forbidden |
|-------|---------|-----------|
| Domain | Repositories (the pattern), Entity classes | Eloquent, Query Builder, DB facade (in Clean/Onion only) |
| Application | Uses repository interfaces | Direct Eloquent or DB calls |
| Infrastructure | Eloquent models, Query Builder, DB facade | N/A |
| Presentation | N/A (delegates to Application) | Any direct DB access |
