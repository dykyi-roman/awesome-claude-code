# Laravel Antipatterns

Common Laravel antipatterns with detection patterns, bad/good code examples, and severity ratings.

## Critical Violations

### 1. God Model (Fat Eloquent Model)

**Description:** Eloquent Model containing business logic, validation, formatting, notifications, and query scopes all in one massive class.

**Why Critical:** Violates SRP, untestable without database, mixes persistence with business logic, grows uncontrollably.

**Detection:**
```bash
# Find large models (potential God Models)
Grep: "extends Model" --glob "**/Models/**/*.php"

# Business methods in models
Grep: "public function (calculate|process|validate|send|notify|approve|reject|charge|refund)" --glob "**/Models/**/*.php"

# Models using external services
Grep: "Mail::|Notification::|Event::|Queue::|Http::" --glob "**/Models/**/*.php"
```

**Bad:**
```php
<?php

declare(strict_types=1);

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Support\Facades\Mail;
use Illuminate\Support\Facades\Cache;

class Order extends Model
{
    // Business logic in model
    public function calculateTotal(): int
    {
        $subtotal = $this->lines->sum(fn ($l) => $l->price * $l->quantity);
        $discount = $this->customer->isVip() ? 0.1 : 0;
        return (int) ($subtotal * (1 - $discount));
    }

    // Notification in model
    public function confirm(): void
    {
        $this->status = 'confirmed';
        $this->save();
        Mail::to($this->customer->email)->send(new OrderConfirmed($this));
        Cache::forget("order:{$this->id}");
    }

    // Validation in model
    public function canBeShipped(): bool
    {
        return $this->status === 'confirmed'
            && $this->payment_status === 'paid'
            && $this->lines->every(fn ($l) => $l->product->inStock());
    }
}
```

**Good:**
```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Persistence\Eloquent\Model;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\HasMany;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

// Model: persistence only
final class OrderModel extends Model
{
    protected $table = 'orders';
    protected $fillable = ['id', 'customer_id', 'status', 'total_cents'];

    public function customer(): BelongsTo
    {
        return $this->belongsTo(CustomerModel::class);
    }

    public function lines(): HasMany
    {
        return $this->hasMany(OrderLineModel::class);
    }
}

// Domain Entity: business logic
// App\Domain\Order\Entity\Order -- separate class with no Eloquent
```

### 2. Fat Controller

**Description:** Controller containing business logic, validation, database queries, and response formatting.

**Why Critical:** Untestable business logic, duplicated across controllers, tight framework coupling.

**Detection:**
```bash
# Long controller methods
Grep: "public function (store|update|index|show)" --glob "**/Controllers/**/*.php" -A 30

# Direct DB/Model calls in controller
Grep: "DB::table\(|::where\(|::find\(|::create\(" --glob "**/Controllers/**/*.php"

# Business conditions in controller
Grep: "if.*->status|if.*->is_|switch.*->type" --glob "**/Controllers/**/*.php"
```

**Bad:**
```php
<?php

declare(strict_types=1);

namespace App\Http\Controllers;

use App\Models\Order;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Mail;

class OrderController extends Controller
{
    public function store(Request $request): JsonResponse
    {
        // Inline validation
        $data = $request->validate([
            'customer_id' => 'required|uuid',
            'lines' => 'required|array',
        ]);

        // Business logic in controller
        $order = DB::transaction(function () use ($data) {
            $order = Order::create(['customer_id' => $data['customer_id'], 'status' => 'draft']);
            $total = 0;

            foreach ($data['lines'] as $line) {
                $product = Product::findOrFail($line['product_id']);
                if ($product->stock < $line['quantity']) {
                    throw new \Exception("Not enough stock for {$product->name}");
                }
                $lineTotal = $product->price * $line['quantity'];
                $total += $lineTotal;
                $order->lines()->create([...]);
                $product->decrement('stock', $line['quantity']);
            }

            $order->update(['total' => $total]);
            return $order;
        });

        Mail::to($order->customer->email)->send(new OrderCreatedMail($order));

        return response()->json($order->load('lines', 'customer'), 201);
    }
}
```

**Good:**
```php
<?php

declare(strict_types=1);

namespace App\Http\Controllers\Order;

use App\Application\Order\UseCase\CreateOrderUseCase;
use App\Http\Requests\Order\CreateOrderRequest;
use App\Http\Resources\Order\OrderResource;
use Illuminate\Http\JsonResponse;
use Symfony\Component\HttpFoundation\Response;

final readonly class CreateOrderController
{
    public function __construct(
        private CreateOrderUseCase $createOrder,
    ) {}

    public function __invoke(CreateOrderRequest $request): JsonResponse
    {
        $orderId = $this->createOrder->execute($request->toCommand());

        return OrderResource::make($orderId)
            ->response()
            ->setStatusCode(Response::HTTP_CREATED);
    }
}
```

### 3. Business Logic in Blade Templates

**Description:** Blade templates containing calculations, conditionals on business state, or data transformation.

**Detection:**
```bash
# Complex logic in Blade
Grep: "@if.*->status|@if.*->is_|@switch" --glob "**/*.blade.php"
Grep: "@php" --glob "**/*.blade.php"
Grep: "\\$.*->calculate|\\$.*->total\(\)" --glob "**/*.blade.php"
```

**Bad:**
```blade
@if($order->status === 'draft' && $order->lines->count() > 0 && $order->customer->isActive())
    <button>Confirm</button>
@elseif($order->status === 'confirmed' && now()->diffInHours($order->confirmed_at) < 24)
    <button>Cancel</button>
@endif

<span>{{ number_format($order->lines->sum(fn($l) => $l->price * $l->quantity) * 0.9, 2) }}</span>
```

**Good:**
```blade
@if($order->canBeConfirmed)
    <button>Confirm</button>
@elseif($order->canBeCancelled)
    <button>Cancel</button>
@endif

<span>{{ $order->formattedTotal }}</span>
```

## Warning Violations

### 4. Facade Overuse

**Description:** Using Facades instead of dependency injection, especially in Application and Domain layers.

**Detection:**
```bash
# Count Facade imports per file
Grep: "use Illuminate\\Support\\Facades\\" --glob "**/*.php" --output_mode count

# Facades in Application layer
Grep: "use Illuminate\\Support\\Facades" --glob "**/Application/**/*.php"

# Static Facade calls
Grep: "(Cache|Log|Event|DB|Auth|Queue|Mail|Storage|Http)::" --glob "**/Application/**/*.php"
```

**Bad:**
```php
<?php

declare(strict_types=1);

namespace App\Application\Order\UseCase;

use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Log;

final class CreateOrderUseCase
{
    public function execute(array $data): Order
    {
        Log::info('Creating order', $data);
        return DB::transaction(fn () => $this->create($data));
    }
}
```

**Good:** Use constructor injection with interfaces (see `dependency-injection.md`).

### 5. Missing Repository Abstraction

**Description:** Eloquent calls scattered across application instead of centralized in repositories.

**Detection:**
```bash
# Direct Eloquent calls outside Infrastructure
Grep: "::where\(|::find\(|::create\(|::firstOrFail\(" --glob "**/Application/**/*.php"
Grep: "::where\(|::find\(|::create\(|::firstOrFail\(" --glob "**/Http/Controllers/**/*.php"

# Check for repository interfaces
Grep: "interface.*RepositoryInterface" --glob "**/Domain/**/*.php"
```

**Bad:**
```php
// In UseCase
$order = Order::where('customer_id', $customerId)->where('status', 'draft')->first();
```

**Good:**
```php
// In UseCase
$order = $this->orders->findDraftByCustomer($customerId);
```

### 6. N+1 Queries with Relationships

**Description:** Accessing related models in a loop without eager loading, causing one query per iteration.

**Detection:**
```bash
# Relationship access in loops (potential N+1)
Grep: "foreach.*->.*\n.*->.*->" --glob "**/*.php" --multiline true

# Missing eager loading before loops
Grep: "::all\(\)|::get\(\)" --glob "**/*.php" -A 5

# Preventive: check for with() usage
Grep: "->with\(|::with\(" --glob "**/*.php" --output_mode count
```

**Bad:**
```php
$orders = Order::all(); // 1 query

foreach ($orders as $order) {
    echo $order->customer->name; // N queries (one per order)
    foreach ($order->lines as $line) {
        echo $line->product->name; // N*M queries
    }
}
```

**Good:**
```php
$orders = Order::with(['customer', 'lines.product'])->get(); // 3 queries total

foreach ($orders as $order) {
    echo $order->customer->name; // Already loaded
    foreach ($order->lines as $line) {
        echo $line->product->name; // Already loaded
    }
}
```

### Prevent N+1 Globally

```php
// In AppServiceProvider::boot()
Model::preventLazyLoading(!app()->isProduction());
```

## 7. Business Logic in Policies

**Severity:** Warning

Policies containing database queries, complex calculations, or domain logic instead of delegating to domain Specifications.

**Detection:**
```bash
# DB access in policies
Grep: "DB::|->where\\(|->count\\(|->exists\\(" --glob "**/*Policy.php"

# Complex conditions in policies
Grep: "&&.*&&|\\|\\|.*\\|\\|" --glob "**/*Policy.php"
```

**Bad:**
```php
<?php

declare(strict_types=1);

namespace App\Policies;

class OrderPolicy
{
    public function cancel(User $user, Order $order): bool
    {
        // VIOLATION: DB query and business logic in Policy
        $hasPendingPayments = DB::table('payments')
            ->where('order_id', $order->id)
            ->where('status', 'pending')
            ->exists();

        return !$hasPendingPayments && $order->customer_id === $user->id;
    }
}
```

**Good:**
```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Http\Policy;

use App\Domain\Order\Specification\CanCancelOrderSpecification;

final class OrderPolicy
{
    public function __construct(
        private readonly CanCancelOrderSpecification $specification,
    ) {}

    public function cancel(UserModel $user, Order $order): bool
    {
        return $this->specification->isSatisfiedBy($order, $user);
    }
}
```

## 8. Missing Job Resilience

**Severity:** Warning

Queued jobs without retry strategy, timeout, or failure handling.

**Detection:**
```bash
# Jobs without retry configuration
Grep: "implements ShouldQueue" --glob "**/Jobs/**/*.php"
Grep: "\\$tries|\\$maxExceptions|\\$timeout|backoff\\(\\)|retryUntil\\(\\)" --glob "**/Jobs/**/*.php" --output_mode count

# Jobs without failed() method
Grep: "function failed\\(" --glob "**/Jobs/**/*.php" --output_mode count
```

**Bad:**
```php
<?php

declare(strict_types=1);

namespace App\Jobs;

use Illuminate\Contracts\Queue\ShouldQueue;

// VIOLATION: No retry, no timeout, no failure handling
class ProcessPayment implements ShouldQueue
{
    public function handle(): void
    {
        // External API call with no resilience
        Http::post('https://api.stripe.com/v1/charges', $this->data);
    }
}
```

**Good:**
```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Queue\Job;

use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\Middleware\WithoutOverlapping;

final class ProcessPayment implements ShouldQueue
{
    use InteractsWithQueue, Queueable;

    public int $tries = 3;
    public int $timeout = 120;
    public bool $failOnTimeout = true;

    /** @return array<int> */
    public function backoff(): array { return [1, 5, 10]; }

    /** @return array<object> */
    public function middleware(): array
    {
        return [(new WithoutOverlapping($this->orderId))->releaseAfter(60)];
    }

    public function handle(ProcessPaymentUseCase $useCase): void { /* ... */ }

    public function failed(\Throwable $exception): void
    {
        Log::critical('Payment failed permanently', ['order' => $this->orderId]);
    }
}
```

## Severity Matrix

| Antipattern | Severity | Impact | Fix Effort |
|-------------|----------|--------|------------|
| God Model | Critical | Architecture, testability | High |
| Fat Controller | Critical | Maintainability, testing | Medium |
| Business logic in Blade | Critical | Separation of concerns | Medium |
| Facade overuse | Warning | Coupling, testability | Medium |
| Missing repository | Warning | Coupling, DDD violation | High |
| N+1 queries | Warning | Performance | Low |
| Direct DB in Controller | Warning | Architecture | Medium |
| Business logic in Policy | Warning | Separation of concerns | Medium |
| Missing job resilience | Warning | Reliability | Low |
| Inline validation | Info | Reusability | Low |
