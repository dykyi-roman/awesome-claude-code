# Test Smell Catalog

Detailed examples and detection patterns for 15 test smells.

## 1. Logic in Test

**Problem:** Test contains conditional logic (if/for/while).

**Detection:**
```bash
Grep: "if \(" --glob "tests/**/*Test.php"
Grep: "for \(" --glob "tests/**/*Test.php"
Grep: "while \(" --glob "tests/**/*Test.php"
Grep: "foreach \(" --glob "tests/**/*Test.php"
```

**Example (Bad):**
```php
public function test_calculates_total(): void
{
    $items = [10, 20, 30];
    $total = 0;
    foreach ($items as $item) {  // ❌ Logic in test
        $total += $item;
    }
    self::assertEquals($total, $this->calculator->sum($items));
}
```

**Fix:** Use data providers or inline expected values.
```php
public function test_calculates_total(): void
{
    $items = [10, 20, 30];

    self::assertEquals(60, $this->calculator->sum($items));  // ✅
}
```

---

## 2. Mock Overuse

**Problem:** More than 3 mocks in a single test.

**Detection:**
```bash
Grep: "createMock\|createStub" --glob "tests/**/*Test.php" -C 20
# Count mocks per test method
```

**Example (Bad):**
```php
public function test_process_order(): void
{
    $repository = $this->createMock(OrderRepository::class);      // 1
    $mailer = $this->createMock(MailerInterface::class);          // 2
    $logger = $this->createMock(LoggerInterface::class);          // 3
    $eventDispatcher = $this->createMock(EventDispatcher::class); // 4
    $validator = $this->createMock(ValidatorInterface::class);    // 5 ❌
    // ...
}
```

**Fix:** Use Fakes, refactor design, or split test.
```php
public function test_process_order(): void
{
    $repository = new InMemoryOrderRepository();  // Fake
    $mailer = new CollectingMailer();             // Fake
    $eventDispatcher = new CollectingEventDispatcher(); // Fake
    // ...
}
```

---

## 3. Test Interdependence

**Problem:** Tests depend on execution order or shared state.

**Detection:**
```bash
Grep: "static \$" --glob "tests/**/*Test.php"
Grep: "self::\$[a-z]" --glob "tests/**/*Test.php"
Grep: "@depends" --glob "tests/**/*Test.php"
```

**Example (Bad):**
```php
private static array $createdUsers = [];  // ❌ Shared state

public function test_creates_user(): void
{
    $user = $this->service->create('john@example.com');
    self::$createdUsers[] = $user;
}

public function test_finds_created_user(): void
{
    $user = $this->service->find(self::$createdUsers[0]->id);  // ❌ Depends on previous
}
```

**Fix:** Each test creates its own data.
```php
public function test_finds_user(): void
{
    $user = UserMother::default();
    $this->repository->save($user);

    $found = $this->service->find($user->id);

    self::assertEquals($user->id, $found->id);
}
```

---

## 4. Fragile Test

**Problem:** Test breaks when implementation changes (not behavior).

**Detection:**
```bash
Grep: "expects\(.*exactly\|expects\(.*at\(" --glob "tests/**/*Test.php"
Grep: "->method\('_" --glob "tests/**/*Test.php"
```

**Example (Bad):**
```php
$mock->expects($this->exactly(3))->method('process');  // ❌ Verifies HOW, not WHAT
$mock->expects($this->at(0))->method('first');
$mock->expects($this->at(1))->method('second');
```

**Fix:** Test outcomes, not call sequences.
```php
$this->service->processAll($items);

self::assertCount(3, $this->repository->findProcessed());  // ✅ Verifies WHAT
```

---

## 5. Mystery Guest

**Problem:** Test uses external files or hidden data sources.

**Detection:**
```bash
Grep: "file_get_contents\|fopen\|include\|require" --glob "tests/**/*Test.php"
Grep: "getenv\|_ENV\|_SERVER" --glob "tests/**/*Test.php"
```

**Example (Bad):**
```php
public function test_imports_products(): void
{
    $data = json_decode(file_get_contents('fixtures/products.json'));  // ❌ Hidden
}
```

**Fix:** Inline test data or use explicit builders.
```php
public function test_imports_products(): void
{
    $data = [
        ['name' => 'Book', 'price' => 1000],
        ['name' => 'Pen', 'price' => 100],
    ];

    $this->importer->import($data);

    self::assertCount(2, $this->repository->findAll());
}
```

---

## 6. Eager Test

**Problem:** Single test verifies multiple unrelated behaviors.

**Detection:**
```bash
Grep: "self::assert" --glob "tests/**/*Test.php" -C 5
# Count assertions per test method
```

**Example (Bad):**
```php
public function test_user_operations(): void
{
    // Testing creation
    $user = $this->service->create('john@example.com');
    self::assertNotNull($user);

    // Testing update (different behavior!)
    $user->setName('John');
    self::assertEquals('John', $user->getName());

    // Testing deletion (another behavior!)
    $this->service->delete($user);
    self::assertNull($this->repository->find($user->id));
}
```

**Fix:** One test per behavior.
```php
public function test_creates_user(): void { ... }
public function test_updates_user_name(): void { ... }
public function test_deletes_user(): void { ... }
```

---

## 7. Assertion Roulette

**Problem:** Multiple assertions without messages, unclear which failed.

**Example (Bad):**
```php
public function test_order_properties(): void
{
    self::assertEquals('pending', $order->status);
    self::assertEquals(100, $order->total);
    self::assertEquals(3, count($order->items));
    self::assertEquals('john@example.com', $order->customer->email);
    // Which one failed?
}
```

**Fix:** Group related assertions or split tests.
```php
public function test_order_has_correct_status(): void
{
    self::assertEquals('pending', $order->status);
}

public function test_order_calculates_total(): void
{
    self::assertEquals(100, $order->total);
}
```

---

## 8. Obscure Test

**Problem:** Test purpose unclear from name or structure.

**Detection:**
```bash
Grep: "test_it_works\|test_test\|test_foo" --glob "tests/**/*Test.php"
```

**Example (Bad):**
```php
public function test_it_works(): void  // ❌ What works?
{
    $x = $this->service->doSomething($this->data);
    self::assertTrue($x);
}
```

**Fix:** Descriptive name following convention.
```php
public function test_calculate_total_with_discount_returns_reduced_price(): void
{
    // Clear intent
}
```

---

## 9. Test Code Duplication

**Problem:** Same setup/assertion code repeated across tests.

**Example (Bad):**
```php
public function test_confirm_order(): void
{
    $order = new Order(OrderId::generate(), CustomerId::generate());
    $order->addItem(new Product('Book', Money::EUR(100)));
    // ... same setup in 10 tests
}
```

**Fix:** Extract to setUp, Builder, or Mother.
```php
protected function setUp(): void
{
    $this->order = OrderBuilder::anOrder()->withItem($this->book)->build();
}
```

---

## 10. Conditional Test Logic

**Problem:** Different assertions based on conditions.

**Detection:**
```bash
Grep: "if.*assert\|assert.*if" --glob "tests/**/*Test.php"
```

**Example (Bad):**
```php
public function test_process(): void
{
    $result = $this->service->process($input);
    if ($result !== null) {  // ❌
        self::assertInstanceOf(Order::class, $result);
    } else {
        self::fail('Should not be null');
    }
}
```

**Fix:** Explicit assertions.
```php
public function test_process_returns_order(): void
{
    $result = $this->service->process($input);

    self::assertNotNull($result);
    self::assertInstanceOf(Order::class, $result);
}
```

---

## 11. Hard-Coded Test Data

**Problem:** Magic values without meaning.

**Detection:**
```bash
Grep: "'[a-z0-9]{8,}'" --glob "tests/**/*Test.php"
Grep: "12345\|999\|100" --glob "tests/**/*Test.php"
```

**Example (Bad):**
```php
$order = new Order('550e8400-e29b-41d4-a716-446655440000');  // ❌ Magic UUID
$money = Money::EUR(12345);  // ❌ Magic number
```

**Fix:** Named constants or builders.
```php
private const KNOWN_ORDER_ID = 'order-123';

$order = OrderBuilder::anOrder()
    ->withId(OrderId::fromString(self::KNOWN_ORDER_ID))
    ->withTotal(Money::EUR(100))  // Meaningful amount
    ->build();
```

---

## 12. Testing Private Methods

**Problem:** Tests access private/protected methods directly.

**Detection:**
```bash
Grep: "setAccessible\(true\)" --glob "tests/**/*Test.php"
Grep: "ReflectionMethod\|ReflectionProperty" --glob "tests/**/*Test.php"
```

**Example (Bad):**
```php
$method = new ReflectionMethod(Order::class, 'calculateDiscount');
$method->setAccessible(true);
$result = $method->invoke($order, $amount);  // ❌ Testing internals
```

**Fix:** Test through public API.
```php
$order->applyDiscount($coupon);

self::assertEquals($expectedTotal, $order->total());  // ✅ Public API
```

---

## 13. Slow Test

**Problem:** Unit test takes >100ms.

**Detection:**
```bash
phpunit --log-junit timing.xml
Grep: "sleep\|usleep\|file_\|curl_" --glob "tests/Unit/**/*Test.php"
```

**Fix:** Mock external dependencies, use in-memory implementations.

---

## 14. Mocking Final Classes

**Problem:** Attempting to mock final classes.

**Detection:**
```bash
Grep: "final class" --glob "src/**/*.php"
Grep: "createMock\(.*::" --glob "tests/**/*Test.php"
```

**Fix:** Mock interfaces, not implementations.
```php
// Bad: $mock = $this->createMock(FinalService::class);
// Good:
$mock = $this->createMock(ServiceInterface::class);
```

---

## 15. Mocking Value Objects

**Problem:** Mocking immutable value objects.

**Detection:**
```bash
Grep: "readonly class" --glob "src/**/*.php"
# Check if they're mocked
```

**Fix:** Use real value objects — they're simple and deterministic.
```php
// Bad: $email = $this->createMock(Email::class);
// Good:
$email = new Email('test@example.com');
```
