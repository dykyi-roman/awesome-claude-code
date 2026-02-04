---
name: acc-check-authorization
description: Analyzes PHP code for authorization issues. Detects missing access control, IDOR vulnerabilities, privilege escalation, role-based access gaps.
---

# Authorization Security Check

Analyze PHP code for authorization and access control vulnerabilities.

## Detection Patterns

### 1. Missing Access Control Checks

```php
// CRITICAL: No authorization
public function deleteUser(int $id): Response
{
    $user = $this->userRepository->find($id);
    $this->userRepository->delete($user);
    // Anyone can delete any user!
}

// CRITICAL: Only checking authentication, not authorization
public function updateOrder(int $orderId): Response
{
    if (!$this->getUser()) {
        throw new UnauthorizedException();
    }
    // Auth check present, but no ownership check
    $order = $this->orderRepository->find($orderId);
    $order->update($this->request->all());
}
```

### 2. IDOR (Insecure Direct Object Reference)

```php
// CRITICAL: Direct ID from user input
$order = $this->orderRepository->find($_GET['id']);
return new JsonResponse($order);

// CRITICAL: Sequential ID enumeration
/api/users/1
/api/users/2
/api/users/3 // Attacker iterates through all users

// CORRECT: Ownership check
$order = $this->orderRepository->findByIdAndUser($id, $currentUser);
if (!$order) {
    throw new NotFoundException();
}
```

### 3. Privilege Escalation

```php
// CRITICAL: Role from user input
$user->setRole($_POST['role']); // User sets own role

// CRITICAL: Mass assignment vulnerability
$user->fill($request->all()); // Could include 'is_admin'

// VULNERABLE: Hidden field role
<input type="hidden" name="role" value="user">
// Attacker changes to "admin"
```

### 4. Horizontal Privilege Escalation

```php
// CRITICAL: Can access other users' data
public function getProfile(int $userId): Response
{
    return new JsonResponse(
        $this->userRepository->find($userId)
    );
    // User A can view User B's profile
}

// CRITICAL: Can modify other users' resources
public function updateProfile(int $userId, array $data): void
{
    $user = $this->userRepository->find($userId);
    $user->update($data);
    // No check if $userId === currentUser->id
}
```

### 5. Vertical Privilege Escalation

```php
// CRITICAL: Admin function accessible to users
#[Route('/admin/users')]
public function listUsers(): Response
{
    // No role check
    return new JsonResponse($this->userRepository->findAll());
}

// VULNERABLE: Role check can be bypassed
if ($request->get('bypass_check') === 'true') {
    $this->isAdmin = true;
}
```

### 6. Path/Action Based Authorization Gaps

```php
// VULNERABLE: Only checking some endpoints
// /api/users - protected
// /api/users/export - NOT protected

// VULNERABLE: Different behavior for same resource
// GET /orders/1 - ownership checked
// DELETE /orders/1 - no ownership check
```

### 7. JWT/Token Authorization Issues

```php
// CRITICAL: Trusting JWT claims without verification
$payload = json_decode(base64_decode(explode('.', $jwt)[1]));
if ($payload->role === 'admin') { }

// CRITICAL: Algorithm confusion
// Server accepts 'none' algorithm

// VULNERABLE: No token expiry check
$token = $this->jwtService->decode($jwt);
// No check for exp claim
```

### 8. Resource-Based Access Control Gaps

```php
// VULNERABLE: Checking role but not resource ownership
if ($this->isAdmin()) {
    $document = $this->documentRepository->find($id);
    return $document; // Admin sees ALL documents across organizations
}

// CORRECT: Scope to organization
$document = $this->documentRepository->findByIdAndOrganization(
    $id,
    $currentUser->getOrganization()
);
```

## Grep Patterns

```bash
# Repository find without ownership
Grep: "Repository->find\(\\\$_|Repository->find\(\\\$request" --glob "**/*.php"

# Direct object access
Grep: "find\(\\\$id\)\s*;" --glob "**/*.php"

# Role from user input
Grep: "setRole\(\\\$_|setRole\(\\\$request" --glob "**/*.php"

# Mass assignment
Grep: "->fill\(\\\$request|->update\(\\\$request" --glob "**/*.php"
```

## Severity Classification

| Pattern | Severity |
|---------|----------|
| Missing access control | 🔴 Critical |
| IDOR vulnerability | 🔴 Critical |
| Privilege escalation from input | 🔴 Critical |
| Horizontal access violation | 🔴 Critical |
| Role bypass mechanism | 🔴 Critical |
| Missing resource scoping | 🟠 Major |
| Inconsistent auth on endpoints | 🟠 Major |

## Best Practices

### Always Check Ownership

```php
public function getOrder(int $id): Response
{
    $order = $this->orderRepository->findByIdAndUser($id, $this->getUser());
    if (!$order) {
        throw new NotFoundHttpException();
    }
    return new JsonResponse($order);
}
```

### Use Voters/Policies

```php
// Symfony Voter
if (!$this->isGranted('EDIT', $order)) {
    throw new AccessDeniedException();
}

// Laravel Policy
$this->authorize('update', $order);
```

### Protected Mass Assignment

```php
// Laravel
protected $fillable = ['name', 'email']; // Whitelist
protected $guarded = ['is_admin', 'role']; // Blacklist

// Explicit assignment
$user->setName($request->get('name'));
// Never: $user->setRole($request->get('role'));
```

### UUIDs Instead of Sequential IDs

```php
// Harder to enumerate
/api/orders/550e8400-e29b-41d4-a716-446655440000
```

## Output Format

```markdown
### Authorization Issue: [Description]

**Severity:** 🔴/🟠/🟡
**Location:** `file.php:line`
**CWE:** CWE-862 (Missing Authorization)

**Issue:**
[Description of the authorization weakness]

**Attack Vector:**
Attacker can access/modify resources belonging to other users.

**Code:**
```php
// Vulnerable code
```

**Fix:**
```php
// With proper authorization
```
```
