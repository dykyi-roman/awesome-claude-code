---
name: check-access-control-model
description: Analyzes PHP code for access control issues. Detects inline role checks, hardcoded permissions, mixed ACL/RBAC models, missing Voter/Policy pattern, and authorization logic in controllers.
---

# Access Control Model Check

Analyze PHP code for access control anti-patterns that lead to inconsistent authorization, privilege escalation, and unmaintainable permission logic.

## Detection Patterns

### 1. Inline Role Checks

```php
<?php

declare(strict_types=1);

// BAD: Hardcoded role check scattered across code
final class ArticleController
{
    public function delete(Request $request, string $id): Response
    {
        if ($request->user()->role === 'admin') {
            $this->articleService->delete($id);
            return new Response(null, 204);
        }

        return new Response('Forbidden', 403);
    }
}

// BAD: String-based role comparison
if ($user->getRole() === 'editor' || $user->getRole() === 'admin') {
    // Allowed
}

// GOOD: Voter/Policy pattern
final class ArticleVoter extends Voter
{
    protected function supports(string $attribute, mixed $subject): bool
    {
        return $subject instanceof Article
            && in_array($attribute, ['VIEW', 'EDIT', 'DELETE'], true);
    }

    protected function voteOnAttribute(string $attribute, mixed $subject, TokenInterface $token): bool
    {
        $user = $token->getUser();

        return match ($attribute) {
            'DELETE' => $this->canDelete($user, $subject),
            'EDIT' => $this->canEdit($user, $subject),
            'VIEW' => true,
            default => false,
        };
    }

    private function canDelete(UserInterface $user, Article $article): bool
    {
        return $user->hasRole('ROLE_ADMIN')
            || $article->authorId()->equals($user->id());
    }

    private function canEdit(UserInterface $user, Article $article): bool
    {
        return $user->hasRole('ROLE_EDITOR')
            || $article->authorId()->equals($user->id());
    }
}

// Usage in controller
final class ArticleController
{
    public function delete(Request $request, string $id): Response
    {
        $article = $this->articleRepository->findOrFail(new ArticleId($id));
        $this->denyAccessUnlessGranted('DELETE', $article);

        $this->articleService->delete($article);

        return new Response(null, 204);
    }
}
```

### 2. Hardcoded Permission Strings

```php
<?php

declare(strict_types=1);

// BAD: Magic permission strings everywhere
if ($user->hasPermission('manage_users')) { /* ... */ }
if ($user->hasPermission('edit_posts')) { /* ... */ }
if ($user->hasPermission('manage_users')) { /* ... */ } // Typo risk!

// GOOD: Permission enum
enum Permission: string
{
    case ManageUsers = 'manage_users';
    case EditPosts = 'edit_posts';
    case ViewReports = 'view_reports';
    case DeleteOrders = 'delete_orders';
}

// Usage
if ($user->hasPermission(Permission::ManageUsers)) { /* ... */ }
```

### 3. Mixed Authorization Models

```php
<?php

declare(strict_types=1);

// BAD: Some endpoints use RBAC, others use ACL, others use nothing
final class UserController
{
    public function index(): Response
    {
        // RBAC-style
        if (!$this->security->isGranted('ROLE_ADMIN')) {
            throw new AccessDeniedHttpException();
        }
        return new Response($this->userService->list());
    }
}

final class OrderController
{
    public function show(string $id): Response
    {
        // ACL-style
        $order = $this->orderRepo->find($id);
        if ($order->userId() !== $this->getUser()->id()) {
            throw new AccessDeniedHttpException();
        }
        return new Response($order);
    }
}

final class ReportController
{
    public function index(): Response
    {
        // No authorization at all!
        return new Response($this->reportService->generate());
    }
}

// GOOD: Consistent Voter-based authorization across all controllers
// Each resource type has its own Voter
// All controllers use denyAccessUnlessGranted()
```

### 4. Authorization Logic in Controllers

```php
<?php

declare(strict_types=1);

// BAD: Complex authorization logic in controller action
final class ProjectController
{
    public function update(Request $request, string $id): Response
    {
        $project = $this->projectRepo->find($id);
        $user = $request->user();

        // 15 lines of authorization logic in controller
        if ($user->role === 'admin') {
            // admin can do anything
        } elseif ($user->role === 'manager' && $project->teamId() === $user->teamId()) {
            // manager can edit own team projects
        } elseif ($project->ownerId() === $user->id()) {
            // owner can edit own project
        } else {
            return new Response('Forbidden', 403);
        }

        $this->projectService->update($project, $request->validated());

        return new Response($project);
    }
}

// GOOD: Authorization in middleware or Voter
#[IsGranted('EDIT', subject: 'project')]
final class ProjectController
{
    public function update(Request $request, #[MapEntity] Project $project): Response
    {
        $this->projectService->update($project, $request->validated());

        return new Response($project);
    }
}
```

### 5. Missing Deny-by-Default

```php
<?php

declare(strict_types=1);

// BAD: Some routes have no authorization at all
// Routes file with no access control:
// Route::get('/admin/users', [AdminController::class, 'users']);
// Route::post('/admin/settings', [AdminController::class, 'updateSettings']);

// GOOD: Global middleware enforces deny-by-default
// security.yaml or middleware
// access_control:
//     - { path: ^/api/public, roles: PUBLIC_ACCESS }
//     - { path: ^/api, roles: IS_AUTHENTICATED_FULLY }
//     - { path: ^/admin, roles: ROLE_ADMIN }
//     - { path: ^/, roles: IS_AUTHENTICATED_FULLY }  # Deny-by-default
```

## Grep Patterns

```bash
# Inline role checks (string comparison)
Grep: "->role\s*===\s*['\"]|->getRole\(\)\s*===\s*['\"]|role\s*==\s*['\"]" --glob "**/*.php"

# Hardcoded permission strings (not enum)
Grep: "hasPermission\(['\"]|can\(['\"]|isAllowed\(['\"]" --glob "**/*.php"

# Authorization checks in controllers
Grep: "->role|->getRole|isAdmin|isManager|hasRole" --glob "**/*Controller*.php"
Grep: "->role|->getRole|isAdmin|isManager|hasRole" --glob "**/*Action*.php"

# Voter/Policy pattern presence
Grep: "extends Voter|extends Policy|implements VoterInterface" --glob "**/*.php"

# Security attributes/annotations
Grep: "#\[IsGranted|@IsGranted|@Security|denyAccessUnlessGranted" --glob "**/*.php"

# Missing authorization (controllers without security)
Grep: "class.*Controller" --glob "**/*Controller*.php"
Grep: "class.*Action" --glob "**/*Action*.php"

# Permission enum existence
Grep: "enum.*Permission|enum.*Role" --glob "**/*.php"
```

## Severity Classification

| Pattern | Severity |
|---------|----------|
| Missing deny-by-default | 🔴 Critical |
| No authorization on admin endpoints | 🔴 Critical |
| Inline role checks with string comparison | 🟠 Major |
| Authorization logic in controllers | 🟠 Major |
| Hardcoded permission strings (no enum) | 🟠 Major |
| Mixed RBAC/ACL models | 🟡 Minor |
| Missing Voter/Policy for resource access | 🟡 Minor |

## Output Format

```markdown
### Access Control Issue: [Brief Description]

**Severity:** 🔴/🟠/🟡
**Location:** `file.php:line`
**Type:** [Inline Check|Hardcoded Permission|Mixed Model|Controller Auth|No Auth]

**Issue:**
[Description of the access control anti-pattern]

**Risk:**
- Privilege escalation via inconsistent checks
- Forgotten authorization on new endpoints
- Permission logic impossible to audit

**Code:**
```php
// Problematic pattern
```

**Fix:**
```php
// With proper access control
```
```

## When This Is Acceptable

- **Public API endpoints** -- Endpoints explicitly designed for unauthenticated access (e.g., login, registration, public data)
- **Internal microservice communication** -- Service-to-service calls behind network security where mutual TLS is used
- **CLI commands** -- Console commands that run with system-level privileges by design
- **Health check endpoints** -- /health, /ready, /live endpoints intended for load balancers

### False Positive Indicators
- Route is explicitly marked as public in security configuration
- Controller is behind a firewall rule that already enforces authentication
- Role check is inside a Voter or Policy class (correct location)
