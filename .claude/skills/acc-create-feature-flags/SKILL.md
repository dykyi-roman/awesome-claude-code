---
name: acc-create-feature-flags
description: Generates feature flag implementations for PHP projects. Creates flag services, configuration, percentage rollouts, user targeting, and integration with deployment pipelines.
---

# Feature Flag Generator

Generates feature flag implementation for progressive deployments.

## Feature Flag Service Interface

```php
<?php
// src/Infrastructure/FeatureFlag/FeatureFlagServiceInterface.php

declare(strict_types=1);

namespace App\Infrastructure\FeatureFlag;

interface FeatureFlagServiceInterface
{
    /**
     * Check if a feature is enabled globally.
     */
    public function isEnabled(string $feature): bool;

    /**
     * Check if a feature is enabled for a specific user.
     */
    public function isEnabledForUser(string $feature, string $userId): bool;

    /**
     * Check if a feature is enabled based on percentage rollout.
     */
    public function isEnabledForPercentage(string $feature, string $identifier): bool;

    /**
     * Get the variant for A/B testing.
     */
    public function getVariant(string $feature, string $userId): string;

    /**
     * Get all enabled features for a user.
     */
    public function getEnabledFeatures(string $userId): array;
}
```

## Feature Configuration DTO

```php
<?php
// src/Infrastructure/FeatureFlag/FeatureConfig.php

declare(strict_types=1);

namespace App\Infrastructure\FeatureFlag;

final readonly class FeatureConfig
{
    /**
     * @param string[] $allowedUsers
     * @param string[] $blockedUsers
     * @param string[] $variants
     * @param array<string, mixed> $metadata
     */
    public function __construct(
        public string $name,
        public bool $enabled = false,
        public ?int $percentage = null,
        public array $allowedUsers = [],
        public array $blockedUsers = [],
        public array $variants = [],
        public array $metadata = [],
    ) {}

    /**
     * @param array<string, mixed> $data
     */
    public static function fromArray(array $data): self
    {
        return new self(
            name: $data['name'],
            enabled: $data['enabled'] ?? false,
            percentage: $data['percentage'] ?? null,
            allowedUsers: $data['allowed_users'] ?? [],
            blockedUsers: $data['blocked_users'] ?? [],
            variants: $data['variants'] ?? [],
            metadata: $data['metadata'] ?? [],
        );
    }
}
```

See `references/templates.md` for: InMemory implementation, YAML configuration, Config Loader, Attribute, Middleware, Twig Extension, Template usage, CI/CD integration, Redis implementation.

## Generation Instructions

1. **Choose storage backend:**
   - In-memory (config file)
   - Redis (dynamic updates)
   - Database (audit trail)
   - External service (LaunchDarkly, etc.)

2. **Define flag types:**
   - Boolean (on/off)
   - Percentage rollout
   - User targeting
   - A/B variants

3. **Integrate with framework:**
   - Middleware for request context
   - Twig extension for templates
   - Service for business logic

4. **Set up CI/CD integration:**
   - Environment-based defaults
   - Dynamic update endpoints
   - Rollback capabilities

## Usage

Provide:
- Storage backend preference
- Framework (Symfony, Laravel, etc.)
- Flag types needed
- CI/CD platform

The generator will:
1. Create interface and implementation
2. Add configuration loader
3. Integrate with framework
4. Set up CI/CD hooks
