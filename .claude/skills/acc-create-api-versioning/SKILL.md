---
name: acc-create-api-versioning
description: Generates API Versioning pattern for PHP 8.5. Creates version resolution strategies (URI prefix, Accept header, query parameter), middleware, and deprecation support. Includes unit tests.
---

# API Versioning Generator

Creates API Versioning infrastructure with multiple resolution strategies and deprecation support.

## When to Use

| Scenario | Example |
|----------|---------|
| Breaking API changes | New response format |
| Multiple API consumers | Mobile v1, web v2 |
| Gradual migration | Sunset old versions |
| Backward compatibility | Support legacy clients |

## Component Characteristics

### ApiVersion (Value Object)
- Immutable version representation
- Major and minor version numbers
- Comparison methods (equals, greaterThan, lessThan)
- String parsing (fromString "v1.2")

### VersionResolverInterface
- Extracts version from PSR-7 request
- Returns null if version not found
- Strategy pattern for different sources

### Resolution Strategies
- **UriPrefixVersionResolver** — Extracts from URI path (/v1/orders)
- **AcceptHeaderVersionResolver** — Extracts from Accept header (application/vnd.api.v1+json)
- **QueryParamVersionResolver** — Extracts from query string (?version=1)
- **CompositeVersionResolver** — Tries multiple strategies in order

### VersionMiddleware
- PSR-15 middleware
- Resolves version via strategy
- Adds version to request attributes
- Returns 400 if version required but missing

---

## Generation Process

### Step 1: Generate Domain Components

**Path:** `src/Domain/Shared/Api/`

1. `ApiVersion.php` — Immutable version value object
2. `VersionResolverInterface.php` — Version resolution contract

### Step 2: Generate Presentation Components

**Path:** `src/Presentation/Middleware/`

1. `UriPrefixVersionResolver.php` — URI path strategy
2. `AcceptHeaderVersionResolver.php` — Content negotiation strategy
3. `QueryParamVersionResolver.php` — Query parameter strategy
4. `CompositeVersionResolver.php` — Composite strategy
5. `VersionMiddleware.php` — PSR-15 middleware
6. `DeprecationHeaderMiddleware.php` — Deprecation/Sunset headers

### Step 3: Generate Tests

1. `ApiVersionTest.php` — Value object tests
2. `UriPrefixVersionResolverTest.php` — URI parsing tests
3. `AcceptHeaderVersionResolverTest.php` — Header parsing tests
4. `VersionMiddlewareTest.php` — Middleware behavior tests

---

## File Placement

| Component | Path |
|-----------|------|
| ApiVersion | `src/Domain/Shared/Api/` |
| VersionResolverInterface | `src/Domain/Shared/Api/` |
| Resolvers | `src/Presentation/Middleware/` |
| Middleware | `src/Presentation/Middleware/` |
| Unit Tests | `tests/Unit/` |

---

## Naming Conventions

| Component | Pattern | Example |
|-----------|---------|---------|
| Version VO | `ApiVersion` | `ApiVersion` |
| Resolver Interface | `VersionResolverInterface` | `VersionResolverInterface` |
| Resolver | `{Strategy}VersionResolver` | `UriPrefixVersionResolver` |
| Composite | `CompositeVersionResolver` | `CompositeVersionResolver` |
| Middleware | `VersionMiddleware` | `VersionMiddleware` |
| Deprecation | `DeprecationHeaderMiddleware` | `DeprecationHeaderMiddleware` |
| Test | `{ClassName}Test` | `ApiVersionTest` |

---

## Quick Template Reference

### ApiVersion

```php
final readonly class ApiVersion
{
    public function __construct(
        public int $major,
        public int $minor = 0
    ) {
        if ($this->major < 1) {
            throw new \InvalidArgumentException('Major version must be at least 1');
        }
    }

    public static function fromString(string $version): self;
    public function toString(): string;
    public function equals(self $other): bool;
    public function greaterThan(self $other): bool;
}
```

### VersionResolverInterface

```php
interface VersionResolverInterface
{
    public function resolve(ServerRequestInterface $request): ?ApiVersion;
}
```

---

## Usage Example

```php
// Create composite resolver
$resolver = new CompositeVersionResolver([
    new UriPrefixVersionResolver(),
    new AcceptHeaderVersionResolver(),
    new QueryParamVersionResolver(),
]);

// Middleware adds version to request attributes
$middleware = new VersionMiddleware($resolver, defaultVersion: new ApiVersion(1));

// In action/controller
$version = $request->getAttribute('api_version');
if ($version->greaterThan(new ApiVersion(1))) {
    return $this->respondV2($data);
}
```

---

## Strategy Comparison

| Strategy | URL Example | Pros | Cons |
|----------|-------------|------|------|
| URI Prefix | `/v1/orders` | Explicit, cacheable | URL changes per version |
| Accept Header | `Accept: application/vnd.api.v1+json` | Clean URLs | Complex client setup |
| Query Param | `/orders?version=1` | Simple to test | Not RESTful, caching issues |

---

## Anti-patterns to Avoid

| Anti-pattern | Problem | Solution |
|--------------|---------|----------|
| Version in Body | Hard to route | Use URI/header/query |
| Unlimited Versions | Maintenance burden | Deprecation policy |
| No Default Version | Breaks existing clients | Configure default |
| Breaking Without Version | Client disruption | Always version breaking changes |
| No Deprecation Notice | Surprise removal | Deprecation/Sunset headers |
| Copy-Paste Controllers | Duplicated code | Version-aware routing |

---

## References

For complete PHP templates and examples, see:
- `references/templates.md` — ApiVersion, resolvers, middleware, deprecation templates
- `references/examples.md` — Framework integration and tests
