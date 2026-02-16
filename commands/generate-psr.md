---
description: Generate PSR-compliant components. Creates PSR-3 loggers, PSR-6/16 caches, PSR-7/17/18 HTTP, PSR-11 containers, PSR-14 events, PSR-15 middleware, PSR-13 links, PSR-20 clocks.
allowed-tools: Read, Write, Edit, Glob, Grep, Task
model: sonnet
argument-hint: <psr-number> <ComponentName> [-- additional instructions]
---

# Generate PSR Component

Generate PHP-FIG compliant PSR implementations with tests.

## Input Parsing

Parse `$ARGUMENTS` to extract PSR number, component name, and optional meta-instructions:

```
Format: <psr-number> <ComponentName> [-- <meta-instructions>]

Examples:
- /acc-generate-psr psr-3 FileLogger
- /acc-generate-psr psr-15 AuthMiddleware
- /acc-generate-psr psr-6 RedisCache -- with TTL support
- /acc-generate-psr psr-7 -- generate full HTTP stack
```

**Parsing rules:**
1. First part = **PSR number** (required: psr-3, psr-6, psr-7, etc.)
2. Second part = **Component name** (optional for some PSRs)
3. After ` -- ` = **meta-instructions** (optional customizations)

## Supported PSRs

| PSR | Name | Components Generated |
|-----|------|---------------------|
| **psr-3** | Logger Interface | LoggerInterface, AbstractLogger, LogLevel |
| **psr-6** | Caching Interface | CacheItemPoolInterface, CacheItemInterface |
| **psr-7** | HTTP Message | Request, Response, Uri, Stream, ServerRequest |
| **psr-11** | Container Interface | ContainerInterface, NotFoundExceptionInterface |
| **psr-13** | Hypermedia Links | LinkInterface, EvolvableLinkInterface |
| **psr-14** | Event Dispatcher | EventDispatcherInterface, StoppableEventInterface |
| **psr-15** | HTTP Handlers | RequestHandlerInterface, MiddlewareInterface |
| **psr-16** | Simple Cache | CacheInterface, InvalidArgumentException |
| **psr-17** | HTTP Factories | RequestFactoryInterface, ResponseFactoryInterface |
| **psr-18** | HTTP Client | ClientInterface, ClientExceptionInterface |
| **psr-20** | Clock | ClockInterface |

## Pre-flight Check

1. Verify valid PSR number:
   - If not provided, ask user which PSR to generate
   - If invalid PSR number, show list of supported PSRs

2. Check project structure:
   - Read `composer.json` for namespace configuration
   - Determine target directory structure

## Instructions

Use the `acc-psr-generator` agent to generate PSR-compliant components:

```
Task tool with subagent_type="acc-psr-generator"
prompt: "Generate [PSR] implementation for [COMPONENT_NAME]. [META-INSTRUCTIONS if provided]

Requirements:
1. PHP 8.4 with declare(strict_types=1)
2. PSR-12 coding style
3. Final readonly classes where appropriate
4. Constructor property promotion
5. Include unit tests
6. Include usage examples

Target structure:
src/Infrastructure/{Component}/
├── {Interface}Interface.php
├── {Implementation}.php
└── Exception/
    └── {Component}Exception.php

tests/Unit/Infrastructure/{Component}/
└── {Implementation}Test.php"
```

## Generation Examples

### PSR-3: Logger
```bash
/acc-generate-psr psr-3 FileLogger
/acc-generate-psr psr-3 JsonLogger -- with context processors
```

Generates:
- `LoggerInterface` implementation
- Log level handling
- Context interpolation
- File/JSON/Console output

### PSR-6: Cache Pool
```bash
/acc-generate-psr psr-6 RedisCache
/acc-generate-psr psr-6 ArrayCache -- for testing
```

Generates:
- `CacheItemPoolInterface` implementation
- `CacheItem` class
- Deferred save support
- TTL handling

### PSR-7: HTTP Message
```bash
/acc-generate-psr psr-7
/acc-generate-psr psr-7 -- with uploaded files support
```

Generates:
- Request, Response, ServerRequest
- Uri, Stream, UploadedFile
- Immutable implementations

### PSR-11: Container
```bash
/acc-generate-psr psr-11 SimpleContainer
/acc-generate-psr psr-11 -- with auto-wiring
```

Generates:
- `ContainerInterface` implementation
- Service registration
- Dependency resolution

### PSR-14: Event Dispatcher
```bash
/acc-generate-psr psr-14 EventDispatcher
/acc-generate-psr psr-14 -- with prioritized listeners
```

Generates:
- `EventDispatcherInterface` implementation
- Listener provider
- Stoppable events support

### PSR-15: Middleware
```bash
/acc-generate-psr psr-15 AuthMiddleware
/acc-generate-psr psr-15 CorsMiddleware
/acc-generate-psr psr-15 RateLimitMiddleware
```

Generates:
- `MiddlewareInterface` implementation
- Request handler chain
- Response modification

### PSR-16: Simple Cache
```bash
/acc-generate-psr psr-16 MemoryCache
/acc-generate-psr psr-16 FileCache -- with serialization
```

Generates:
- `CacheInterface` implementation
- TTL handling
- Multiple/batch operations

### PSR-17: HTTP Factories
```bash
/acc-generate-psr psr-17
/acc-generate-psr psr-17 -- with PSR-7 integration
```

Generates:
- Request, Response, Stream factories
- Uri, UploadedFile factories

### PSR-18: HTTP Client
```bash
/acc-generate-psr psr-18 GuzzleAdapter
/acc-generate-psr psr-18 CurlClient
```

Generates:
- `ClientInterface` implementation
- Request sending
- Exception handling

### PSR-20: Clock
```bash
/acc-generate-psr psr-20 SystemClock
/acc-generate-psr psr-20 FrozenClock -- for testing
```

Generates:
- `ClockInterface` implementation
- System clock
- Test-friendly frozen clock

## Expected Output

### Generated Files

```
Generated PSR-15 Middleware: AuthMiddleware

Files created:
├── src/Infrastructure/Http/Middleware/
│   ├── AuthMiddleware.php
│   └── Exception/
│       └── UnauthorizedException.php
└── tests/Unit/Infrastructure/Http/Middleware/
    └── AuthMiddlewareTest.php
```

### Code Preview

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Http\Middleware;

use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\MiddlewareInterface;
use Psr\Http\Server\RequestHandlerInterface;

final readonly class AuthMiddleware implements MiddlewareInterface
{
    public function __construct(
        private TokenValidatorInterface $tokenValidator,
    ) {
    }

    public function process(
        ServerRequestInterface $request,
        RequestHandlerInterface $handler,
    ): ResponseInterface {
        // Implementation...
    }
}
```

### Integration Instructions

```php
// DI Container configuration
$container->set(MiddlewareInterface::class, AuthMiddleware::class);

// Usage in middleware pipeline
$pipeline->pipe(new AuthMiddleware($tokenValidator));
```

## Common Combinations

### Full HTTP Stack (PSR-7 + PSR-15 + PSR-17 + PSR-18)
```bash
/acc-generate-psr psr-7 -- HTTP messages
/acc-generate-psr psr-17 -- factories
/acc-generate-psr psr-15 Pipeline -- middleware
/acc-generate-psr psr-18 HttpClient
```

### Caching Layer
```bash
/acc-generate-psr psr-6 RedisPool -- full cache with pools
# or
/acc-generate-psr psr-16 SimpleRedis -- simple get/set
```

### Infrastructure Services
```bash
/acc-generate-psr psr-3 AppLogger
/acc-generate-psr psr-11 Container
/acc-generate-psr psr-14 EventBus
/acc-generate-psr psr-20 Clock
```

## Usage Examples

```bash
/acc-generate-psr psr-3 FileLogger
/acc-generate-psr psr-15 AuthMiddleware
/acc-generate-psr psr-6 RedisCache -- with TTL and tags support
/acc-generate-psr psr-7 -- generate complete HTTP message stack
/acc-generate-psr psr-20 FrozenClock -- for unit testing time-dependent code
```
