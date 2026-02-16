---
name: acc-check-mass-assignment
description: Detects mass assignment vulnerabilities. Identifies unguarded model filling, Request::all() to create/update, missing $fillable/$guarded, and parameter binding without whitelisting.
---

# Mass Assignment Security Check (A01:2021)

Analyze PHP code for mass assignment vulnerabilities where user input directly populates model attributes.

## Detection Patterns

### 1. Request::all() Passed to Create/Update

```php
// CRITICAL: All request data used to create model
class UserController
{
    public function store(Request $request): Response
    {
        $user = User::create($request->all());
        // Attacker can set: is_admin=true, role=superadmin, balance=999999
        return new Response($user);
    }
}

// CRITICAL: All input to update
class ProfileController
{
    public function update(Request $request, int $id): Response
    {
        $user = User::findOrFail($id);
        $user->update($request->all());
        // Attacker modifies fields not in the form
    }
}

// CORRECT: Whitelist specific fields
class UserController
{
    public function store(Request $request): Response
    {
        $user = User::create($request->only(['name', 'email', 'password']));
        return new Response($user);
    }
}
```

### 2. Missing $fillable or $guarded (Laravel)

```php
// CRITICAL: No mass assignment protection
class User extends Model
{
    // No $fillable defined — all fields assignable!
    // No $guarded defined — nothing protected!
}

// VULNERABLE: Empty guarded (allows everything)
class User extends Model
{
    protected $guarded = []; // Disables ALL protection!
}

// CORRECT: Explicit fillable
class User extends Model
{
    protected $fillable = ['name', 'email', 'password'];
    // is_admin, role, etc. are NOT fillable
}
```

### 3. Array Spread / Merge Into Entity

```php
// CRITICAL: Unfiltered array to entity constructor
class CreateUserUseCase
{
    public function execute(array $data): User
    {
        return new User(...$data); // Any key becomes a constructor argument!
    }
}

// CRITICAL: Array merge with user input
class UpdateHandler
{
    public function handle(UpdateCommand $command): void
    {
        $entity = $this->repo->find($command->id());
        $merged = array_merge($entity->toArray(), $command->data());
        // User-supplied data overrides ALL fields
        $this->repo->save(User::fromArray($merged));
    }
}

// CORRECT: Explicit mapping
class CreateUserUseCase
{
    public function execute(CreateUserCommand $command): User
    {
        return new User(
            name: $command->name(),
            email: $command->email(),
            // Only mapped fields, no mass assignment
        );
    }
}
```

### 4. Doctrine Entity Public Setters

```php
// VULNERABLE: All setters exposed, bulk update possible
class User
{
    public function setRole(string $role): void { $this->role = $role; }
    public function setIsAdmin(bool $isAdmin): void { $this->isAdmin = $isAdmin; }
    public function setBalance(int $balance): void { $this->balance = $balance; }
}

// Combined with:
foreach ($request->all() as $key => $value) {
    $setter = 'set' . ucfirst($key);
    if (method_exists($user, $setter)) {
        $user->$setter($value); // Mass assignment via reflection!
    }
}
```

### 5. API Resource Without Field Filtering

```php
// VULNERABLE: PATCH endpoint accepts any field
class UserApiController
{
    public function patch(Request $request, int $id): Response
    {
        $user = $this->repo->find($id);
        $data = json_decode($request->getContent(), true);
        foreach ($data as $field => $value) {
            $user->{'set' . ucfirst($field)}($value); // Any field!
        }
    }
}

// CORRECT: Explicit allowed fields for PATCH
class UserApiController
{
    private const array PATCHABLE_FIELDS = ['name', 'email', 'phone'];

    public function patch(Request $request, int $id): Response
    {
        $user = $this->repo->find($id);
        $data = json_decode($request->getContent(), true);
        foreach ($data as $field => $value) {
            if (!in_array($field, self::PATCHABLE_FIELDS, true)) {
                throw new BadRequestException("Field '$field' is not modifiable");
            }
        }
    }
}
```

## Grep Patterns

```bash
# Request::all() to create/update
Grep: "::create\(\\\$request->all\(\)\)|->update\(\\\$request->all\(\)\)" --glob "**/*.php"
Grep: "request->all\(\)" --glob "**/*Controller*.php"

# Missing fillable/guarded (Laravel)
Grep: "extends Model" --glob "**/*.php"
Grep: "\\\$fillable|\\\$guarded" --glob "**/*.php"

# Empty guarded
Grep: "\\\$guarded = \[\]" --glob "**/*.php"

# Array spread to constructor
Grep: "new.*\(\.\.\.\\\$" --glob "**/*.php"

# Dynamic setters
Grep: "->.*\\\$.*\(|method_exists.*set" --glob "**/*.php"

# array_merge with user input
Grep: "array_merge\(.*request|array_merge\(.*\\\$data" --glob "**/*.php"
```

## Severity Classification

| Pattern | Severity |
|---------|----------|
| Request::all() to create/update | 🔴 Critical |
| Empty $guarded = [] | 🔴 Critical |
| Dynamic setters from user input | 🔴 Critical |
| Missing $fillable on Model | 🟠 Major |
| Array spread from unvalidated input | 🟠 Major |
| No field whitelist on PATCH | 🟡 Minor |

## Output Format

```markdown
### Mass Assignment: [Description]

**Severity:** 🔴/🟠/🟡
**Location:** `file.php:line`
**CWE:** CWE-915 (Improperly Controlled Modification of Dynamically-Determined Object Attributes)
**OWASP:** A01:2021 — Broken Access Control

**Issue:**
[Description of the mass assignment vulnerability]

**Attack Vector:**
Attacker adds `is_admin=true` to request body, gaining admin privileges.

**Code:**
```php
// Vulnerable code
```

**Fix:**
```php
// With explicit field whitelisting
```
```
