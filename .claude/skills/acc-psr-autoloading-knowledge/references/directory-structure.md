# PSR-4 Directory Structure

## Standard Layouts

### Simple Project

```
project/
├── composer.json
├── src/
│   ├── Controller/
│   │   └── UserController.php    # App\Controller\UserController
│   ├── Entity/
│   │   └── User.php              # App\Entity\User
│   ├── Repository/
│   │   └── UserRepository.php    # App\Repository\UserRepository
│   └── Service/
│       └── UserService.php       # App\Service\UserService
└── tests/
    └── Unit/
        └── Service/
            └── UserServiceTest.php  # App\Tests\Unit\Service\UserServiceTest
```

**composer.json:**
```json
{
    "autoload": {
        "psr-4": {
            "App\\": "src/"
        }
    },
    "autoload-dev": {
        "psr-4": {
            "App\\Tests\\": "tests/"
        }
    }
}
```

### DDD Project

```
project/
├── composer.json
├── src/
│   ├── Domain/
│   │   ├── User/
│   │   │   ├── Entity/
│   │   │   │   └── User.php                    # App\Domain\User\Entity\User
│   │   │   ├── ValueObject/
│   │   │   │   ├── UserId.php                  # App\Domain\User\ValueObject\UserId
│   │   │   │   └── Email.php                   # App\Domain\User\ValueObject\Email
│   │   │   ├── Repository/
│   │   │   │   └── UserRepositoryInterface.php # App\Domain\User\Repository\UserRepositoryInterface
│   │   │   ├── Service/
│   │   │   │   └── UserDomainService.php       # App\Domain\User\Service\UserDomainService
│   │   │   └── Event/
│   │   │       └── UserCreated.php             # App\Domain\User\Event\UserCreated
│   │   └── Order/
│   │       ├── Entity/
│   │       │   └── Order.php                   # App\Domain\Order\Entity\Order
│   │       └── ValueObject/
│   │           └── OrderId.php                 # App\Domain\Order\ValueObject\OrderId
│   ├── Application/
│   │   └── User/
│   │       ├── Command/
│   │       │   └── CreateUserCommand.php       # App\Application\User\Command\CreateUserCommand
│   │       ├── Handler/
│   │       │   └── CreateUserHandler.php       # App\Application\User\Handler\CreateUserHandler
│   │       ├── Query/
│   │       │   └── GetUserQuery.php            # App\Application\User\Query\GetUserQuery
│   │       └── DTO/
│   │           └── UserDTO.php                 # App\Application\User\DTO\UserDTO
│   ├── Infrastructure/
│   │   ├── Persistence/
│   │   │   └── Doctrine/
│   │   │       ├── Repository/
│   │   │       │   └── DoctrineUserRepository.php
│   │   │       └── Mapping/
│   │   │           └── User.orm.xml
│   │   ├── Messaging/
│   │   │   └── RabbitMQ/
│   │   │       └── UserEventPublisher.php
│   │   └── Cache/
│   │       └── Redis/
│   │           └── UserCacheRepository.php
│   └── Presentation/
│       ├── Api/
│       │   ├── Controller/
│       │   │   └── UserController.php          # App\Presentation\Api\Controller\UserController
│       │   ├── Request/
│       │   │   └── CreateUserRequest.php
│       │   └── Response/
│       │       └── UserResponse.php
│       └── Console/
│           └── Command/
│               └── CreateUserCommand.php       # App\Presentation\Console\Command\CreateUserCommand
└── tests/
    ├── Unit/
    │   ├── Domain/
    │   │   └── User/
    │   │       ├── Entity/
    │   │       │   └── UserTest.php
    │   │       └── ValueObject/
    │   │           └── EmailTest.php
    │   └── Application/
    │       └── User/
    │           └── Handler/
    │               └── CreateUserHandlerTest.php
    ├── Integration/
    │   └── Infrastructure/
    │       └── Persistence/
    │           └── DoctrineUserRepositoryTest.php
    └── Functional/
        └── Api/
            └── UserControllerTest.php
```

**composer.json:**
```json
{
    "autoload": {
        "psr-4": {
            "App\\": "src/"
        }
    },
    "autoload-dev": {
        "psr-4": {
            "App\\Tests\\": "tests/"
        }
    }
}
```

### Hexagonal Architecture

```
project/
├── composer.json
├── src/
│   ├── Core/                         # Domain + Application
│   │   ├── Domain/
│   │   │   └── User/
│   │   │       ├── User.php          # App\Core\Domain\User\User
│   │   │       └── UserRepository.php
│   │   ├── Application/
│   │   │   └── User/
│   │   │       └── CreateUser.php
│   │   └── Port/
│   │       ├── In/                   # Driving ports
│   │       │   └── CreateUserPort.php
│   │       └── Out/                  # Driven ports
│   │           └── UserPersistencePort.php
│   └── Adapter/
│       ├── In/                       # Driving adapters
│       │   ├── Web/
│       │   │   └── UserController.php
│       │   └── Console/
│       │       └── CreateUserCommand.php
│       └── Out/                      # Driven adapters
│           ├── Persistence/
│           │   └── PostgresUserRepository.php
│           └── Messaging/
│               └── RabbitMQPublisher.php
└── tests/
```

### Modular Monolith

```
project/
├── composer.json
├── src/
│   ├── Shared/                       # Shared Kernel
│   │   ├── Domain/
│   │   │   ├── ValueObject/
│   │   │   │   └── AggregateId.php   # App\Shared\Domain\ValueObject\AggregateId
│   │   │   └── Event/
│   │   │       └── DomainEvent.php
│   │   └── Infrastructure/
│   │       └── Bus/
│   │           └── MessageBus.php
│   ├── UserManagement/               # Bounded Context
│   │   ├── Domain/
│   │   │   ├── Entity/
│   │   │   │   └── User.php          # App\UserManagement\Domain\Entity\User
│   │   │   └── Repository/
│   │   │       └── UserRepositoryInterface.php
│   │   ├── Application/
│   │   │   └── Service/
│   │   │       └── UserService.php
│   │   └── Infrastructure/
│   │       └── Repository/
│   │           └── DoctrineUserRepository.php
│   ├── Billing/                      # Bounded Context
│   │   ├── Domain/
│   │   │   └── Entity/
│   │   │       └── Invoice.php       # App\Billing\Domain\Entity\Invoice
│   │   └── Application/
│   │       └── Service/
│   │           └── BillingService.php
│   └── Shipping/                     # Bounded Context
│       └── Domain/
│           └── Entity/
│               └── Shipment.php      # App\Shipping\Domain\Entity\Shipment
└── tests/
```

**composer.json:**
```json
{
    "autoload": {
        "psr-4": {
            "App\\Shared\\": "src/Shared/",
            "App\\UserManagement\\": "src/UserManagement/",
            "App\\Billing\\": "src/Billing/",
            "App\\Shipping\\": "src/Shipping/"
        }
    }
}
```

## File Naming Conventions

### Class Types

| Type | Suffix | Example |
|------|--------|---------|
| Entity | - | `User.php`, `Order.php` |
| Value Object | - | `Email.php`, `Money.php` |
| Repository Interface | `Interface` | `UserRepositoryInterface.php` |
| Repository Implementation | - or prefix | `DoctrineUserRepository.php` |
| Service | `Service` | `UserService.php` |
| Handler | `Handler` | `CreateUserHandler.php` |
| Command | `Command` | `CreateUserCommand.php` |
| Query | `Query` | `GetUserQuery.php` |
| Event | - (past tense) | `UserCreated.php` |
| Exception | `Exception` | `UserNotFoundException.php` |
| DTO | `DTO` or `Request`/`Response` | `UserDTO.php`, `CreateUserRequest.php` |
| Factory | `Factory` | `UserFactory.php` |
| Specification | `Specification` | `ActiveUserSpecification.php` |

### Directory Conventions

```
src/
├── Domain/
│   └── {Context}/
│       ├── Entity/           # Aggregates and Entities
│       ├── ValueObject/      # Value Objects
│       ├── Repository/       # Repository Interfaces
│       ├── Service/          # Domain Services
│       ├── Event/            # Domain Events
│       ├── Exception/        # Domain Exceptions
│       ├── Factory/          # Factories
│       └── Specification/    # Specifications
├── Application/
│   └── {Context}/
│       ├── Command/          # Commands
│       ├── Query/            # Queries
│       ├── Handler/          # Handlers
│       ├── Service/          # Application Services
│       ├── DTO/              # Data Transfer Objects
│       └── Event/            # Application Events
├── Infrastructure/
│   ├── Persistence/          # Database implementations
│   ├── Messaging/            # Message queue implementations
│   ├── Cache/                # Cache implementations
│   ├── Http/                 # HTTP client implementations
│   └── External/             # External service integrations
└── Presentation/
    ├── Api/                  # REST API
    │   ├── Controller/
    │   ├── Request/
    │   └── Response/
    ├── Web/                  # Web UI
    │   ├── Controller/
    │   └── View/
    └── Console/              # CLI
        └── Command/
```

## Validation Script

```bash
#!/bin/bash
# validate-psr4.sh - Validate PSR-4 structure

SRC_DIR="${1:-src}"
NAMESPACE_PREFIX="${2:-App}"
ERRORS=0

echo "Validating PSR-4 structure in $SRC_DIR with prefix $NAMESPACE_PREFIX"

# Find all PHP files
while IFS= read -r -d '' file; do
    # Extract namespace from file
    namespace=$(grep -m1 "^namespace" "$file" 2>/dev/null | sed 's/namespace //;s/;//')

    if [ -z "$namespace" ]; then
        echo "WARNING: No namespace in $file"
        continue
    fi

    # Calculate expected namespace from path
    rel_path="${file#$SRC_DIR/}"
    dir_path=$(dirname "$rel_path")

    if [ "$dir_path" = "." ]; then
        expected_ns="$NAMESPACE_PREFIX"
    else
        expected_ns="$NAMESPACE_PREFIX\\$(echo "$dir_path" | tr '/' '\\')"
    fi

    # Compare
    if [ "$namespace" != "$expected_ns" ]; then
        echo "MISMATCH: $file"
        echo "  Found:    $namespace"
        echo "  Expected: $expected_ns"
        ERRORS=$((ERRORS + 1))
    fi

    # Check class name matches filename
    filename=$(basename "$file" .php)
    if ! grep -q "^\(class\|interface\|trait\|enum\|abstract class\|final class\|final readonly class\|readonly class\) $filename" "$file"; then
        echo "WARNING: Class name may not match filename: $file"
    fi

done < <(find "$SRC_DIR" -name "*.php" -print0)

echo ""
if [ "$ERRORS" -gt 0 ]; then
    echo "Found $ERRORS namespace mismatches"
    exit 1
else
    echo "All files pass PSR-4 validation"
    exit 0
fi
```
