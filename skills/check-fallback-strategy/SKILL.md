---
name: acc-check-fallback-strategy
description: Audits fallback and graceful degradation strategies. Checks cache fallback, feature flags, default values, circuit breaker fallbacks, and degraded mode implementations.
---

# Fallback Strategy Audit

Analyze PHP code for missing or insufficient fallback strategies ensuring graceful degradation under failure conditions.

## Detection Patterns

### 1. No Fallback on External Service Failure

```php
// CRITICAL: Exception propagates — no graceful degradation
class ProductService
{
    public function getRecommendations(UserId $userId): array
    {
        return $this->recommendationApi->fetch($userId); // If API down → 500 error
    }
}

// CORRECT: Fallback to cached/default recommendations
class ProductService
{
    public function getRecommendations(UserId $userId): array
    {
        try {
            $recommendations = $this->recommendationApi->fetch($userId);
            $this->cache->set("reco:{$userId}", $recommendations, 3600);
            return $recommendations;
        } catch (ServiceUnavailableException $e) {
            $cached = $this->cache->get("reco:{$userId}");
            if ($cached !== null) {
                return $cached; // Stale but available
            }
            return $this->defaultRecommendations(); // Ultimate fallback
        }
    }
}
```

### 2. Missing Cache Fallback (Cache-Aside Without Stale)

```php
// ANTIPATTERN: Cache miss + origin failure = error
class PricingService
{
    public function getPrice(ProductId $id): Money
    {
        $cached = $this->cache->get("price:{$id}");
        if ($cached !== null) {
            return $cached;
        }

        $price = $this->pricingApi->fetch($id); // If API fails, no fallback!
        $this->cache->set("price:{$id}", $price, 300);
        return $price;
    }
}

// CORRECT: Stale-while-revalidate pattern
class PricingService
{
    public function getPrice(ProductId $id): Money
    {
        $cached = $this->cache->get("price:{$id}");
        $stale = $this->cache->get("price:stale:{$id}");

        if ($cached !== null) {
            return $cached;
        }

        try {
            $price = $this->pricingApi->fetch($id);
            $this->cache->set("price:{$id}", $price, 300);
            $this->cache->set("price:stale:{$id}", $price, 86400); // 24h stale
            return $price;
        } catch (ServiceUnavailableException $e) {
            if ($stale !== null) {
                return $stale; // Stale but available
            }
            throw new PriceUnavailableException('Cannot determine price', previous: $e);
        }
    }
}
```

### 3. Feature Flag Without Fallback

```php
// ANTIPATTERN: Feature flag service down = unknown state
class FeatureService
{
    public function isEnabled(string $feature): bool
    {
        return $this->flagService->evaluate($feature); // What if flag service is down?
    }
}

// CORRECT: Default values when flag service unavailable
class FeatureService
{
    private const array DEFAULTS = [
        'new_checkout' => false, // Conservative default
        'dark_mode' => true,     // Safe to enable
    ];

    public function isEnabled(string $feature): bool
    {
        try {
            return $this->flagService->evaluate($feature);
        } catch (FeatureFlagException $e) {
            $this->logger->warning('Feature flag service unavailable', [
                'feature' => $feature,
                'default' => self::DEFAULTS[$feature] ?? false,
            ]);
            return self::DEFAULTS[$feature] ?? false;
        }
    }
}
```

### 4. Circuit Breaker Without Fallback

```php
// ANTIPATTERN: Circuit breaker opens but no fallback
class PaymentGateway
{
    public function charge(Money $amount): PaymentResult
    {
        return $this->circuitBreaker->call(
            fn () => $this->stripe->charge($amount),
            // No fallback! When circuit opens → exception
        );
    }
}

// CORRECT: Meaningful fallback
class PaymentGateway
{
    public function charge(Money $amount): PaymentResult
    {
        return $this->circuitBreaker->call(
            fn () => $this->stripe->charge($amount),
            fallback: fn () => PaymentResult::deferred(
                reason: 'Payment gateway temporarily unavailable',
                retryAt: new DateTimeImmutable('+5 minutes'),
            ),
        );
    }
}
```

### 5. Degraded Mode Not Implemented

```php
// ANTIPATTERN: All-or-nothing — no partial functionality
class DashboardService
{
    public function getData(): DashboardDTO
    {
        return new DashboardDTO(
            stats: $this->statsService->getStats(),           // Required
            recommendations: $this->recoService->get(),        // Optional!
            notifications: $this->notificationService->get(),  // Optional!
            weather: $this->weatherApi->current(),             // Optional!
        );
        // If ANY optional service fails → entire dashboard fails
    }
}

// CORRECT: Graceful degradation per component
class DashboardService
{
    public function getData(): DashboardDTO
    {
        return new DashboardDTO(
            stats: $this->statsService->getStats(), // Required — let it throw
            recommendations: $this->tryGet(fn () => $this->recoService->get(), []),
            notifications: $this->tryGet(fn () => $this->notificationService->get(), []),
            weather: $this->tryGet(fn () => $this->weatherApi->current(), null),
        );
    }

    private function tryGet(callable $fn, mixed $default): mixed
    {
        try {
            return $fn();
        } catch (\Throwable $e) {
            $this->logger->warning('Degraded mode', ['error' => $e->getMessage()]);
            return $default;
        }
    }
}
```

## Grep Patterns

```bash
# External calls without try-catch
Grep: "->fetch\(|->call\(|->request\(|->send\(" --glob "**/Infrastructure/**/*.php"

# Cache without stale fallback
Grep: "cache->get|cache->set" --glob "**/*.php"
Grep: "stale|fallback|default" --glob "**/*.php"

# Circuit breaker usage (check for fallback parameter)
Grep: "circuitBreaker->call\(" --glob "**/*.php"

# Feature flags
Grep: "isEnabled\(|featureFlag|feature_flag" --glob "**/*.php"

# Multiple service calls in one method
Grep: "\$this->.*Service->.*\n.*\$this->.*Service->" --glob "**/Application/**/*.php"
```

## Severity Classification

| Pattern | Severity |
|---------|----------|
| No fallback on critical service | 🔴 Critical |
| Cache without stale data | 🟠 Major |
| Circuit breaker without fallback | 🟠 Major |
| Feature flags without defaults | 🟠 Major |
| All-or-nothing dashboard/page | 🟡 Minor |

## Output Format

```markdown
### Fallback Strategy: [Description]

**Severity:** 🔴/🟠/🟡
**Location:** `file.php:line`
**Service:** [External service name]

**Issue:**
[Description of missing fallback]

**User Impact:**
- Complete failure when service X is unavailable
- No graceful degradation path

**Code:**
```php
// No fallback
```

**Fix:**
```php
// With fallback strategy
```

**Fallback Chain:**
1. Primary: Live data from service
2. Secondary: Cached/stale data
3. Tertiary: Default values
```
