# PSR Selection Guide

## Project Information

| Field | Value |
|-------|-------|
| **Project** | {PROJECT_NAME} |
| **Type** | {PROJECT_TYPE} |
| **Date** | {DATE} |

## Quick Selection

Based on your project type, select the recommended PSRs:

### Web Application
- [x] PSR-1, PSR-12 (Code Style)
- [x] PSR-4 (Autoloading)
- [x] PSR-3 (Logging)
- [x] PSR-7, PSR-15, PSR-17 (HTTP)
- [x] PSR-11 (DI Container)
- [ ] PSR-6 or PSR-16 (Caching)
- [ ] PSR-14 (Events)
- [ ] PSR-20 (Clock)

### REST API
- [x] PSR-1, PSR-12 (Code Style)
- [x] PSR-4 (Autoloading)
- [x] PSR-3 (Logging)
- [x] PSR-7, PSR-15, PSR-17 (HTTP)
- [x] PSR-18 (HTTP Client for external APIs)
- [ ] PSR-13 (Hypermedia Links)
- [ ] PSR-16 (Response Caching)

### CLI Application
- [x] PSR-1, PSR-12 (Code Style)
- [x] PSR-4 (Autoloading)
- [x] PSR-3 (Logging)
- [ ] PSR-11 (DI Container)
- [ ] PSR-16 (Caching)

### Library/Package
- [x] PSR-1, PSR-12 (Code Style)
- [x] PSR-4 (Autoloading)
- [ ] PSR-3 (if logging needed)
- [ ] Other PSRs based on functionality

### Microservice
- [x] All PSRs typically needed
- [x] Focus on HTTP (PSR-7, 15, 17, 18)
- [x] Events (PSR-14) for async
- [x] Caching (PSR-6 or PSR-16)

## Detailed Selection Checklist

### Code Quality (Required)

| PSR | Need | Selected |
|-----|------|----------|
| PSR-1 | Basic coding standard | [ ] |
| PSR-12 | Extended coding style | [ ] |
| PSR-4 | Class autoloading | [ ] |

### HTTP Handling

| PSR | Need | Selected |
|-----|------|----------|
| PSR-7 | HTTP message abstraction | [ ] |
| PSR-15 | Middleware pipeline | [ ] |
| PSR-17 | HTTP object factories | [ ] |
| PSR-18 | External HTTP calls | [ ] |
| PSR-13 | HATEOAS/hypermedia | [ ] |

### Application Services

| PSR | Need | Selected |
|-----|------|----------|
| PSR-3 | Logging | [ ] |
| PSR-11 | Dependency injection | [ ] |
| PSR-14 | Event dispatching | [ ] |
| PSR-20 | Time abstraction | [ ] |

### Data Management

| PSR | Need | Selected |
|-----|------|----------|
| PSR-6 | Complex caching | [ ] |
| PSR-16 | Simple caching | [ ] |

## Composer Configuration

Based on your selection, add to `composer.json`:

```json
{
    "require": {
        "php": "^8.5",

        // Always required
        "psr/log": "^3.0",

        // HTTP Stack (select based on needs)
        "psr/http-message": "^2.0",
        "psr/http-server-handler": "^1.0",
        "psr/http-server-middleware": "^1.0",
        "psr/http-factory": "^1.1",
        "psr/http-client": "^1.0",

        // Services (select based on needs)
        "psr/container": "^2.0",
        "psr/event-dispatcher": "^1.0",
        "psr/clock": "^1.0",

        // Caching (choose one)
        "psr/cache": "^3.0",
        "psr/simple-cache": "^3.0",

        // Optional
        "psr/link": "^2.0"
    }
}
```

## Implementation Recommendations

### PSR-3: Logger

| Package | Pros | Cons |
|---------|------|------|
| `monolog/monolog` | Feature-rich, widely used | Heavier |
| `laminas/laminas-log` | Modular | Less popular |
| Custom | Minimal, tailored | Maintenance burden |

**Recommendation:** `monolog/monolog`

### PSR-6/PSR-16: Cache

| Package | Pros | Cons |
|---------|------|------|
| `symfony/cache` | Both PSR-6 and PSR-16 | Symfony dependency |
| `cache/filesystem-adapter` | Lightweight | Limited features |
| `phpfastcache/phpfastcache` | Many drivers | Complex |

**Recommendation:** `symfony/cache`

### PSR-7/PSR-17: HTTP Message

| Package | Pros | Cons |
|---------|------|------|
| `nyholm/psr7` | Lightweight, fast | Minimal |
| `guzzlehttp/psr7` | Feature-rich | Heavier |
| `laminas/laminas-diactoros` | Complete | Verbose |

**Recommendation:** `nyholm/psr7`

### PSR-11: Container

| Package | Pros | Cons |
|---------|------|------|
| `php-di/php-di` | Autowiring | Learning curve |
| `league/container` | Flexible | Less automatic |
| `pimple/pimple` | Simple | Manual wiring |

**Recommendation:** `php-di/php-di`

### PSR-14: Event Dispatcher

| Package | Pros | Cons |
|---------|------|------|
| `symfony/event-dispatcher` | Powerful | Symfony patterns |
| `league/event` | Simple | Less features |

**Recommendation:** `symfony/event-dispatcher`

### PSR-15: Middleware

| Package | Pros | Cons |
|---------|------|------|
| `middlewares/utils` | Utilities | Needs dispatcher |
| `relay/relay` | Simple | Minimal |

**Recommendation:** `relay/relay` + framework integration

### PSR-18: HTTP Client

| Package | Pros | Cons |
|---------|------|------|
| `guzzlehttp/guzzle` | Feature-rich | Heavy |
| `symfony/http-client` | PSR-18 native | Symfony style |

**Recommendation:** `symfony/http-client`

### PSR-20: Clock

| Package | Pros | Cons |
|---------|------|------|
| `symfony/clock` | Integration | Symfony dependency |
| `lcobucci/clock` | Simple | Minimal |

**Recommendation:** `lcobucci/clock`

## Summary

### Selected PSRs

| PSR | Selected | Implementation |
|-----|----------|----------------|
| PSR-1 | {YES/NO} | PHP-CS-Fixer |
| PSR-3 | {YES/NO} | {PACKAGE} |
| PSR-4 | {YES/NO} | Composer |
| PSR-6 | {YES/NO} | {PACKAGE} |
| PSR-7 | {YES/NO} | {PACKAGE} |
| PSR-11 | {YES/NO} | {PACKAGE} |
| PSR-12 | {YES/NO} | PHP-CS-Fixer |
| PSR-13 | {YES/NO} | {PACKAGE} |
| PSR-14 | {YES/NO} | {PACKAGE} |
| PSR-15 | {YES/NO} | {PACKAGE} |
| PSR-16 | {YES/NO} | {PACKAGE} |
| PSR-17 | {YES/NO} | {PACKAGE} |
| PSR-18 | {YES/NO} | {PACKAGE} |
| PSR-20 | {YES/NO} | {PACKAGE} |

---

*Generated by Claude Code PSR Selection Guide*
