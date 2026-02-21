# Feature Flag Patterns

Detailed patterns for feature flags in PHP 8.4 projects with DDD architecture, multiple storage backends, and deployment integration.

## Feature Flag Types

```
┌─────────────────────────────────────────────────────────────────────┐
│                     FEATURE FLAG TYPES                              │
│                                                                     │
│  SIMPLE TOGGLE     PERCENTAGE         USER SEGMENT     ENVIRONMENT │
│  ┌───────────┐     ┌───────────┐     ┌───────────┐    ┌──────────┐│
│  │ ON / OFF  │     │  0% ━━ 100%│     │ Premium   │    │ dev: ON  ││
│  │           │     │  ━━━━━━━━━ │     │ Beta      │    │ stg: ON  ││
│  │ [x] = ON  │     │  25% ████░░│     │ Internal  │    │ prd: OFF ││
│  └───────────┘     └───────────┘     └───────────┘    └──────────┘│
│                                                                     │
│  Runtime flags:     Can change at any time without deploy           │
│  Build-time flags:  Require deploy to change                        │
└─────────────────────────────────────────────────────────────────────┘
```

## PHP 8.4 Feature Flag Implementation

### Domain Layer — Feature Flag Value Objects

```php
<?php

declare(strict_types=1);

namespace Domain\FeatureFlag;

enum FlagType: string
{
    case Boolean = 'boolean';
    case Percentage = 'percentage';
    case UserSegment = 'user_segment';
    case Environment = 'environment';
}
```

```php
<?php

declare(strict_types=1);

namespace Domain\FeatureFlag;

final readonly class FeatureFlag
{
    /**
     * @param list<string> $allowedSegments
     * @param list<string> $allowedEnvironments
     */
    public function __construct(
        public string $name,
        public FlagType $type,
        public bool $enabled,
        public int $percentage = 100,
        public array $allowedSegments = [],
        public array $allowedEnvironments = [],
        public ?\DateTimeImmutable $expiresAt = null,
        public ?string $description = null,
        public ?string $ticket = null,
    ) {}

    public function isExpired(): bool
    {
        if ($this->expiresAt === null) {
            return false;
        }

        return $this->expiresAt < new \DateTimeImmutable();
    }

    public function isStale(\DateTimeImmutable $threshold): bool
    {
        if ($this->expiresAt === null) {
            return false;
        }

        return $this->expiresAt < $threshold;
    }
}
```

### Domain Layer — Feature Flag Resolver Interface

```php
<?php

declare(strict_types=1);

namespace Domain\FeatureFlag;

interface FeatureFlagResolverInterface
{
    public function isEnabled(string $featureName): bool;

    public function isEnabledForIdentifier(string $featureName, string $identifier): bool;

    public function isEnabledForSegment(string $featureName, string $segment): bool;
}
```

### Application Layer — Feature Flag Service

```php
<?php

declare(strict_types=1);

namespace Application\Service;

use Domain\FeatureFlag\FeatureFlag;
use Domain\FeatureFlag\FeatureFlagResolverInterface;
use Domain\FeatureFlag\FlagType;

final readonly class FeatureFlagService implements FeatureFlagResolverInterface
{
    /**
     * @param array<string, FeatureFlag> $flags
     */
    public function __construct(
        private array $flags,
        private string $currentEnvironment,
    ) {}

    public function isEnabled(string $featureName): bool
    {
        $flag = $this->flags[$featureName] ?? null;

        if ($flag === null || !$flag->enabled || $flag->isExpired()) {
            return false;
        }

        return match ($flag->type) {
            FlagType::Boolean => true,
            FlagType::Environment => in_array($this->currentEnvironment, $flag->allowedEnvironments, true),
            FlagType::Percentage => $this->checkPercentage($featureName, $featureName, $flag->percentage),
            FlagType::UserSegment => false,
        };
    }

    public function isEnabledForIdentifier(string $featureName, string $identifier): bool
    {
        $flag = $this->flags[$featureName] ?? null;

        if ($flag === null || !$flag->enabled || $flag->isExpired()) {
            return false;
        }

        if ($flag->type === FlagType::Percentage) {
            return $this->checkPercentage($featureName, $identifier, $flag->percentage);
        }

        return $this->isEnabled($featureName);
    }

    public function isEnabledForSegment(string $featureName, string $segment): bool
    {
        $flag = $this->flags[$featureName] ?? null;

        if ($flag === null || !$flag->enabled || $flag->isExpired()) {
            return false;
        }

        if ($flag->type === FlagType::UserSegment) {
            return in_array($segment, $flag->allowedSegments, true);
        }

        return $this->isEnabled($featureName);
    }

    /**
     * Deterministic percentage check based on feature name + identifier.
     * Same identifier always gets the same result for the same feature.
     */
    private function checkPercentage(string $featureName, string $identifier, int $percentage): bool
    {
        $hash = crc32($featureName . ':' . $identifier);
        $bucket = abs($hash) % 100;

        return $bucket < $percentage;
    }
}
```

## Feature Flag Storage Backends

### Config File Storage (YAML)

```yaml
# config/features.yaml
features:
  new_checkout:
    type: percentage
    enabled: true
    percentage: 25
    description: "Redesigned checkout flow"
    ticket: "SHOP-1234"
    expires_at: "2026-04-01"

  dark_mode:
    type: user_segment
    enabled: true
    allowed_segments:
      - premium
      - enterprise
    description: "Dark mode UI"
    ticket: "UI-567"

  new_search_engine:
    type: environment
    enabled: true
    allowed_environments:
      - development
      - staging
    description: "Elasticsearch-based search"
    ticket: "SEARCH-890"

  maintenance_banner:
    type: boolean
    enabled: false
    description: "Show maintenance warning banner"

  api_v3:
    type: percentage
    enabled: true
    percentage: 10
    description: "API v3 endpoints"
    ticket: "API-321"
    expires_at: "2026-06-01"
```

```php
<?php

declare(strict_types=1);

namespace Infrastructure\FeatureFlag;

use Domain\FeatureFlag\FeatureFlag;
use Domain\FeatureFlag\FlagType;
use Symfony\Component\Yaml\Yaml;

final readonly class YamlFeatureFlagLoader
{
    public function __construct(
        private string $configPath,
    ) {}

    /**
     * @return array<string, FeatureFlag>
     */
    public function load(): array
    {
        $data = Yaml::parseFile($this->configPath);
        $flags = [];

        foreach ($data['features'] ?? [] as $name => $config) {
            $flags[$name] = new FeatureFlag(
                name: $name,
                type: FlagType::from($config['type'] ?? 'boolean'),
                enabled: $config['enabled'] ?? false,
                percentage: $config['percentage'] ?? 100,
                allowedSegments: $config['allowed_segments'] ?? [],
                allowedEnvironments: $config['allowed_environments'] ?? [],
                expiresAt: isset($config['expires_at'])
                    ? new \DateTimeImmutable($config['expires_at'])
                    : null,
                description: $config['description'] ?? null,
                ticket: $config['ticket'] ?? null,
            );
        }

        return $flags;
    }
}
```

### Database Storage (Doctrine DBAL)

```php
<?php

declare(strict_types=1);

namespace Infrastructure\FeatureFlag;

use Domain\FeatureFlag\FeatureFlag;
use Domain\FeatureFlag\FlagType;
use Doctrine\DBAL\Connection;

final readonly class DatabaseFeatureFlagLoader
{
    public function __construct(
        private Connection $connection,
    ) {}

    /**
     * @return array<string, FeatureFlag>
     */
    public function load(): array
    {
        $rows = $this->connection->fetchAllAssociative(
            'SELECT * FROM feature_flags WHERE deleted_at IS NULL',
        );

        $flags = [];
        foreach ($rows as $row) {
            $flags[$row['name']] = new FeatureFlag(
                name: $row['name'],
                type: FlagType::from($row['type']),
                enabled: (bool) $row['enabled'],
                percentage: (int) $row['percentage'],
                allowedSegments: json_decode($row['allowed_segments'] ?? '[]', true),
                allowedEnvironments: json_decode($row['allowed_environments'] ?? '[]', true),
                expiresAt: $row['expires_at'] !== null
                    ? new \DateTimeImmutable($row['expires_at'])
                    : null,
                description: $row['description'],
                ticket: $row['ticket'],
            );
        }

        return $flags;
    }
}
```

```sql
-- migrations/create_feature_flags_table.sql
CREATE TABLE feature_flags (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(128) NOT NULL UNIQUE,
    type ENUM('boolean', 'percentage', 'user_segment', 'environment') NOT NULL DEFAULT 'boolean',
    enabled TINYINT(1) NOT NULL DEFAULT 0,
    percentage TINYINT UNSIGNED NOT NULL DEFAULT 100,
    allowed_segments JSON DEFAULT NULL,
    allowed_environments JSON DEFAULT NULL,
    description TEXT DEFAULT NULL,
    ticket VARCHAR(64) DEFAULT NULL,
    expires_at DATETIME DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at DATETIME DEFAULT NULL,
    INDEX idx_feature_flags_enabled (enabled),
    INDEX idx_feature_flags_expires (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### Redis Storage (Runtime Flags)

```php
<?php

declare(strict_types=1);

namespace Infrastructure\FeatureFlag;

use Domain\FeatureFlag\FeatureFlag;
use Domain\FeatureFlag\FlagType;

final readonly class RedisFeatureFlagLoader
{
    private const PREFIX = 'ff:';

    public function __construct(
        private \Redis $redis,
    ) {}

    /**
     * @return array<string, FeatureFlag>
     */
    public function load(): array
    {
        $keys = $this->redis->keys(self::PREFIX . '*');
        $flags = [];

        if (count($keys) === 0) {
            return $flags;
        }

        $values = $this->redis->mGet($keys);

        foreach ($keys as $i => $key) {
            $name = substr($key, strlen(self::PREFIX));
            $data = json_decode($values[$i], true, 512, JSON_THROW_ON_ERROR);

            $flags[$name] = new FeatureFlag(
                name: $name,
                type: FlagType::from($data['type'] ?? 'boolean'),
                enabled: $data['enabled'] ?? false,
                percentage: $data['percentage'] ?? 100,
                allowedSegments: $data['allowed_segments'] ?? [],
                allowedEnvironments: $data['allowed_environments'] ?? [],
                expiresAt: isset($data['expires_at'])
                    ? new \DateTimeImmutable($data['expires_at'])
                    : null,
                description: $data['description'] ?? null,
                ticket: $data['ticket'] ?? null,
            );
        }

        return $flags;
    }

    public function save(FeatureFlag $flag): void
    {
        $key = self::PREFIX . $flag->name;
        $data = json_encode([
            'type' => $flag->type->value,
            'enabled' => $flag->enabled,
            'percentage' => $flag->percentage,
            'allowed_segments' => $flag->allowedSegments,
            'allowed_environments' => $flag->allowedEnvironments,
            'expires_at' => $flag->expiresAt?->format('c'),
            'description' => $flag->description,
            'ticket' => $flag->ticket,
        ], JSON_THROW_ON_ERROR);

        if ($flag->expiresAt !== null) {
            $ttl = $flag->expiresAt->getTimestamp() - time();
            if ($ttl > 0) {
                $this->redis->setex($key, $ttl, $data);
                return;
            }
        }

        $this->redis->set($key, $data);
    }

    public function delete(string $featureName): void
    {
        $this->redis->del(self::PREFIX . $featureName);
    }
}
```

### Cached Loader (Config + Redis Cache)

```php
<?php

declare(strict_types=1);

namespace Infrastructure\FeatureFlag;

use Domain\FeatureFlag\FeatureFlag;

final class CachedFeatureFlagLoader
{
    private const CACHE_KEY = 'ff:all';
    private const CACHE_TTL = 60;

    public function __construct(
        private readonly YamlFeatureFlagLoader $yamlLoader,
        private readonly \Redis $redis,
    ) {}

    /**
     * @return array<string, FeatureFlag>
     */
    public function load(): array
    {
        $cached = $this->redis->get(self::CACHE_KEY);

        if ($cached !== false) {
            return unserialize($cached, ['allowed_classes' => [FeatureFlag::class, FlagType::class, \DateTimeImmutable::class]]);
        }

        $flags = $this->yamlLoader->load();

        $this->redis->setex(self::CACHE_KEY, self::CACHE_TTL, serialize($flags));

        return $flags;
    }

    public function invalidate(): void
    {
        $this->redis->del(self::CACHE_KEY);
    }
}
```

## Feature Flag Lifecycle

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Create  │───▶│  Enable  │───▶│  Rollout │───▶│ Full On  │───▶│  Remove  │
│   Flag   │    │  in Dev  │    │  10→100% │    │  100%    │    │   Flag   │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
   Day 1         Day 1-2         1-2 weeks        2 weeks         Sprint+1

 - Add YAML      - Test in       - Canary 10%    - Confirm OK     - Remove flag
 - Add ticket      staging       - Monitor        - All users      - Remove code
 - Add expiry    - QA verify     - 25% → 50%       on new path    - Remove YAML
                                 - Full rollout                    - Remove tests
```

### Lifecycle Management Commands

```php
<?php

declare(strict_types=1);

namespace Application\UseCase\FeatureFlag;

final readonly class CleanupExpiredFlagsUseCase
{
    public function __construct(
        private RedisFeatureFlagLoader $redisLoader,
        private DatabaseFeatureFlagLoader $dbLoader,
        private \Psr\Log\LoggerInterface $logger,
    ) {}

    /**
     * Find and report expired flags that should be cleaned up.
     *
     * @return list<array{name: string, expired_at: string, ticket: ?string}>
     */
    public function execute(): array
    {
        $flags = $this->dbLoader->load();
        $expired = [];

        foreach ($flags as $flag) {
            if ($flag->isExpired()) {
                $expired[] = [
                    'name' => $flag->name,
                    'expired_at' => $flag->expiresAt->format('c'),
                    'ticket' => $flag->ticket,
                ];

                $this->logger->warning('Feature flag expired and should be cleaned up', [
                    'flag' => $flag->name,
                    'expired_at' => $flag->expiresAt->format('c'),
                    'ticket' => $flag->ticket,
                ]);
            }
        }

        return $expired;
    }
}
```

### Stale Flag Detection (CI Step)

```php
<?php

declare(strict_types=1);

namespace Infrastructure\FeatureFlag\Console;

use Symfony\Component\Console\Command\Command;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Output\OutputInterface;

final class DetectStaleFlagsCommand extends Command
{
    protected static $defaultName = 'feature-flags:detect-stale';

    public function __construct(
        private readonly YamlFeatureFlagLoader $loader,
    ) {
        parent::__construct();
    }

    protected function execute(InputInterface $input, OutputInterface $output): int
    {
        $flags = $this->loader->load();
        $threshold = new \DateTimeImmutable('+7 days');
        $staleCount = 0;

        foreach ($flags as $flag) {
            if ($flag->isStale($threshold)) {
                $output->writeln(sprintf(
                    '<error>STALE</error> Flag "%s" expires %s (ticket: %s)',
                    $flag->name,
                    $flag->expiresAt->format('Y-m-d'),
                    $flag->ticket ?? 'none',
                ));
                $staleCount++;
            }
        }

        if ($staleCount > 0) {
            $output->writeln(sprintf('<error>%d stale flags found</error>', $staleCount));
            return Command::FAILURE;
        }

        $output->writeln('<info>No stale flags found</info>');
        return Command::SUCCESS;
    }
}
```

## Environment-Based Flags vs Runtime Flags

### Environment-Based (Build-Time)

```php
<?php
// Set at deploy time via environment variables, cannot change without redeploy

declare(strict_types=1);

namespace Infrastructure\FeatureFlag;

final readonly class EnvironmentFeatureFlagResolver
{
    /**
     * Reads flags from environment variables.
     * Convention: FEATURE_FLAG_{UPPERCASE_NAME}=1|0
     */
    public function isEnabled(string $featureName): bool
    {
        $envKey = 'FEATURE_FLAG_' . strtoupper(str_replace('-', '_', $featureName));

        return filter_var(
            $_ENV[$envKey] ?? $_SERVER[$envKey] ?? '0',
            FILTER_VALIDATE_BOOLEAN,
        );
    }
}
```

```yaml
# docker-compose.yml — environment flags
services:
  php-fpm:
    environment:
      FEATURE_FLAG_NEW_CHECKOUT: "1"
      FEATURE_FLAG_API_V3: "0"
      FEATURE_FLAG_DARK_MODE: "1"
```

### Runtime Flags (Redis-Backed, No Redeploy)

```php
<?php
// Can change at any time via admin panel or API, no redeploy needed

declare(strict_types=1);

namespace Infrastructure\FeatureFlag;

final readonly class RuntimeFeatureFlagResolver
{
    private const PREFIX = 'ff:runtime:';

    public function __construct(
        private \Redis $redis,
    ) {}

    public function isEnabled(string $featureName): bool
    {
        $value = $this->redis->get(self::PREFIX . $featureName);

        return $value === '1';
    }

    public function enable(string $featureName): void
    {
        $this->redis->set(self::PREFIX . $featureName, '1');
    }

    public function disable(string $featureName): void
    {
        $this->redis->set(self::PREFIX . $featureName, '0');
    }
}
```

### Combined Resolver (Environment Overrides Runtime)

```php
<?php

declare(strict_types=1);

namespace Infrastructure\FeatureFlag;

use Domain\FeatureFlag\FeatureFlagResolverInterface;

final readonly class ChainedFeatureFlagResolver implements FeatureFlagResolverInterface
{
    public function __construct(
        private EnvironmentFeatureFlagResolver $envResolver,
        private RuntimeFeatureFlagResolver $runtimeResolver,
        private FeatureFlagService $configResolver,
    ) {}

    /**
     * Resolution order:
     * 1. Environment variable (highest priority, set at deploy)
     * 2. Runtime flag (Redis, changeable without deploy)
     * 3. Config file flag (YAML, default)
     */
    public function isEnabled(string $featureName): bool
    {
        // Check environment override first
        $envKey = 'FEATURE_FLAG_' . strtoupper(str_replace('-', '_', $featureName));
        if (isset($_ENV[$envKey]) || isset($_SERVER[$envKey])) {
            return $this->envResolver->isEnabled($featureName);
        }

        // Check runtime (Redis) override
        $runtimeValue = $this->runtimeResolver->isEnabled($featureName);
        if ($runtimeValue) {
            return true;
        }

        // Fall back to config-based resolution
        return $this->configResolver->isEnabled($featureName);
    }

    public function isEnabledForIdentifier(string $featureName, string $identifier): bool
    {
        // Environment and runtime overrides take precedence
        $envKey = 'FEATURE_FLAG_' . strtoupper(str_replace('-', '_', $featureName));
        if (isset($_ENV[$envKey]) || isset($_SERVER[$envKey])) {
            return $this->envResolver->isEnabled($featureName);
        }

        return $this->configResolver->isEnabledForIdentifier($featureName, $identifier);
    }

    public function isEnabledForSegment(string $featureName, string $segment): bool
    {
        return $this->configResolver->isEnabledForSegment($featureName, $segment);
    }
}
```

## Integration with Deployment Strategies

### Canary + Feature Flags

```yaml
# features.yaml — canary-aware feature flags
features:
  new_checkout:
    type: percentage
    enabled: true
    percentage: 0       # Start at 0%, canary deploy script bumps this
    description: "New checkout — controlled via canary deploy"
    ticket: "SHOP-1234"
```

```bash
#!/bin/bash
# canary-with-flags.sh — combine canary traffic splitting with feature flags

VERSION="${1:?Usage: $0 <version>}"
FEATURE="${2:-new_checkout}"

# Stage 1: Deploy canary, enable flag for 10%
deploy_canary "$VERSION"
redis-cli SET "ff:runtime:${FEATURE}" "1"
update_feature_percentage "$FEATURE" 10

# Stage 2: Expand to 25%
sleep 600  # 10 min analysis
check_metrics || rollback
update_feature_percentage "$FEATURE" 25

# Stage 3: Expand to 100%
sleep 1800  # 30 min analysis
check_metrics || rollback
update_feature_percentage "$FEATURE" 100
promote_canary
```

## Cleanup: Removing Stale Flags

### Automated Flag Audit (CI Pipeline)

```yaml
# .github/workflows/feature-flag-audit.yml
name: Feature Flag Audit

on:
  schedule:
    - cron: '0 9 * * 1'  # Every Monday at 09:00
  workflow_dispatch:

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Check for stale flags
        run: |
          php bin/console feature-flags:detect-stale

      - name: Check for orphaned flag references in code
        run: |
          # Extract flag names from config
          CONFIGURED_FLAGS=$(grep -E "^  [a-z_]+:" config/features.yaml | sed 's/://;s/^ *//')

          # Search for flag references in PHP code
          for FLAG in $CONFIGURED_FLAGS; do
              COUNT=$(grep -r "$FLAG" src/ --include="*.php" -l 2>/dev/null | wc -l)
              if [[ "$COUNT" -eq 0 ]]; then
                  echo "WARNING: Flag '${FLAG}' is configured but not referenced in code"
              fi
          done

      - name: Check for code references to removed flags
        run: |
          CONFIGURED_FLAGS=$(grep -E "^  [a-z_]+:" config/features.yaml | sed 's/://;s/^ *//')

          # Find Feature:: calls in PHP code
          grep -roh "Feature::.*'[a-z_]*'" src/ --include="*.php" | \
              grep -oP "'[a-z_]+'" | sort -u | while read -r FLAG_REF; do
              FLAG_NAME=${FLAG_REF//\'/}
              if ! echo "$CONFIGURED_FLAGS" | grep -q "^${FLAG_NAME}$"; then
                  echo "ERROR: Code references flag '${FLAG_NAME}' which is not in config"
              fi
          done
```

### Cleanup Checklist

```
Feature Flag Removal Checklist:
┌───┐
│ 1 │ Verify flag is at 100% for all users (or disabled permanently)
├───┤
│ 2 │ Remove conditional code branches (keep only the enabled path)
├───┤
│ 3 │ Remove flag from config/features.yaml
├───┤
│ 4 │ Remove flag from Redis (if runtime flag)
├───┤
│ 5 │ Remove flag from database (if stored there)
├───┤
│ 6 │ Update tests (remove flag-dependent test branches)
├───┤
│ 7 │ Search for all references: grep -r "flag_name" src/ tests/ config/
├───┤
│ 8 │ Close the associated ticket
└───┘
```

## Detection Patterns

```bash
# Find feature flag service implementations
Grep: "FeatureFlag|isEnabled|feature.*flag" --glob "**/*.php"

# Check for feature flag configuration files
Grep: "features:|feature_flags:" --glob "*.yaml" --glob "*.yml"

# Find feature flag checks in application code
Grep: "Feature::enabled|isEnabled\(|isEnabledFor" --glob "**/*.php"

# Check for environment-based feature flags
Grep: "FEATURE_FLAG_|feature_flag_" --glob "*.env*" --glob "docker-compose*.yml"

# Find feature flag Redis keys
Grep: "ff:|feature:" --glob "**/*.php"

# Check for stale flag detection
Grep: "isExpired|isStale|expires_at|detect.*stale" --glob "**/*.php"

# Find feature flag middleware or attributes
Grep: "RequiresFeature|FeatureFlagMiddleware|feature.*middleware" --glob "**/*.php"

# Check for percentage-based rollout logic
Grep: "checkPercentage|crc32|bucket.*100|percentage.*rollout" --glob "**/*.php"
```

## Summary Table

| Flag Type | Use Case | Storage | Change Without Deploy |
|-----------|----------|---------|----------------------|
| **Boolean** | Kill switch, maintenance mode | Config YAML / Redis | Redis: yes, YAML: no |
| **Percentage** | Gradual rollout (10% -> 100%) | Config YAML / Redis | Redis: yes, YAML: no |
| **User Segment** | Beta testers, premium users | Config YAML / Database | Database: yes, YAML: no |
| **Environment** | Dev-only features, staging previews | Config YAML / ENV vars | ENV: requires redeploy |
| **Runtime (Redis)** | Emergency toggles, live experiments | Redis | Yes (instant) |
| **Combined (Chained)** | Production with overrides | ENV > Redis > YAML | Partial (depends on layer) |
