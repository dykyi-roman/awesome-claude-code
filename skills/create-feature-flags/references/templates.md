# Feature Flag Templates

## In-Memory Implementation

```php
<?php
// src/Infrastructure/FeatureFlag/InMemoryFeatureFlagService.php

declare(strict_types=1);

namespace App\Infrastructure\FeatureFlag;

final class InMemoryFeatureFlagService implements FeatureFlagServiceInterface
{
    /**
     * @param array<string, FeatureConfig> $features
     */
    public function __construct(
        private readonly array $features,
    ) {}

    public function isEnabled(string $feature): bool
    {
        return $this->features[$feature]?->enabled ?? false;
    }

    public function isEnabledForUser(string $feature, string $userId): bool
    {
        $config = $this->features[$feature] ?? null;

        if ($config === null || !$config->enabled) {
            return false;
        }

        // Check if user is in allowed list
        if (in_array($userId, $config->allowedUsers, true)) {
            return true;
        }

        // Check if user is in blocked list
        if (in_array($userId, $config->blockedUsers, true)) {
            return false;
        }

        // Check percentage rollout
        if ($config->percentage !== null) {
            return $this->isInPercentage($userId, $config->percentage);
        }

        return $config->enabled;
    }

    public function isEnabledForPercentage(string $feature, string $identifier): bool
    {
        $config = $this->features[$feature] ?? null;

        if ($config === null || !$config->enabled || $config->percentage === null) {
            return false;
        }

        return $this->isInPercentage($identifier, $config->percentage);
    }

    public function getVariant(string $feature, string $userId): string
    {
        $config = $this->features[$feature] ?? null;

        if ($config === null || empty($config->variants)) {
            return 'control';
        }

        // Deterministic variant assignment based on user ID
        $hash = crc32($feature . $userId);
        $index = $hash % count($config->variants);

        return $config->variants[$index];
    }

    public function getEnabledFeatures(string $userId): array
    {
        $enabled = [];

        foreach ($this->features as $name => $config) {
            if ($this->isEnabledForUser($name, $userId)) {
                $enabled[] = $name;
            }
        }

        return $enabled;
    }

    private function isInPercentage(string $identifier, int $percentage): bool
    {
        // Deterministic percentage check based on identifier
        $hash = crc32($identifier);
        $bucket = abs($hash) % 100;

        return $bucket < $percentage;
    }
}
```

## YAML Configuration

```yaml
# config/features.yaml
features:
  # Simple on/off flag
  new_dashboard:
    enabled: true

  # Percentage rollout
  new_checkout:
    enabled: true
    percentage: 25

  # User targeting
  beta_features:
    enabled: true
    allowed_users:
      - user-123
      - user-456
    blocked_users:
      - user-789

  # A/B testing
  button_color:
    enabled: true
    variants:
      - blue
      - green
      - red

  # Combined: percentage + user override
  new_search:
    enabled: true
    percentage: 10
    allowed_users:
      - beta-tester-1
      - beta-tester-2
    metadata:
      description: "New search algorithm"
      jira_ticket: "SEARCH-123"
```

## Configuration Loader

```php
<?php
// src/Infrastructure/FeatureFlag/YamlFeatureConfigLoader.php

declare(strict_types=1);

namespace App\Infrastructure\FeatureFlag;

use Symfony\Component\Yaml\Yaml;

final class YamlFeatureConfigLoader
{
    public function __construct(
        private readonly string $configPath,
    ) {}

    /**
     * @return array<string, FeatureConfig>
     */
    public function load(): array
    {
        $data = Yaml::parseFile($this->configPath);
        $features = [];

        foreach ($data['features'] ?? [] as $name => $config) {
            $features[$name] = FeatureConfig::fromArray([
                'name' => $name,
                ...$config,
            ]);
        }

        return $features;
    }
}
```

## Feature Flag Attribute

```php
<?php
// src/Infrastructure/FeatureFlag/Attribute/RequiresFeature.php

declare(strict_types=1);

namespace App\Infrastructure\FeatureFlag\Attribute;

use Attribute;

#[Attribute(Attribute::TARGET_CLASS | Attribute::TARGET_METHOD)]
final readonly class RequiresFeature
{
    public function __construct(
        public string $feature,
        public ?string $fallback = null,
    ) {}
}
```

## Middleware for Feature Flags

```php
<?php
// src/Infrastructure/FeatureFlag/Middleware/FeatureFlagMiddleware.php

declare(strict_types=1);

namespace App\Infrastructure\FeatureFlag\Middleware;

use App\Infrastructure\FeatureFlag\FeatureFlagServiceInterface;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\MiddlewareInterface;
use Psr\Http\Server\RequestHandlerInterface;

final readonly class FeatureFlagMiddleware implements MiddlewareInterface
{
    public function __construct(
        private FeatureFlagServiceInterface $featureFlags,
    ) {}

    public function process(
        ServerRequestInterface $request,
        RequestHandlerInterface $handler,
    ): ResponseInterface {
        // Get user ID from request (auth, session, or anonymous)
        $userId = $this->getUserId($request);

        // Get all enabled features for this user
        $enabledFeatures = $this->featureFlags->getEnabledFeatures($userId);

        // Add to request attributes
        $request = $request
            ->withAttribute('feature_flags', $enabledFeatures)
            ->withAttribute('user_id', $userId);

        return $handler->handle($request);
    }

    private function getUserId(ServerRequestInterface $request): string
    {
        // Try to get from auth
        $user = $request->getAttribute('user');
        if ($user !== null) {
            return $user->getId();
        }

        // Fall back to session or cookie
        $cookies = $request->getCookieParams();
        return $cookies['visitor_id'] ?? uniqid('anon-', true);
    }
}
```

## Twig Extension

```php
<?php
// src/Infrastructure/FeatureFlag/Twig/FeatureFlagExtension.php

declare(strict_types=1);

namespace App\Infrastructure\FeatureFlag\Twig;

use App\Infrastructure\FeatureFlag\FeatureFlagServiceInterface;
use Twig\Extension\AbstractExtension;
use Twig\TwigFunction;

final class FeatureFlagExtension extends AbstractExtension
{
    public function __construct(
        private readonly FeatureFlagServiceInterface $featureFlags,
    ) {}

    public function getFunctions(): array
    {
        return [
            new TwigFunction('feature_enabled', [$this, 'isEnabled']),
            new TwigFunction('feature_variant', [$this, 'getVariant']),
        ];
    }

    public function isEnabled(string $feature, ?string $userId = null): bool
    {
        if ($userId !== null) {
            return $this->featureFlags->isEnabledForUser($feature, $userId);
        }

        return $this->featureFlags->isEnabled($feature);
    }

    public function getVariant(string $feature, string $userId): string
    {
        return $this->featureFlags->getVariant($feature, $userId);
    }
}
```

## Template Usage

```twig
{# In Twig templates #}

{% if feature_enabled('new_dashboard', user.id) %}
    {% include 'dashboard/new.html.twig' %}
{% else %}
    {% include 'dashboard/legacy.html.twig' %}
{% endif %}

{# A/B testing #}
{% set variant = feature_variant('button_color', user.id) %}
<button class="btn btn-{{ variant }}">
    Click me
</button>
```

## CI/CD Integration

### Environment-Based Flags

```yaml
# .github/workflows/deploy.yml
jobs:
  deploy:
    steps:
      - name: Set feature flags for environment
        run: |
          if [ "${{ github.ref }}" = "refs/heads/main" ]; then
            # Production: conservative rollout
            echo "NEW_CHECKOUT_PERCENTAGE=10" >> $GITHUB_ENV
          else
            # Staging: full rollout
            echo "NEW_CHECKOUT_PERCENTAGE=100" >> $GITHUB_ENV
          fi

      - name: Deploy with flags
        run: |
          helm upgrade app ./chart \
            --set featureFlags.newCheckout.percentage=$NEW_CHECKOUT_PERCENTAGE
```

### Dynamic Flag Updates

```yaml
# GitLab CI
update:feature:
  stage: deploy
  script:
    - |
      curl -X PATCH "https://api.example.com/features/$FEATURE_NAME" \
        -H "Authorization: Bearer $API_TOKEN" \
        -d "{\"percentage\": $NEW_PERCENTAGE}"
  rules:
    - if: $CI_PIPELINE_SOURCE == "web"
  when: manual
```

## Redis-Based Feature Flags

```php
<?php
// src/Infrastructure/FeatureFlag/RedisFeatureFlagService.php

declare(strict_types=1);

namespace App\Infrastructure\FeatureFlag;

use Redis;

final class RedisFeatureFlagService implements FeatureFlagServiceInterface
{
    private const PREFIX = 'feature:';

    public function __construct(
        private readonly Redis $redis,
        private readonly int $cacheTtl = 60,
    ) {}

    public function isEnabled(string $feature): bool
    {
        $key = self::PREFIX . $feature;
        $data = $this->redis->get($key);

        if ($data === false) {
            return false;
        }

        $config = json_decode($data, true);
        return $config['enabled'] ?? false;
    }

    public function setFeature(string $feature, FeatureConfig $config): void
    {
        $key = self::PREFIX . $feature;
        $this->redis->setex($key, $this->cacheTtl, json_encode([
            'enabled' => $config->enabled,
            'percentage' => $config->percentage,
            'allowed_users' => $config->allowedUsers,
            'blocked_users' => $config->blockedUsers,
            'variants' => $config->variants,
        ]));
    }

    // ... other methods
}
```
