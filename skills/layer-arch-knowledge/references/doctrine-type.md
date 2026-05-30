# Doctrine Custom Type (Layered Architecture, Doctrine ORM)

Custom Doctrine types are a Doctrine-specific pattern for mapping a Value Object to a column. In the 3-layer Domain-centric Layered Architecture this skill describes, custom types typically live in `Infrastructure/Doctrine/Type/` — they bridge the ORM (Infrastructure) to Value Objects (Domain) without leaking Doctrine awareness into the Domain.

Note: in other architectures (Clean/Onion), Doctrine custom types live in adapter / persistence-infrastructure folders; in N-Tier, also under Infrastructure. The mechanics are identical — only placement varies.

## Characteristics

- One type class per Value Object (e.g. `EmailType` for `Email`).
- Extends `Doctrine\DBAL\Types\Type` or a base of choice.
- Converts between PHP value (Value Object) and database value (string, int, JSON, etc.).
- Registered globally via `doctrine.yaml` types map or in Doctrine config bootstrap.
- Stateless; safe to share across entity mappings.

## When to use

| Scenario | Use a custom Doctrine Type |
|----------|----------------------------|
| Embedding a Value Object in a column (`Email`, `Money`, `UserId`) | Yes |
| Custom enum mapping where PHP enum support isn't enough | Yes |
| Complex JSON-mapped value | Yes — but consider Doctrine Embeddables first |
| Multi-column Value Object (e.g. `Address(street, city, zip)`) | No — use Embeddable, not a custom type |

## Folder layout

```
Infrastructure/Doctrine/Type/
├── EmailType.php
├── MoneyType.php
└── UserIdType.php
```

## Template — string-backed Value Object

```php
<?php

declare(strict_types=1);

namespace Doctrine\Type;

use Doctrine\DBAL\Platforms\AbstractPlatform;
use Doctrine\DBAL\Types\Type;

final class EmailType extends Type
{
    public const NAME = 'email';

    public function getName(): string
    {
        return self::NAME;
    }

    public function getSQLDeclaration(array $column, AbstractPlatform $platform): string
    {
        $length = $column['length'] ?? 255;

        return $platform->getStringTypeDeclarationSQL([
            'length' => $length,
        ]);
    }

    public function convertToPHPValue($value, AbstractPlatform $platform): ?Email
    {
        if ($value === null) {
            return null;
        }

        return new Email((string) $value);
    }

    public function convertToDatabaseValue($value, AbstractPlatform $platform): ?string
    {
        if ($value === null) {
            return null;
        }

        if (!$value instanceof Email) {
            throw new \InvalidArgumentException(sprintf(
                'EmailType expects an Email instance; got %s.',
                get_debug_type($value),
            ));
        }

        return $value->value();
    }

    public function requiresSQLCommentHint(AbstractPlatform $platform): bool
    {
        return true;
    }
}
```

## Template — int-backed Value Object (Money in cents)

```php
<?php

declare(strict_types=1);

namespace Doctrine\Type;

use Doctrine\DBAL\Platforms\AbstractPlatform;
use Doctrine\DBAL\Types\Type;

final class MoneyType extends Type
{
    public const NAME = 'money_cents';

    public function getName(): string
    {
        return self::NAME;
    }

    public function getSQLDeclaration(array $column, AbstractPlatform $platform): string
    {
        return $platform->getBigIntTypeDeclarationSQL($column);
    }

    public function convertToPHPValue($value, AbstractPlatform $platform): ?Money
    {
        if ($value === null) {
            return null;
        }

        // Currency assumed stored separately (column or part of context).
        // For multi-currency, consider a Doctrine Embeddable instead.
        return Money::fromCents((int) $value, Currency::USD);
    }

    public function convertToDatabaseValue($value, AbstractPlatform $platform): ?int
    {
        if ($value === null) {
            return null;
        }

        if (!$value instanceof Money) {
            throw new \InvalidArgumentException(sprintf(
                'MoneyType expects a Money instance; got %s.',
                get_debug_type($value),
            ));
        }

        return $value->cents();
    }
}
```

## Registration

In Symfony:

```yaml
# config/packages/doctrine.yaml
doctrine:
    dbal:
        types:
            email: Doctrine\Type\EmailType
            money_cents: Doctrine\Type\MoneyType
```

Or programmatically (any Doctrine bootstrap):

```php
use Doctrine\DBAL\Types\Type;

Type::addType(EmailType::NAME, EmailType::class);
Type::addType(MoneyType::NAME, MoneyType::class);
```

## Usage on an entity

```php
<?php

declare(strict_types=1);

namespace Model;

use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity]
#[ORM\Table(name: 'users')]
class User
{
    #[ORM\Id]
    #[ORM\Column(type: 'string', length: 36)]
    private string $id;

    #[ORM\Column(type: 'email', length: 255, unique: true)]
    private Email $email;

    // ...
}
```

## Antipatterns

| Antipattern | Why it's bad | Fix |
|-------------|--------------|-----|
| Domain Value Object aware of Doctrine | Couples domain to ORM | Keep Value Object pure; conversion happens in the Type |
| Custom Type for a multi-field Value Object | Forces JSON encoding or string concat | Use a Doctrine Embeddable |
| Currency assumed inside `MoneyType` | Hides domain meaning | Use an Embeddable that stores both `cents` and `currency` |
| Type that returns `null` on bad input | Hides bugs | Throw `InvalidArgumentException` |
| Registering types ad-hoc per fixture/test | Inconsistent — works in some envs, breaks in others | Register centrally via doctrine config |
