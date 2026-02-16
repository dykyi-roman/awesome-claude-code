---
name: acc-check-async-patterns
description: Detects synchronous operations that should be async. Identifies blocking email sends, in-request API calls, heavy processing in request cycle, and missing queue offloading.
---

# Async Patterns Audit

Analyze PHP code for synchronous operations that should be handled asynchronously to improve response times and system resilience.

## Detection Patterns

### 1. Email Sending in Request Cycle

```php
// CRITICAL: Blocking email send in HTTP request
class RegistrationController
{
    public function register(Request $request): Response
    {
        $user = $this->userService->create($request->validated());
        $this->mailer->send(new WelcomeEmail($user));  // Blocks 2-5 seconds!
        return new Response('Registered', 201);
        // User waits for email server response
    }
}

// CORRECT: Dispatch to queue
class RegistrationController
{
    public function register(Request $request): Response
    {
        $user = $this->userService->create($request->validated());
        $this->messageBus->dispatch(new SendWelcomeEmail($user->id()));
        return new Response('Registered', 201);
        // Response immediate, email sent by worker
    }
}
```

### 2. External API Call in Request Path

```php
// CRITICAL: Third-party API call blocks request
class OrderController
{
    public function create(Request $request): Response
    {
        $order = $this->orderService->create($request->validated());
        $tracking = $this->shippingApi->createShipment($order);  // 1-10 seconds!
        $this->notificationApi->send($order->userId(), 'Order created');  // 1-3 seconds!
        $this->analyticsApi->track('order_created', $order->toArray());   // 0.5-2 seconds!
        return new Response($order, 201);
        // Total: 3-15 seconds blocked!
    }
}

// CORRECT: Only essential ops synchronous
class OrderController
{
    public function create(Request $request): Response
    {
        $order = $this->orderService->create($request->validated());
        // Async: shipping, notifications, analytics
        $this->eventBus->dispatch(new OrderCreated($order->id()));
        return new Response($order, 201);
    }
}
```

### 3. PDF/Report Generation in Request

```php
// CRITICAL: Heavy processing blocks request
class ReportController
{
    public function generate(Request $request): Response
    {
        $data = $this->reportService->collectData($request->get('dateRange'));  // 5-30s
        $pdf = $this->pdfGenerator->generate($data);  // 2-10s
        return new Response($pdf, 200, ['Content-Type' => 'application/pdf']);
        // User stares at spinner for 30+ seconds
    }
}

// CORRECT: Async generation with polling/webhook
class ReportController
{
    public function request(Request $request): Response
    {
        $jobId = $this->reportService->requestGeneration($request->get('dateRange'));
        return new Response(['jobId' => $jobId, 'status' => 'processing'], 202);
    }

    public function status(string $jobId): Response
    {
        $job = $this->reportService->getStatus($jobId);
        return new Response($job); // { status: 'completed', downloadUrl: '...' }
    }
}
```

### 4. Image/File Processing in Request

```php
// CRITICAL: Image processing in upload handler
class ImageController
{
    public function upload(Request $request): Response
    {
        $file = $request->file('image');
        $this->imageService->resize($file, [800, 600]);      // CPU intensive
        $this->imageService->generateThumbnail($file, [200, 200]); // CPU intensive
        $this->imageService->optimizePng($file);              // CPU intensive
        $this->cdn->upload($file);                            // Network I/O
        return new Response('Uploaded', 201);
    }
}

// CORRECT: Upload fast, process async
class ImageController
{
    public function upload(Request $request): Response
    {
        $file = $request->file('image');
        $path = $this->storage->putTemporary($file);
        $this->queue->dispatch(new ProcessImage($path));
        return new Response(['status' => 'processing'], 202);
    }
}
```

### 5. Bulk Operations in Single Request

```php
// CRITICAL: Processing 1000 items synchronously
class ImportController
{
    public function import(Request $request): Response
    {
        $rows = $this->csvParser->parse($request->file('data'));
        foreach ($rows as $row) {
            $this->productService->createOrUpdate($row); // N database operations
        }
        return new Response('Imported ' . count($rows));
        // Timeout after 30s / 100 items
    }
}

// CORRECT: Chunked async processing
class ImportController
{
    public function import(Request $request): Response
    {
        $path = $this->storage->putTemporary($request->file('data'));
        $jobId = $this->importService->startImport($path);
        return new Response(['jobId' => $jobId], 202);
    }
}
```

### 6. Webhook/Notification Fan-Out

```php
// CRITICAL: Sending to multiple endpoints sequentially
class WebhookService
{
    public function notify(Event $event): void
    {
        $subscribers = $this->subscriberRepo->findByEvent($event->name());
        foreach ($subscribers as $subscriber) {
            $this->httpClient->post($subscriber->url(), $event->payload());
            // Each call: 1-5 seconds. 10 subscribers = 10-50 seconds!
        }
    }
}

// CORRECT: Dispatch to queue
class WebhookService
{
    public function notify(Event $event): void
    {
        $subscribers = $this->subscriberRepo->findByEvent($event->name());
        foreach ($subscribers as $subscriber) {
            $this->queue->dispatch(new DeliverWebhook($subscriber->id(), $event));
        }
    }
}
```

## Grep Patterns

```bash
# Email sending in controllers/use cases
Grep: "->send\(.*Mail|->send\(.*Email|mailer->send" --glob "**/*Controller*.php"
Grep: "->send\(.*Mail|->send\(.*Email|mailer->send" --glob "**/*UseCase*.php"

# External API calls in request path
Grep: "->post\(|->get\(|->request\(" --glob "**/*Controller*.php"
Grep: "->post\(|->get\(|->request\(" --glob "**/*Action*.php"

# PDF generation
Grep: "pdf->generate|generatePdf|Dompdf|Snappy|mpdf" --glob "**/*Controller*.php"

# Image processing
Grep: "imagecreatefrom|GdImage|Imagick|InterventionImage" --glob "**/*Controller*.php"

# Bulk operations
Grep: "foreach.*->create\(|foreach.*->save\(|foreach.*->update\(" --glob "**/*Controller*.php"

# Sequential HTTP calls in loop
Grep: "foreach.*->post\(|foreach.*->send\(" --glob "**/*.php"
```

## Severity Classification

| Pattern | Severity |
|---------|----------|
| Email sending in request cycle | 🔴 Critical |
| Multiple external API calls in request | 🔴 Critical |
| PDF/report generation in request | 🟠 Major |
| Image processing in request | 🟠 Major |
| Bulk import without chunking | 🟠 Major |
| Webhook fan-out synchronously | 🟡 Minor |

## Output Format

```markdown
### Async Pattern: [Description]

**Severity:** 🔴/🟠/🟡
**Location:** `file.php:line`
**Estimated Block Time:** X-Y seconds

**Issue:**
[Synchronous operation that should be async]

**Impact:**
- Response time: +Xs per request
- Under load: thread pool exhaustion
- User experience: unacceptable wait

**Code:**
```php
// Synchronous blocking code
```

**Fix:**
```php
// Offloaded to queue/async
```

**Architecture:**
Request → Queue → Worker → Complete
```
