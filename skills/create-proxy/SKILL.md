---
name: acc-create-proxy
description: Generates Proxy pattern for PHP 8.4. Controls access, adds lazy loading, caching, logging. Includes unit tests.
---

# Proxy Pattern Generator

Creates Proxy pattern infrastructure for controlling access to objects.

## When to Use

| Scenario | Example |
|----------|---------|
| Lazy initialization | Load expensive resources on first access |
| Access control | Check permissions before delegating |
| Caching | Cache results of expensive operations |
| Logging | Log calls to real subject |

## Component Characteristics

### Subject Interface
- Defines operations
- Shared by proxy and real subject
- Enables transparent substitution

### Real Subject
- Actual implementation
- Contains business logic
- May be expensive to create

### Proxy
- Implements subject interface
- Controls access to real subject
- Adds additional behavior

---

## Generation Process

### Step 1: Generate Subject Interface

**Path:** `src/Domain/{BoundedContext}/`

1. `{Name}Interface.php` — Operations contract

### Step 2: Generate Proxy

**Path:** `src/Infrastructure/{BoundedContext}/Proxy/`

1. `Lazy{Name}Proxy.php` — Lazy initialization
2. `Caching{Name}Proxy.php` — Result caching
3. `AccessControl{Name}Proxy.php` — Permission checks
4. `Logging{Name}Proxy.php` — Call logging

### Step 3: Generate Tests

1. `{ProxyName}Test.php` — Proxy behavior verification

---

## File Placement

| Component | Path |
|-----------|------|
| Subject Interface | `src/Domain/{BoundedContext}/` |
| Real Subject | `src/Domain/` or `src/Infrastructure/` |
| Proxy | `src/Infrastructure/{BoundedContext}/Proxy/` |
| Unit Tests | `tests/Unit/Infrastructure/{BoundedContext}/Proxy/` |

---

## Naming Conventions

| Component | Pattern | Example |
|-----------|---------|---------|
| Subject Interface | `{Name}Interface` | `RepositoryInterface` |
| Real Subject | `{Name}` | `UserRepository` |
| Proxy | `{Type}{Name}Proxy` | `LazyUserRepositoryProxy` |
| Test | `{ClassName}Test` | `LazyUserRepositoryProxyTest` |

---

## Quick Template Reference

### Proxy

```php
final class {Type}{Name}Proxy implements {Name}Interface
{
    private ?{Name}Interface $realSubject = null;

    public function __construct(
        private \Closure $factory
    ) {}

    public function {operation}({params}): {returnType}
    {
        {beforeBehavior}

        $result = $this->getRealSubject()->{operation}({args});

        {afterBehavior}

        return $result;
    }

    private function getRealSubject(): {Name}Interface
    {
        if ($this->realSubject === null) {
            $this->realSubject = ($this->factory)();
        }

        return $this->realSubject;
    }
}
```

---

## Usage Example

```php
// Lazy loading proxy
$repository = new LazyUserRepositoryProxy(
    fn() => new UserRepository($connection)
);

// Real subject created only on first call
$user = $repository->findById($id);
```

---

## Common Proxies

| Proxy | Purpose |
|-------|---------|
| LazyLoadingProxy | Defer expensive object creation |
| CachingProxy | Cache method results |
| AccessControlProxy | Check permissions before execution |
| LoggingProxy | Log all method calls |
| MetricsProxy | Collect performance metrics |
| RetryProxy | Retry failed operations |

---

## Anti-patterns to Avoid

| Anti-pattern | Problem | Solution |
|--------------|---------|----------|
| Proxy != Real Subject | Behavior differs | Proxy must be transparent |
| Heavy Proxy | Too much logic | Keep proxies focused |
| Missing Interface | Can't substitute proxy | Use shared interface |
| Leaky State | Proxy state affects behavior | Keep proxies stateless when possible |
| Multiple Responsibilities | Proxy does many things | One proxy, one concern |

---

## References

For complete PHP templates and examples, see:
- `references/templates.md` — Lazy loading, caching, access control proxy templates
- `references/examples.md` — Repository, service proxies with unit tests
