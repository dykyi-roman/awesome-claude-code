# When to Use Each PSR

## Decision Flowchart

```
START
  │
  ├─► Need code formatting standards?
  │   └─► PSR-1 + PSR-12
  │
  ├─► Need class autoloading?
  │   └─► PSR-4
  │
  ├─► Need logging?
  │   └─► PSR-3
  │
  ├─► Need caching?
  │   ├─► Simple get/set/delete? → PSR-16
  │   └─► Complex (pools, deferred, tags)? → PSR-6
  │
  ├─► Need HTTP handling?
  │   ├─► HTTP messages (request/response)? → PSR-7
  │   ├─► Middleware pipeline? → PSR-15
  │   ├─► Creating HTTP objects? → PSR-17
  │   └─► External HTTP calls? → PSR-18
  │
  ├─► Need dependency injection?
  │   └─► PSR-11
  │
  ├─► Need event system?
  │   └─► PSR-14
  │
  ├─► Need REST API with HATEOAS?
  │   └─► PSR-13
  │
  └─► Need time abstraction?
      └─► PSR-20
```

## Use Cases by Application Type

### Web Application

| Feature | PSRs |
|---------|------|
| Code style | PSR-1, PSR-12 |
| Autoloading | PSR-4 |
| Logging | PSR-3 |
| HTTP handling | PSR-7, PSR-15, PSR-17 |
| Session/cache | PSR-6 or PSR-16 |
| DI Container | PSR-11 |

### REST API

| Feature | PSRs |
|---------|------|
| Code style | PSR-1, PSR-12 |
| Autoloading | PSR-4 |
| HTTP messages | PSR-7, PSR-17 |
| Middleware | PSR-15 |
| External calls | PSR-18 |
| Response caching | PSR-16 |
| HATEOAS links | PSR-13 |

### CLI Application

| Feature | PSRs |
|---------|------|
| Code style | PSR-1, PSR-12 |
| Autoloading | PSR-4 |
| Logging | PSR-3 |
| DI Container | PSR-11 |
| Caching | PSR-16 |

### Event-Driven System

| Feature | PSRs |
|---------|------|
| Code style | PSR-1, PSR-12 |
| Events | PSR-14 |
| Logging | PSR-3 |
| DI Container | PSR-11 |
| External services | PSR-18 |

### Microservice

| Feature | PSRs |
|---------|------|
| All standards | PSR-1, PSR-4, PSR-12 |
| HTTP | PSR-7, PSR-15, PSR-17, PSR-18 |
| Logging | PSR-3 |
| Caching | PSR-6 or PSR-16 |
| Events | PSR-14 |
| DI | PSR-11 |
| Time | PSR-20 |

## PSR Comparison Tables

### Caching: PSR-6 vs PSR-16

| Feature | PSR-6 | PSR-16 |
|---------|-------|--------|
| Complexity | High | Low |
| Cache items | Objects | Values |
| Deferred saves | Yes | No |
| Batch operations | Yes | Yes |
| Tags | Possible | No |
| Use case | Complex caching | Simple caching |

**Choose PSR-6 when:**
- Need deferred/batched saves
- Need cache item metadata
- Building cache framework
- Need tags or pools

**Choose PSR-16 when:**
- Simple get/set operations
- Performance critical
- Minimal abstraction needed
- Quick integration

### HTTP: PSR-7 vs PSR-15 vs PSR-17 vs PSR-18

| PSR | Purpose | When to Use |
|-----|---------|-------------|
| PSR-7 | HTTP messages | Always for HTTP handling |
| PSR-15 | Middleware | Building middleware stacks |
| PSR-17 | Factories | Creating PSR-7 objects |
| PSR-18 | Client | Making external HTTP calls |

**Typical combinations:**
- **API Server:** PSR-7 + PSR-15 + PSR-17
- **API Client:** PSR-7 + PSR-17 + PSR-18
- **Full-stack:** All four

## Integration Patterns

### DDD Application

```php
// Domain Layer
namespace App\Domain\User\Event;
// Uses: None directly (pure PHP)

// Application Layer
namespace App\Application\User\Handler;
use Psr\Log\LoggerInterface;           // PSR-3
use Psr\EventDispatcher\EventDispatcherInterface;  // PSR-14
use Psr\Clock\ClockInterface;          // PSR-20

// Infrastructure Layer
namespace App\Infrastructure\Cache;
use Psr\SimpleCache\CacheInterface;    // PSR-16

namespace App\Infrastructure\Http;
use Psr\Http\Client\ClientInterface;   // PSR-18

// Presentation Layer
namespace App\Presentation\Api;
use Psr\Http\Message\ResponseInterface;           // PSR-7
use Psr\Http\Server\MiddlewareInterface;          // PSR-15
use Psr\Http\Message\ResponseFactoryInterface;    // PSR-17
```

### Hexagonal Architecture

```php
// Core (Domain + Application)
// - PSR-3 for logging ports
// - PSR-14 for event ports
// - PSR-20 for clock ports

// Adapters (Infrastructure)
// - PSR-6/16 for cache adapters
// - PSR-18 for HTTP client adapters
// - PSR-11 for DI container

// Driving Adapters (Presentation)
// - PSR-7 + PSR-15 + PSR-17 for HTTP
```

## Anti-patterns

### Don't Use PSR-6 For:
- Simple key-value caching
- Performance-critical hot paths
- When PSR-16 suffices

### Don't Use PSR-7 For:
- CLI applications (no HTTP)
- Internal service communication (consider gRPC)

### Don't Use PSR-11 For:
- Simple applications without DI
- When manual instantiation suffices

### Don't Use PSR-14 For:
- Direct method calls
- Synchronous-only operations
- When callbacks suffice

## Checklist for New Projects

| Category | PSR | Priority | Notes |
|----------|-----|----------|-------|
| Code Style | PSR-1, PSR-12 | Required | Always use |
| Autoloading | PSR-4 | Required | Always use |
| Logging | PSR-3 | Recommended | For any app with logs |
| HTTP Messages | PSR-7 | Required | For HTTP apps |
| Middleware | PSR-15 | Recommended | For HTTP apps |
| HTTP Factories | PSR-17 | Recommended | For HTTP apps |
| HTTP Client | PSR-18 | Recommended | For external API calls |
| Caching | PSR-16 | Recommended | For apps with caching |
| DI Container | PSR-11 | Optional | For complex apps |
| Events | PSR-14 | Optional | For event-driven apps |
| Links | PSR-13 | Optional | For HATEOAS APIs |
| Clock | PSR-20 | Optional | For testable time |
