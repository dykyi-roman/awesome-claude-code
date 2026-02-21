# Routing and HTTP Layer

Detailed patterns for Laravel routing, controllers, middleware, validation, and authorization.

## Single-Action Controllers

### Why Single-Action

| Benefit | Explanation |
|---------|-------------|
| SRP compliance | One controller = one endpoint = one responsibility |
| Smaller classes | Easier to read, test, and maintain |
| Clear routing | Route points to a specific action |
| Better DI | Constructor only injects what this action needs |

### Implementation

```php
<?php

declare(strict_types=1);

namespace App\Http\Controllers\Order;

use App\Application\Order\UseCase\ConfirmOrderUseCase;
use App\Domain\Order\ValueObject\OrderId;
use Illuminate\Http\JsonResponse;

final readonly class ConfirmOrderController
{
    public function __construct(
        private ConfirmOrderUseCase $confirmOrder,
    ) {}

    public function __invoke(string $orderId): JsonResponse
    {
        $this->confirmOrder->execute(new OrderId($orderId));

        return new JsonResponse(status: 204);
    }
}
```

### Route Registration

```php
// routes/api.php
use App\Http\Controllers\Order\CreateOrderController;
use App\Http\Controllers\Order\ConfirmOrderController;
use App\Http\Controllers\Order\GetOrderController;

Route::prefix('orders')->group(function () {
    Route::post('/', CreateOrderController::class);
    Route::post('/{order}/confirm', ConfirmOrderController::class);
    Route::get('/{order}', GetOrderController::class);
});
```

### Detection Patterns

```bash
# Find multi-action controllers (potential violation)
Grep: "public function (index|show|store|update|destroy|create|edit)" --glob "**/Controllers/**/*.php"

# Find single-action controllers (good pattern)
Grep: "public function __invoke" --glob "**/Controllers/**/*.php"

# Controllers with too many methods
Grep: "public function " --glob "**/Controllers/**/*.php" --output_mode count
```

## Middleware Pipeline

### Custom Middleware

```php
<?php

declare(strict_types=1);

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;

final readonly class EnsureJsonResponse
{
    public function handle(Request $request, Closure $next): Response
    {
        $request->headers->set('Accept', 'application/json');

        return $next($request);
    }
}
```

### Middleware for Correlation ID

```php
<?php

declare(strict_types=1);

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Illuminate\Support\Str;
use Symfony\Component\HttpFoundation\Response;

final readonly class CorrelationIdMiddleware
{
    private const HEADER = 'X-Correlation-ID';

    public function handle(Request $request, Closure $next): Response
    {
        $correlationId = $request->header(self::HEADER, Str::uuid()->toString());
        $request->headers->set(self::HEADER, $correlationId);

        /** @var Response $response */
        $response = $next($request);
        $response->headers->set(self::HEADER, $correlationId);

        return $response;
    }
}
```

## FormRequest for Validation

### Typed FormRequest with DTO Conversion

```php
<?php

declare(strict_types=1);

namespace App\Http\Requests\Order;

use App\Application\Order\Command\UpdateOrderCommand;
use App\Domain\Order\ValueObject\OrderId;
use App\Domain\Shared\ValueObject\Money;
use Illuminate\Foundation\Http\FormRequest;

final class UpdateOrderRequest extends FormRequest
{
    public function authorize(): bool
    {
        return $this->user()->can('update', $this->route('order'));
    }

    /** @return array<string, mixed> */
    public function rules(): array
    {
        return [
            'lines' => ['required', 'array', 'min:1'],
            'lines.*.product_id' => ['required', 'uuid'],
            'lines.*.quantity' => ['required', 'integer', 'min:1'],
            'lines.*.unit_price' => ['required', 'integer', 'min:0'],
            'notes' => ['nullable', 'string', 'max:500'],
        ];
    }

    public function toCommand(): UpdateOrderCommand
    {
        $validated = $this->validated();

        return new UpdateOrderCommand(
            orderId: new OrderId($this->route('order')),
            lines: $validated['lines'],
            notes: $validated['notes'] ?? null,
        );
    }
}
```

### Detection Patterns

```bash
# Find controllers doing inline validation (bad)
Grep: "\\$request->validate\(" --glob "**/Controllers/**/*.php"
Grep: "Validator::make" --glob "**/Controllers/**/*.php"

# Find proper FormRequest usage (good)
Grep: "extends FormRequest" --glob "**/*.php"
Glob: **/Requests/**/*Request.php
```

## API Resources for Response Transformation

### Resource Class

```php
<?php

declare(strict_types=1);

namespace App\Http\Resources\Order;

use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

/** @mixin \App\Application\Order\DTO\OrderDetailsDTO */
final class OrderResource extends JsonResource
{
    /** @return array<string, mixed> */
    public function toArray(Request $request): array
    {
        return [
            'id' => $this->id,
            'status' => $this->status,
            'customer' => [
                'id' => $this->customerId,
                'name' => $this->customerName,
            ],
            'total' => [
                'amount' => $this->totalCents,
                'currency' => $this->currency,
            ],
            'created_at' => $this->createdAt->toISOString(),
        ];
    }
}
```

### Collection Resource

```php
<?php

declare(strict_types=1);

namespace App\Http\Resources\Order;

use Illuminate\Http\Resources\Json\ResourceCollection;

final class OrderCollection extends ResourceCollection
{
    public $collects = OrderResource::class;
}
```

## Route Model Binding

### Implicit Binding with Custom Key

```php
// In the Eloquent Model
public function getRouteKeyName(): string
{
    return 'uuid';
}
```

### Explicit Binding via Service Provider

```php
// In RouteServiceProvider::boot()
Route::bind('order', function (string $value) {
    return OrderModel::where('uuid', $value)->firstOrFail();
});
```

### DDD-Friendly Binding (Resolve Domain Entity)

```php
// In RouteServiceProvider::boot()
Route::bind('order', function (string $value) {
    $repository = app(OrderRepositoryInterface::class);
    $order = $repository->findById(new OrderId($value));

    if ($order === null) {
        abort(404);
    }

    return $order;
});
```

## Laravel Policies for Authorization

### Policy with Domain Logic Delegation

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Http\Policy;

use App\Domain\Order\Entity\Order;
use App\Infrastructure\Auth\UserModel;

final class OrderPolicy
{
    public function update(UserModel $user, Order $order): bool
    {
        return $order->customerId()->value() === $user->id
            && $order->status()->isEditable();
    }

    public function confirm(UserModel $user, Order $order): bool
    {
        return $order->customerId()->value() === $user->id
            && $order->status()->isDraft();
    }

    public function cancel(UserModel $user, Order $order): bool
    {
        return $order->customerId()->value() === $user->id
            && $order->status()->isCancellable();
    }
}
```

### Detection Patterns

```bash
# Find authorization in controllers (should use Policy or Gate)
Grep: "if.*->id ==|if.*->user_id ==" --glob "**/Controllers/**/*.php"

# Find Policy classes
Glob: **/Policies/**/*Policy.php
Grep: "function (view|create|update|delete|restore|forceDelete)\(" --glob "**/*Policy.php"
```
