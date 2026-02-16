# Anti-Corruption Layer Templates

## Domain Port (Interface)

**File:** `src/Domain/{BoundedContext}/Port/{ExternalSystem}PortInterface.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext}\Port;

use Domain\{BoundedContext}\Entity\{Entity};
use Domain\{BoundedContext}\ValueObject\{ValueObject};

interface {ExternalSystem}PortInterface
{
    /**
     * @throws {ExternalSystem}Exception
     */
    public function {operation}({DomainParameters}): {DomainReturnType};
}
```

---

## External DTO

**File:** `src/Infrastructure/{BoundedContext}/ACL/{ExternalSystem}/DTO/{ExternalSystem}{Concept}DTO.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\{BoundedContext}\ACL\{ExternalSystem}\DTO;

/**
 * DTO matching external system's data structure.
 * This is NOT a domain object - it's a data carrier for external format.
 */
final readonly class {ExternalSystem}{Concept}DTO
{
    public function __construct(
        public string $externalId,
        public string $externalField1,
        public ?string $externalField2,
        public array $externalNestedData,
    ) {}

    public static function fromArray(array $data): self
    {
        return new self(
            externalId: $data['external_id'] ?? $data['id'],
            externalField1: $data['field_1'],
            externalField2: $data['field_2'] ?? null,
            externalNestedData: $data['nested'] ?? [],
        );
    }

    public function toArray(): array
    {
        return [
            'external_id' => $this->externalId,
            'field_1' => $this->externalField1,
            'field_2' => $this->externalField2,
            'nested' => $this->externalNestedData,
        ];
    }
}
```

---

## Translator

**File:** `src/Infrastructure/{BoundedContext}/ACL/{ExternalSystem}/{ExternalSystem}Translator.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\{BoundedContext}\ACL\{ExternalSystem};

use Domain\{BoundedContext}\Entity\{Entity};
use Domain\{BoundedContext}\ValueObject\{ValueObject};
use Infrastructure\{BoundedContext}\ACL\{ExternalSystem}\DTO\{ExternalSystem}{Concept}DTO;

final readonly class {ExternalSystem}Translator
{
    /**
     * Translate external DTO to domain entity/value object.
     */
    public function toDomain({ExternalSystem}{Concept}DTO $dto): {Entity}
    {
        return new {Entity}(
            id: {EntityId}::fromString($this->mapExternalId($dto->externalId)),
            {mappedProperties}
        );
    }

    /**
     * Translate domain entity to external DTO.
     */
    public function toExternal({Entity} $entity): {ExternalSystem}{Concept}DTO
    {
        return new {ExternalSystem}{Concept}DTO(
            externalId: $this->mapToExternalId($entity->id()),
            {mappedExternalProperties}
        );
    }

    /**
     * Translate domain value object to external format.
     */
    public function {valueObject}ToExternal({ValueObject} $vo): array
    {
        return [
            'external_field' => $vo->value(),
        ];
    }

    /**
     * Translate external format to domain value object.
     */
    public function {valueObject}ToDomain(array $data): {ValueObject}
    {
        return new {ValueObject}($data['external_field']);
    }

    private function mapExternalId(string $externalId): string
    {
        return $externalId;
    }

    private function mapToExternalId({EntityId} $id): string
    {
        return $id->toString();
    }
}
```

---

## Facade

**File:** `src/Infrastructure/{BoundedContext}/ACL/{ExternalSystem}/{ExternalSystem}Facade.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\{BoundedContext}\ACL\{ExternalSystem};

use Infrastructure\{BoundedContext}\ACL\{ExternalSystem}\DTO\{ExternalSystem}{Concept}DTO;
use Infrastructure\{BoundedContext}\ACL\{ExternalSystem}\Exception\{ExternalSystem}ConnectionException;

final readonly class {ExternalSystem}Facade
{
    public function __construct(
        private {ExternalSystem}ClientInterface $client,
        private string $apiKey,
    ) {}

    /**
     * @throws {ExternalSystem}ConnectionException
     */
    public function fetch{Concept}(string $externalId): {ExternalSystem}{Concept}DTO
    {
        try {
            $response = $this->client->get("/api/{concepts}/{$externalId}", [
                'headers' => ['Authorization' => "Bearer {$this->apiKey}"],
            ]);

            return {ExternalSystem}{Concept}DTO::fromArray($response);
        } catch (\Throwable $e) {
            throw new {ExternalSystem}ConnectionException(
                "Failed to fetch {concept}: {$e->getMessage()}",
                previous: $e
            );
        }
    }

    /**
     * @throws {ExternalSystem}ConnectionException
     */
    public function create{Concept}({ExternalSystem}{Concept}DTO $dto): string
    {
        try {
            $response = $this->client->post('/api/{concepts}', [
                'headers' => ['Authorization' => "Bearer {$this->apiKey}"],
                'json' => $dto->toArray(),
            ]);

            return $response['id'];
        } catch (\Throwable $e) {
            throw new {ExternalSystem}ConnectionException(
                "Failed to create {concept}: {$e->getMessage()}",
                previous: $e
            );
        }
    }

    /**
     * @throws {ExternalSystem}ConnectionException
     */
    public function update{Concept}(string $externalId, {ExternalSystem}{Concept}DTO $dto): void
    {
        try {
            $this->client->put("/api/{concepts}/{$externalId}", [
                'headers' => ['Authorization' => "Bearer {$this->apiKey}"],
                'json' => $dto->toArray(),
            ]);
        } catch (\Throwable $e) {
            throw new {ExternalSystem}ConnectionException(
                "Failed to update {concept}: {$e->getMessage()}",
                previous: $e
            );
        }
    }
}
```

---

## Adapter (Implements Domain Port)

**File:** `src/Infrastructure/{BoundedContext}/ACL/{ExternalSystem}/{ExternalSystem}Adapter.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\{BoundedContext}\ACL\{ExternalSystem};

use Domain\{BoundedContext}\Entity\{Entity};
use Domain\{BoundedContext}\Port\{ExternalSystem}PortInterface;
use Domain\{BoundedContext}\ValueObject\{EntityId};
use Infrastructure\{BoundedContext}\ACL\{ExternalSystem}\Exception\{ExternalSystem}Exception;

final readonly class {ExternalSystem}Adapter implements {ExternalSystem}PortInterface
{
    public function __construct(
        private {ExternalSystem}Facade $facade,
        private {ExternalSystem}Translator $translator,
    ) {}

    public function find({EntityId} $id): ?{Entity}
    {
        try {
            $dto = $this->facade->fetch{Concept}($id->toString());
            return $this->translator->toDomain($dto);
        } catch ({ExternalSystem}ConnectionException $e) {
            if ($this->isNotFound($e)) {
                return null;
            }
            throw new {ExternalSystem}Exception($e->getMessage(), previous: $e);
        }
    }

    public function save({Entity} $entity): void
    {
        $dto = $this->translator->toExternal($entity);

        try {
            if ($this->exists($entity->id())) {
                $this->facade->update{Concept}($entity->id()->toString(), $dto);
            } else {
                $externalId = $this->facade->create{Concept}($dto);
            }
        } catch ({ExternalSystem}ConnectionException $e) {
            throw new {ExternalSystem}Exception($e->getMessage(), previous: $e);
        }
    }

    private function exists({EntityId} $id): bool
    {
        return $this->find($id) !== null;
    }

    private function isNotFound({ExternalSystem}ConnectionException $e): bool
    {
        return str_contains($e->getMessage(), '404')
            || str_contains($e->getMessage(), 'not found');
    }
}
```

---

## Exceptions

**File:** `src/Infrastructure/{BoundedContext}/ACL/{ExternalSystem}/Exception/{ExternalSystem}Exception.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\{BoundedContext}\ACL\{ExternalSystem}\Exception;

use Domain\{BoundedContext}\Exception\{BoundedContext}Exception;

final class {ExternalSystem}Exception extends {BoundedContext}Exception
{
}
```

**File:** `src/Infrastructure/{BoundedContext}/ACL/{ExternalSystem}/Exception/{ExternalSystem}ConnectionException.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\{BoundedContext}\ACL\{ExternalSystem}\Exception;

final class {ExternalSystem}ConnectionException extends \RuntimeException
{
}
```
