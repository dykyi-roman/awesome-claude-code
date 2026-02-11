# Correlation Context — Integration Examples

Examples for integrating Correlation ID propagation in PHP frameworks and message systems.

---

## Symfony Integration

### Service Configuration

```yaml
# config/services.yaml
services:
    App\Infrastructure\Logging\CorrelationLogProcessor:
        tags:
            - { name: monolog.processor }

    App\Presentation\Middleware\CorrelationContextMiddleware:
        tags:
            - { name: kernel.event_listener, event: kernel.request, priority: 255 }
```

### Symfony Messenger Middleware

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Messaging\Middleware;

use App\Domain\Shared\Correlation\CorrelationContext;
use App\Infrastructure\Messaging\CorrelationMessageStamp;
use Symfony\Component\Messenger\Envelope;
use Symfony\Component\Messenger\Middleware\MiddlewareInterface;
use Symfony\Component\Messenger\Middleware\StackInterface;

final readonly class CorrelationMessengerMiddleware implements MiddlewareInterface
{
    public function __construct(
        private CorrelationLogProcessor $logProcessor,
    ) {
    }

    public function handle(Envelope $envelope, StackInterface $stack): Envelope
    {
        $stamp = $envelope->last(CorrelationMessageStamp::class);

        if ($stamp === null) {
            $context = CorrelationContext::create();
            $envelope = $envelope->with(CorrelationMessageStamp::fromContext($context));
        } else {
            $context = new CorrelationContext(
                correlationId: new \App\Domain\Shared\Correlation\CorrelationId($stamp->correlationId),
                causationId: $stamp->causationId,
            );
        }

        $this->logProcessor->setContext($context);

        return $stack->next()->handle($envelope, $stack);
    }
}
```

### Messenger Configuration

```yaml
# config/packages/messenger.yaml
framework:
    messenger:
        buses:
            command.bus:
                middleware:
                    - App\Infrastructure\Messaging\Middleware\CorrelationMessengerMiddleware
```

---

## Laravel Integration

### HTTP Middleware

```php
<?php

declare(strict_types=1);

namespace App\Http\Middleware;

use App\Domain\Shared\Correlation\CorrelationContext;
use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;

final class CorrelationIdMiddleware
{
    public function handle(Request $request, Closure $next): Response
    {
        $correlationId = $request->header('X-Correlation-ID')
            ?? \App\Domain\Shared\Correlation\CorrelationId::generate()->value;

        $context = new CorrelationContext(
            correlationId: new \App\Domain\Shared\Correlation\CorrelationId($correlationId),
            causationId: $request->header('X-Causation-ID'),
        );

        app()->instance(CorrelationContext::class, $context);

        /** @var Response $response */
        $response = $next($request);

        $response->headers->set('X-Correlation-ID', $context->correlationId->value);

        return $response;
    }
}
```

### Kernel Registration

```php
// app/Http/Kernel.php
protected $middleware = [
    \App\Http\Middleware\CorrelationIdMiddleware::class,
    // ...
];
```

---

## RabbitMQ / AMQP Integration

### Publishing with Correlation Headers

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Messaging;

use App\Domain\Shared\Correlation\CorrelationContext;
use PhpAmqpLib\Message\AMQPMessage;

final readonly class CorrelationAwarePublisher
{
    public function __construct(
        private \PhpAmqpLib\Channel\AMQPChannel $channel,
    ) {
    }

    public function publish(
        string $exchange,
        string $routingKey,
        string $body,
        CorrelationContext $context,
    ): void {
        $message = new AMQPMessage($body, [
            'application_headers' => new \PhpAmqpLib\Wire\AMQPTable([
                'X-Correlation-ID' => $context->correlationId->value,
                'X-Causation-ID' => $context->causationId ?? '',
            ]),
        ]);

        $this->channel->basic_publish($message, $exchange, $routingKey);
    }
}
```

### Consuming with Correlation Extraction

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Messaging;

use App\Domain\Shared\Correlation\CorrelationContext;
use App\Domain\Shared\Correlation\CorrelationId;
use PhpAmqpLib\Message\AMQPMessage;

final readonly class CorrelationExtractor
{
    public function extractContext(AMQPMessage $message): CorrelationContext
    {
        $headers = $message->get('application_headers')?->getNativeData() ?? [];

        $correlationId = isset($headers['X-Correlation-ID']) && $headers['X-Correlation-ID'] !== ''
            ? new CorrelationId($headers['X-Correlation-ID'])
            : CorrelationId::generate();

        $causationId = isset($headers['X-Causation-ID']) && $headers['X-Causation-ID'] !== ''
            ? $headers['X-Causation-ID']
            : null;

        return new CorrelationContext(
            correlationId: $correlationId,
            causationId: $causationId,
        );
    }
}
```

---

## Guzzle HTTP Client (Outbound Propagation)

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Http;

use App\Domain\Shared\Correlation\CorrelationContext;
use GuzzleHttp\Client;
use Psr\Http\Message\ResponseInterface;

final readonly class CorrelationAwareHttpClient
{
    public function __construct(
        private Client $client,
        private CorrelationContext $context,
    ) {
    }

    public function request(string $method, string $uri, array $options = []): ResponseInterface
    {
        $options['headers'] = array_merge($options['headers'] ?? [], [
            'X-Correlation-ID' => $this->context->correlationId->value,
            'X-Causation-ID' => $this->context->causationId ?? '',
        ]);

        return $this->client->request($method, $uri, $options);
    }
}
```

---

## DI Container Configuration (PHP-DI)

```php
<?php

declare(strict_types=1);

use App\Domain\Shared\Correlation\CorrelationContext;
use App\Infrastructure\Logging\CorrelationLogProcessor;
use App\Presentation\Middleware\CorrelationContextMiddleware;

return [
    CorrelationContextMiddleware::class => \DI\autowire(),

    CorrelationLogProcessor::class => \DI\autowire(),

    CorrelationContext::class => \DI\factory(function () {
        return CorrelationContext::create();
    }),
];
```
