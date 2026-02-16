# ADR Antipatterns Reference

Common ADR violations with detection patterns and fixes.

## Critical Antipatterns

### 1. Fat Action

**Description:** Action contains business logic, validation, or response building.

**Detection:**
```bash
# Response building in Action
Grep: "new Response|->withStatus|->withHeader|->withBody" --glob "**/*Action.php"

# Business logic in Action
Grep: "if \(.*->status|switch \(.*->get|foreach \(.*->get" --glob "**/*Action.php"

# Repository calls in Action
Grep: "Repository|->save\(|->persist\(" --glob "**/*Action.php"
```

**Bad Example:**
```php
final readonly class CreateUserAction
{
    public function __invoke(ServerRequestInterface $request): ResponseInterface
    {
        $data = (array) $request->getParsedBody();

        // BAD: Validation in Action
        if (empty($data['email'])) {
            return new Response(400, [], json_encode(['error' => 'Email required']));
        }

        // BAD: Business logic in Action
        if ($this->userRepository->existsByEmail($data['email'])) {
            return new Response(409, [], json_encode(['error' => 'Email exists']));
        }

        $user = new User($data['email'], $data['name']);
        $this->userRepository->save($user);

        // BAD: Response building in Action
        return new Response(201, [
            'Content-Type' => 'application/json',
        ], json_encode(['id' => $user->id()]));
    }
}
```

**Good Example:**
```php
final readonly class CreateUserAction
{
    public function __invoke(ServerRequestInterface $request): ResponseInterface
    {
        $body = (array) $request->getParsedBody();

        $command = new CreateUserCommand(
            email: $body['email'] ?? '',
            name: $body['name'] ?? '',
        );

        $result = $this->handler->handle($command);

        return $this->responder->respond($result);
    }
}
```

---

### 2. Smart Responder

**Description:** Responder contains business logic, domain calls, or side effects.

**Detection:**
```bash
# Domain calls in Responder
Grep: "Repository|Service|UseCase|Handler" --glob "**/*Responder.php"

# Business logic in Responder
Grep: "if \(.*->is|->validate|->check" --glob "**/*Responder.php"

# Side effects in Responder
Grep: "->save\(|->persist\(|->dispatch\(|->send\(" --glob "**/*Responder.php"
```

**Bad Example:**
```php
final readonly class CreateUserResponder
{
    public function respond(User $user): ResponseInterface
    {
        // BAD: Side effect in Responder
        $this->emailService->sendWelcome($user->email());

        // BAD: Business logic in Responder
        if ($user->isAdmin()) {
            $this->notificationService->notifyAdmins();
        }

        // BAD: Repository call in Responder
        $stats = $this->userRepository->getStats();

        return $this->json([
            'id' => $user->id(),
            'total_users' => $stats->total(),
        ], 201);
    }
}
```

**Good Example:**
```php
final readonly class CreateUserResponder
{
    public function respond(CreateUserResult $result): ResponseInterface
    {
        if ($result->isFailure()) {
            return $this->badRequest($result->errorMessage());
        }

        return $this->created([
            'id' => $result->userId(),
            'email' => $result->email(),
        ]);
    }
}
```

---

### 3. Anemic Responder

**Description:** Responder doesn't properly build response, just passes data through.

**Detection:**
```bash
# Responder that just encodes data
Grep: "return.*json_encode\(.*\$result" --glob "**/*Responder.php"

# No status code handling
Grep: "respond.*\{[^}]*json_encode[^}]*\}" --glob "**/*Responder.php"
```

**Bad Example:**
```php
final readonly class CreateUserResponder
{
    public function respond(mixed $result): ResponseInterface
    {
        // BAD: No error handling, no status codes
        return new Response(
            200,
            ['Content-Type' => 'application/json'],
            json_encode($result)
        );
    }
}
```

**Good Example:**
```php
final readonly class CreateUserResponder
{
    public function respond(CreateUserResult $result): ResponseInterface
    {
        if ($result->isFailure()) {
            return match ($result->failureReason()) {
                'email_exists' => $this->conflict('Email already exists'),
                'invalid_email' => $this->badRequest('Invalid email format'),
                default => $this->badRequest($result->errorMessage()),
            };
        }

        return $this->created([
            'id' => $result->userId(),
            'email' => $result->email(),
        ]);
    }
}
```

---

### 4. Multi-Action Class

**Description:** Class has multiple action methods instead of single `__invoke()`.

**Detection:**
```bash
# Multiple public methods in Action
Grep: "public function [^_]" --glob "**/*Action.php" -c

# Classes with action-like method names
Grep: "public function (create|update|delete|show|index|list)" --glob "**/*Action.php"
```

**Bad Example:**
```php
final readonly class UserAction
{
    // BAD: Multiple actions in one class
    public function create(ServerRequestInterface $request): ResponseInterface
    {
        // ...
    }

    public function show(ServerRequestInterface $request): ResponseInterface
    {
        // ...
    }

    public function update(ServerRequestInterface $request): ResponseInterface
    {
        // ...
    }
}
```

**Good Example:**
```php
// CreateUserAction.php
final readonly class CreateUserAction
{
    public function __invoke(ServerRequestInterface $request): ResponseInterface
    {
        // ...
    }
}

// GetUserByIdAction.php
final readonly class GetUserByIdAction
{
    public function __invoke(ServerRequestInterface $request): ResponseInterface
    {
        // ...
    }
}
```

---

## Warning Antipatterns

### 5. Direct Domain Object in Response

**Description:** Responder serializes domain objects directly without DTO.

**Detection:**
```bash
# Direct entity serialization
Grep: "json_encode\(.*\$entity|\$user|\$order" --glob "**/*Responder.php"
```

**Issue:** Exposes internal domain structure to API consumers.

**Solution:** Use Response DTOs or explicit array mapping.

---

### 6. Missing Error Mapping

**Description:** Responder doesn't map domain errors to proper HTTP codes.

**Detection:**
```bash
# Generic error responses
Grep: "return.*500|return.*400" --glob "**/*Responder.php"
```

**Bad Example:**
```php
public function respond(CreateUserResult $result): ResponseInterface
{
    if ($result->isFailure()) {
        // BAD: All errors return 400
        return $this->json(['error' => $result->errorMessage()], 400);
    }
    // ...
}
```

**Good Example:**
```php
public function respond(CreateUserResult $result): ResponseInterface
{
    if ($result->isFailure()) {
        return match ($result->failureReason()) {
            'not_found' => $this->notFound($result->errorMessage()),
            'already_exists' => $this->conflict($result->errorMessage()),
            'validation_error' => $this->unprocessableEntity($result->errors()),
            default => $this->badRequest($result->errorMessage()),
        };
    }
    // ...
}
```

---

### 7. Shared Responder

**Description:** One Responder used for multiple Actions.

**Detection:**
```bash
# Responder used in multiple Actions
Grep: "new GenericResponder|use.*GenericResponder" --glob "**/*Action.php"
```

**Issue:** Reduces cohesion, harder to customize responses per action.

**Solution:** Create specific Responder for each Action.

---

### 8. HTTP in Domain

**Description:** Domain/Application layer has HTTP dependencies.

**Detection:**
```bash
# HTTP in Application layer
Grep: "use Psr\\\\Http|use Symfony\\\\.*Request|use Symfony\\\\.*Response" --glob "**/Application/**/*.php"

# HTTP in Domain layer
Grep: "use Psr\\\\Http|Response|Request" --glob "**/Domain/**/*.php"
```

**Issue:** Domain becomes HTTP-dependent, can't be reused in CLI.

**Solution:** Domain returns Result objects, not Responses.

---

## Detection Summary

| Antipattern | Severity | Grep Pattern |
|-------------|----------|--------------|
| Fat Action | Critical | `new Response\|->withStatus` in Action |
| Smart Responder | Critical | `Repository\|Service` in Responder |
| Anemic Responder | Warning | Simple `json_encode` only |
| Multi-Action Class | Warning | Multiple public methods |
| Direct Domain Serialization | Warning | Entity in json_encode |
| Missing Error Mapping | Warning | Generic 400/500 responses |
| Shared Responder | Info | GenericResponder usage |
| HTTP in Domain | Critical | PSR\\Http in Application/Domain |

## Quick Fix Commands

```bash
# Find all ADR violations
Grep: "new Response|->withStatus|->withHeader" --glob "**/*Action.php"
Grep: "Repository|Service|UseCase" --glob "**/*Responder.php"

# Find potential multi-action classes
for f in $(find . -name "*Action.php"); do
  count=$(grep -c "public function" "$f")
  if [ "$count" -gt 1 ]; then
    echo "$f has $count public methods"
  fi
done
```
