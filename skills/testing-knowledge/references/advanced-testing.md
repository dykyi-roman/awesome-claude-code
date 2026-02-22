# Advanced Testing Patterns Reference

## Contract Testing (Pact)

### What Is Contract Testing

Contract testing verifies that services communicate correctly by testing against an agreed contract rather than the actual service.

```
Consumer Test                    Provider Test
┌──────────┐                     ┌──────────┐
│ Consumer  │ → generates →      │ Provider  │
│ writes    │   Pact file        │ verifies  │
│ contract  │   (JSON)    ───▶   │ against   │
│ tests     │                    │ contract  │
└──────────┘                     └──────────┘
```

### PHP Consumer Test (Pact)

```php
<?php

declare(strict_types=1);

namespace Tests\Contract\Consumer;

use PhpPact\Consumer\InteractionBuilder;
use PhpPact\Consumer\Model\ConsumerRequest;
use PhpPact\Consumer\Model\ProviderResponse;
use PHPUnit\Framework\TestCase;

final class OrderServiceConsumerTest extends TestCase
{
    public function test_get_order_returns_order_details(): void
    {
        $request = new ConsumerRequest();
        $request->setMethod('GET');
        $request->setPath('/api/orders/123');
        $request->addHeader('Accept', 'application/json');

        $response = new ProviderResponse();
        $response->setStatus(200);
        $response->addHeader('Content-Type', 'application/json');
        $response->setBody([
            'id' => '123',
            'status' => 'confirmed',
            'total' => 99.99,
        ]);

        $builder = new InteractionBuilder($this->config);
        $builder->given('order 123 exists')
            ->uponReceiving('a request for order 123')
            ->with($request)
            ->willRespondWith($response);

        $client = new OrderServiceClient($this->mockServerUrl);
        $order = $client->getOrder('123');

        self::assertSame('123', $order->id);
        self::assertSame('confirmed', $order->status);

        $builder->verify();
    }
}
```

### Provider Verification

```php
<?php

declare(strict_types=1);

namespace Tests\Contract\Provider;

use PhpPact\Standalone\ProviderVerifier\Model\VerifierConfig;
use PhpPact\Standalone\ProviderVerifier\Verifier;
use PHPUnit\Framework\TestCase;

final class OrderServiceProviderTest extends TestCase
{
    public function test_provider_honors_consumer_contracts(): void
    {
        $config = new VerifierConfig();
        $config->setProviderName('OrderService');
        $config->setProviderBaseUrl('http://localhost:8080');
        $config->setPactBrokerUri('https://pact-broker.example.com');

        $verifier = new Verifier($config);
        $verifier->verifyProvider();

        self::assertTrue(true);
    }
}
```

### When to Use Contract Testing

| Scenario | Contract Testing? | Why |
|----------|-------------------|-----|
| Microservices REST APIs | Yes | Verify API compatibility across deploys |
| Shared libraries | No | Unit tests sufficient |
| Message-based systems | Yes | Verify event schema compatibility |
| Database schema | No | Migration tests cover this |
| Third-party APIs | Consumer only | Can't control provider |

## Chaos Testing (Failure Injection)

### Failure Types to Inject

| Failure | How to Inject | What It Tests |
|---------|---------------|---------------|
| Network latency | Sleep in middleware | Timeout handling |
| Service error | Return 500 randomly | Circuit breaker, retry |
| Connection refused | Close port | Fallback behavior |
| Slow database | Add delay to queries | Query timeout handling |
| Memory pressure | Allocate large arrays | OOM handling |
| Disk full | Fill temp directory | Write error handling |

### PHP Failure Injector

```php
<?php

declare(strict_types=1);

namespace Tests\Chaos;

final class FailureInjector
{
    private static array $rules = [];

    public static function addRule(string $service, FailureRule $rule): void
    {
        self::$rules[$service] = $rule;
    }

    public static function shouldFail(string $service): bool
    {
        if (!isset(self::$rules[$service])) {
            return false;
        }

        return self::$rules[$service]->shouldTrigger();
    }

    public static function reset(): void
    {
        self::$rules = [];
    }
}

final readonly class FailureRule
{
    public function __construct(
        private int $failurePercentage,
        private int $latencyMs = 0,
    ) {}

    public function shouldTrigger(): bool
    {
        return random_int(1, 100) <= $this->failurePercentage;
    }
}
```

## Load Testing Patterns

### Test Types

| Pattern | Duration | Load Profile | Goal |
|---------|----------|-------------- |------|
| Smoke | 1-2 min | Minimal load | Verify script works |
| Load | 10-30 min | Expected traffic | Find performance baseline |
| Stress | 10-30 min | 1.5-2x expected | Find breaking point |
| Spike | 5-10 min | Sudden burst | Test auto-scaling |
| Soak/Endurance | 2-8 hours | Sustained load | Find memory leaks |
| Breakpoint | Until failure | Incremental increase | Find maximum capacity |

### Load Test Script Structure (k6-style)

```javascript
// k6 load test example for PHP API
export const options = {
    stages: [
        { duration: '2m', target: 50 },   // Ramp up
        { duration: '5m', target: 50 },   // Sustained
        { duration: '2m', target: 100 },  // Stress
        { duration: '5m', target: 100 },  // Sustained stress
        { duration: '2m', target: 0 },    // Ramp down
    ],
    thresholds: {
        http_req_duration: ['p(95)<500'],  // 95th percentile < 500ms
        http_req_failed: ['rate<0.01'],    // Error rate < 1%
    },
};
```

### PHP Performance Baseline Checklist

| Metric | Target | Measurement |
|--------|--------|-------------|
| p50 response time | < 100ms | Percentile from load test |
| p95 response time | < 500ms | Percentile from load test |
| p99 response time | < 1000ms | Percentile from load test |
| Error rate | < 0.1% | Failed requests / total |
| Throughput | > 1000 RPS | Requests per second |
| CPU usage | < 70% | Under normal load |
| Memory usage | < 80% | No growth over time |

## E2E Distributed Testing

### Test Boundaries

```
┌─────────────────────────────────────────┐
│           E2E Test Scope                 │
│                                          │
│  API Gateway → Service A → Service B     │
│       ↓             ↓           ↓        │
│    Database      Cache      Message Queue│
│                                          │
│  Verify: Full user journey works         │
│  Avoid: Testing internal implementation  │
└─────────────────────────────────────────┘
```

### PHPUnit E2E Test with Docker

```php
<?php

declare(strict_types=1);

namespace Tests\E2E;

use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('e2e')]
final class OrderFlowE2ETest extends TestCase
{
    private HttpClientInterface $client;

    protected function setUp(): void
    {
        $this->client = HttpClient::create([
            'base_uri' => 'http://localhost:8080',
            'timeout' => 30,
        ]);
    }

    public function test_complete_order_flow(): void
    {
        $response = $this->client->request('POST', '/api/orders', [
            'json' => [
                'product_id' => 'prod-123',
                'quantity' => 2,
            ],
            'headers' => [
                'Authorization' => 'Bearer ' . $this->getTestToken(),
                'Idempotency-Key' => 'test-' . uniqid(),
            ],
        ]);

        self::assertSame(201, $response->getStatusCode());

        $order = json_decode($response->getContent(), true);
        self::assertArrayHasKey('id', $order);
        self::assertSame('pending', $order['status']);

        $this->waitForEventProcessing(timeout: 5);

        $statusResponse = $this->client->request('GET', '/api/orders/' . $order['id']);
        $updated = json_decode($statusResponse->getContent(), true);
        self::assertSame('confirmed', $updated['status']);
    }

    private function waitForEventProcessing(int $timeout): void
    {
        sleep($timeout);
    }
}
```

### Test Data Management in Distributed Tests

| Strategy | How | Trade-off |
|----------|-----|-----------|
| Test containers | Docker Compose per test | Isolated but slow startup |
| Shared test environment | Dedicated staging | Fast but test interference |
| Data seeding | API/DB setup per test | Controlled but complex |
| Snapshot restore | DB snapshot before tests | Fast reset, storage cost |
