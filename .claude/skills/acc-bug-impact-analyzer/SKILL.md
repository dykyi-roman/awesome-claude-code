---
name: acc-bug-impact-analyzer
description: Analyzes bug fix blast radius. Determines affected code, dependencies, callers/callees, and potential side effects of changes.
---

# Bug Impact Analyzer

Systematic analysis of how a bug fix will affect the codebase.

## Blast Radius Concept

Every code change has a "blast radius" - the scope of code that could be affected.

```
                    ┌─────────────────┐
                    │   Direct Fix    │ ← Minimal blast radius
                    │  (1 method)     │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
        ┌─────────┐    ┌─────────┐    ┌─────────┐
        │ Caller 1│    │ Caller 2│    │ Caller 3│ ← Medium blast radius
        └────┬────┘    └────┬────┘    └────┬────┘
             │              │              │
    ┌────────┴────────┬─────┴─────┬────────┴────────┐
    ▼                 ▼           ▼                 ▼
┌───────┐        ┌───────┐   ┌───────┐        ┌───────┐
│Public │        │ Event │   │ Test  │        │  API  │ ← Large blast radius
│  API  │        │Handler│   │ Suite │        │Client │
└───────┘        └───────┘   └───────┘        └───────┘
```

## Analysis Dimensions

### 1. Direct Callers Analysis

Find all code that directly calls the changed method.

```bash
# Find callers of a method
grep -rn "->methodName(" src/
grep -rn "::methodName(" src/

# Find callers in tests
grep -rn "->methodName(" tests/
```

**Impact Questions:**
- Will callers still work with the fix?
- Do callers expect the old behavior?
- Are there callers in external packages?

### 2. Callees Analysis (Dependencies)

Find all code that the changed method calls.

```php
// Example: Method being fixed
public function calculateTotal(array $items): Money
{
    // Callees:
    $sum = Money::zero($this->currency);           // 1. Money::zero()
    foreach ($items as $item) {
        $price = $item->getPrice();                // 2. Item::getPrice()
        $quantity = $item->getQuantity();          // 3. Item::getQuantity()
        $sum = $sum->add($price->multiply($quantity)); // 4. Money::add(), Money::multiply()
    }
    return $sum;
}
```

**Impact Questions:**
- Does the fix change how callees are used?
- Are new callees introduced?
- Could new callees throw exceptions?

### 3. Data Flow Analysis

Trace how data flows through the system.

```
Input Data Flow:
Request → DTO → Command → Entity → Repository → Database
                  ↓
              Validation
                  ↓
              [BUG HERE] - invalid data passed forward

Fix Impact:
- Validation added at Command level
- All downstream code now receives valid data
- Callers must handle ValidationException
```

### 4. Event/Message Impact

Check if the change affects published events or messages.

```php
// If the buggy method publishes events:
class OrderService
{
    public function completeOrder(Order $order): void
    {
        // BUG FIX HERE
        $order->complete();

        // EVENT PUBLISHED - fix might change event data
        $this->eventBus->publish(new OrderCompleted($order));
    }
}
```

**Impact Questions:**
- Does the fix change event payload?
- Are there subscribers depending on old data?
- Are events used for external integration?

### 5. API Contract Analysis

Check if the change affects public APIs.

| Change Type | API Impact | Severity |
|-------------|------------|----------|
| Return type change | Breaking | High |
| New exception type | Breaking | High |
| New required parameter | Breaking | High |
| New optional parameter | Compatible | Low |
| Different return value (same type) | Semantic breaking | Medium |
| Performance change | SLA impact | Medium |

### 6. Database Impact

Check if the fix affects database state.

```php
// Fix that changes data format
// BEFORE: stored as "2024-01-15"
// AFTER: stored as "2024-01-15T00:00:00Z"

// Impact:
// - Existing data incompatible
// - Need migration
// - Other services reading same data affected
```

**Impact Questions:**
- Does fix change data format?
- Is migration needed?
- Are other services affected?

## Impact Assessment Matrix

### Severity Levels

| Level | Description | Action Required |
|-------|-------------|-----------------|
| **Low** | Internal implementation only | Fix and test |
| **Medium** | Affects callers within same bounded context | Verify all callers |
| **High** | Affects public API or other contexts | Coordinate with stakeholders |
| **Critical** | Affects external integrations | Version API, migration plan |

### Assessment Checklist

```markdown
## Impact Assessment: [Bug ID]

### Direct Impact (Low)
- [ ] Method signature unchanged
- [ ] Return type unchanged
- [ ] Exceptions unchanged
- [ ] Side effects unchanged

### Caller Impact (Medium)
- [ ] All callers identified: [count]
- [ ] Callers tested: [count]
- [ ] No behavioral changes for callers

### Cross-Context Impact (High)
- [ ] Events payload unchanged
- [ ] Messages format unchanged
- [ ] Shared database schema unchanged

### External Impact (Critical)
- [ ] Public API unchanged
- [ ] SDK compatibility maintained
- [ ] Documentation update not needed

### Overall Blast Radius: [Low/Medium/High/Critical]
```

## Dependency Graph Building

### Step 1: Identify Changed Code

```php
// File: src/Domain/Order/OrderService.php
// Method: calculateTotal()
// Line: 45-60
```

### Step 2: Find Direct Dependents

```bash
# Classes that use OrderService
grep -rn "OrderService" src/ --include="*.php"

# Results:
# src/Application/UseCase/CreateOrderUseCase.php:15
# src/Application/UseCase/UpdateOrderUseCase.php:18
# src/Presentation/Api/OrderController.php:22
```

### Step 3: Build Dependency Tree

```
OrderService::calculateTotal()
├── CreateOrderUseCase (calls calculateTotal)
│   ├── OrderController::create() (calls UseCase)
│   │   └── POST /api/orders (HTTP endpoint)
│   └── CreateOrderFromCartHandler (event handler)
│       └── CartCheckoutCompleted (event trigger)
│
├── UpdateOrderUseCase (calls calculateTotal)
│   ├── OrderController::update() (calls UseCase)
│   │   └── PUT /api/orders/{id} (HTTP endpoint)
│   └── AddItemToOrderHandler (command handler)
│
└── OrderTotalRecalculationJob (calls calculateTotal)
    └── Scheduler (cron trigger)
```

### Step 4: Assess Each Branch

| Dependent | Risk | Needs Testing | Notes |
|-----------|------|---------------|-------|
| CreateOrderUseCase | Medium | Yes | Core flow |
| UpdateOrderUseCase | Medium | Yes | Core flow |
| OrderController::create | Low | Covered | Via UseCase test |
| OrderController::update | Low | Covered | Via UseCase test |
| CreateOrderFromCartHandler | High | Yes | Async, hard to debug |
| OrderTotalRecalculationJob | High | Yes | Background job |

## Side Effects Mapping

### Intentional Side Effects

```php
class OrderService
{
    public function completeOrder(Order $order): void
    {
        $order->complete();                        // State change
        $this->repository->save($order);           // Database write
        $this->eventBus->publish($event);          // Event published
        $this->metrics->increment('orders.completed'); // Metrics
        $this->logger->info('Order completed');    // Logging
    }
}
```

### Side Effect Impact Table

| Side Effect | Preserved After Fix? | Impact if Changed |
|-------------|---------------------|-------------------|
| Entity state change | Must preserve | Breaks domain logic |
| Database write | Must preserve | Data inconsistency |
| Event publish | Check payload | Downstream handlers affected |
| Metrics | Should preserve | Dashboard/alerts affected |
| Logging | Can change | Low impact |

## Test Coverage Analysis

### Finding Existing Tests

```bash
# Tests for the class being fixed
grep -rn "OrderService" tests/ --include="*.php"

# Tests that might break
grep -rn "calculateTotal" tests/ --include="*.php"
```

### Coverage Gaps

```markdown
## Test Coverage for OrderService::calculateTotal()

### Existing Tests
- [x] OrderServiceTest::testCalculateTotalWithItems
- [x] OrderServiceTest::testCalculateTotalEmpty
- [ ] Missing: testCalculateTotalWithNullItem ← Bug case

### Integration Tests
- [x] CreateOrderUseCaseTest
- [ ] Missing: UpdateOrderUseCaseTest

### E2E Tests
- [x] POST /api/orders
- [ ] Missing: PUT /api/orders/{id}
```

## Quick Impact Commands

```bash
# Find all files that import/use the changed class
grep -rln "use.*OrderService" src/

# Find all method calls
grep -rn "->calculateTotal(" src/ tests/

# Find event subscribers
grep -rn "OrderCompleted" src/

# Find API routes using the controller
grep -rn "OrderController" routes/

# Count affected files
grep -rln "OrderService" src/ | wc -l
```

## Impact Report Template

```markdown
# Impact Analysis Report

## Bug: [ID/Description]
## Fix Location: [File:Line]

## Blast Radius Summary

| Dimension | Count | Risk |
|-----------|-------|------|
| Direct Callers | X | Low/Med/High |
| Event Handlers | X | Low/Med/High |
| API Endpoints | X | Low/Med/High |
| Database Tables | X | Low/Med/High |
| External Services | X | Low/Med/High |

## Detailed Impact

### Callers Affected
1. [Caller 1] - [Impact description]
2. [Caller 2] - [Impact description]

### Events Affected
1. [Event 1] - [Payload change?]

### APIs Affected
1. [Endpoint 1] - [Response change?]

## Testing Requirements
- [ ] Unit test for fix
- [ ] Integration tests for callers
- [ ] E2E tests for APIs
- [ ] Manual testing for [scenarios]

## Rollout Recommendation
- [ ] Safe for immediate deployment
- [ ] Requires staged rollout
- [ ] Requires feature flag
- [ ] Requires coordination with [teams]
```
