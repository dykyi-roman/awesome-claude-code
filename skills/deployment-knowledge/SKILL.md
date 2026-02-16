---
name: acc-deployment-knowledge
description: Deployment knowledge base. Provides zero-downtime strategies, blue-green deployment, canary releases, rolling updates, rollback procedures, feature flags, and health check patterns.
---

# Deployment Knowledge Base

Quick reference for deployment strategies, zero-downtime patterns, and release management.

## Deployment Strategies

### Strategy Comparison

| Strategy | Downtime | Rollback Speed | Risk | Resource Usage |
|----------|----------|----------------|------|----------------|
| **Recreate** | Yes | Slow | High | 1x |
| **Rolling** | No | Medium | Medium | 1.25x |
| **Blue-Green** | No | Instant | Low | 2x |
| **Canary** | No | Fast | Very Low | 1.1x |
| **A/B Testing** | No | Fast | Low | Variable |

```
┌─────────────────────────────────────────────────────────────────┐
│                    DEPLOYMENT STRATEGIES                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  RECREATE         ROLLING          BLUE-GREEN       CANARY      │
│  ┌───┐           ┌───┬───┐        ┌───┐ ┌───┐     ┌───┐        │
│  │ v1│           │v1 │v1 │        │ v1│ │ v2│     │v1 │ 90%    │
│  └───┘           └───┴───┘        └───┘ └───┘     └───┘        │
│    ↓               ↓  ↓              ↕             ┌───┐        │
│  ┌───┐           ┌───┬───┐        Traffic         │v2 │ 10%    │
│  │ v2│           │v2 │v1 │        Switch          └───┘        │
│  └───┘           └───┴───┘                                      │
│                    ↓  ↓                                         │
│                  ┌───┬───┐                                      │
│                  │v2 │v2 │                                      │
│                  └───┴───┘                                      │
└─────────────────────────────────────────────────────────────────┘
```

## Blue-Green Deployment

### Overview

Two identical environments (Blue = current, Green = new). Traffic switches instantly.

```yaml
# Environment structure
environments:
  blue:
    url: blue.example.com
    version: v1.2.3
    active: true

  green:
    url: green.example.com
    version: v1.2.4
    active: false

# Load balancer config
upstream backend {
    server blue.example.com weight=100;
    server green.example.com weight=0;
}
```

### Deployment Steps

```bash
#!/bin/bash
# blue-green-deploy.sh

ACTIVE=$(get_active_environment)
INACTIVE=$(get_inactive_environment)

# 1. Deploy to inactive environment
deploy_to_environment $INACTIVE $VERSION

# 2. Run health checks
if ! health_check $INACTIVE; then
    echo "Health check failed, aborting"
    exit 1
fi

# 3. Run smoke tests
if ! smoke_tests $INACTIVE; then
    echo "Smoke tests failed, aborting"
    exit 1
fi

# 4. Switch traffic
switch_traffic_to $INACTIVE

# 5. Verify
if ! verify_deployment $INACTIVE; then
    echo "Verification failed, rolling back"
    switch_traffic_to $ACTIVE
    exit 1
fi

# 6. Mark as active
set_active_environment $INACTIVE
```

### Rollback

```bash
# Instant rollback - just switch traffic back
switch_traffic_to $PREVIOUS_ACTIVE
```

## Canary Deployment

### Traffic Distribution

```yaml
# Canary stages
stages:
  - name: canary-5
    traffic: 5%
    duration: 10m

  - name: canary-25
    traffic: 25%
    duration: 30m

  - name: canary-50
    traffic: 50%
    duration: 1h

  - name: full-rollout
    traffic: 100%
```

### Implementation

```yaml
# nginx canary config
upstream backend {
    server stable.example.com weight=95;
    server canary.example.com weight=5;
}

# Or with cookie-based routing
map $cookie_canary $backend {
    "true"  canary.example.com;
    default stable.example.com;
}
```

### Canary Analysis

```yaml
# Automated canary analysis
analysis:
  metrics:
    - name: error_rate
      threshold: 1%
      comparison: less_than

    - name: latency_p99
      threshold: 500ms
      comparison: less_than

    - name: success_rate
      threshold: 99%
      comparison: greater_than

  duration: 10m
  interval: 1m

  on_failure: rollback
  on_success: promote
```

## Rolling Deployment

### Configuration

```yaml
# Kubernetes-style rolling update
deployment:
  replicas: 4
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
```

### Sequence

```
Time →
Pod 1: [v1][v1][v1][v2][v2][v2][v2]
Pod 2: [v1][v1][v1][v1][v2][v2][v2]
Pod 3: [v1][v1][v1][v1][v1][v2][v2]
Pod 4: [v1][v1][v1][v1][v1][v1][v2]
```

## Zero-Downtime Checklist

### Database Migrations

```php
// WRONG: Destructive migration
Schema::dropColumn('users', 'old_field');

// RIGHT: Backward-compatible migration
// Step 1: Add new column (deploy #1)
Schema::addColumn('users', 'new_field');

// Step 2: Migrate data (deploy #2)
DB::statement('UPDATE users SET new_field = old_field');

// Step 3: Switch code to use new_field (deploy #3)
// Step 4: Drop old column (deploy #4, weeks later)
Schema::dropColumn('users', 'old_field');
```

### Migration Strategies

| Change | Strategy |
|--------|----------|
| Add column | Add with default, deploy, backfill |
| Remove column | Stop using, deploy, wait, remove |
| Rename column | Add new, migrate, switch, remove old |
| Change type | Add new column, migrate, switch |
| Add index | Online DDL, low-traffic window |

### Health Checks

```php
// Readiness probe - can accept traffic?
public function ready(): JsonResponse
{
    return response()->json([
        'database' => $this->checkDatabase(),
        'cache' => $this->checkCache(),
        'queue' => $this->checkQueue(),
    ]);
}

// Liveness probe - is the app running?
public function live(): JsonResponse
{
    return response()->json(['status' => 'ok']);
}
```

## Feature Flags

### Implementation Patterns

```php
// Simple feature flag
if (Feature::enabled('new-checkout')) {
    return $this->newCheckout();
}
return $this->oldCheckout();

// User-based rollout
if (Feature::enabledForUser('new-checkout', $user)) {
    return $this->newCheckout();
}

// Percentage rollout
if (Feature::enabledForPercentage('new-checkout', 10)) {
    return $this->newCheckout();
}
```

### Feature Flag Service

```php
interface FeatureFlagService
{
    public function isEnabled(string $feature): bool;
    public function isEnabledForUser(string $feature, User $user): bool;
    public function isEnabledForPercentage(string $feature, int $percent): bool;
    public function getVariant(string $feature): string;
}
```

### Configuration

```yaml
# features.yaml
features:
  new-checkout:
    enabled: true
    rollout:
      type: percentage
      value: 25
    users:
      - user-123  # Beta testers
      - user-456

  dark-mode:
    enabled: true
    rollout:
      type: user_attribute
      attribute: plan
      values: [premium, enterprise]
```

### Best Practices

```
Feature Flag Lifecycle:
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Create  │───▶│  Rollout │───▶│ Full On  │───▶│  Remove  │
│   Flag   │    │  0-100%  │    │   100%   │    │   Flag   │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
     1 day         1-2 weeks       2 weeks         Sprint
```

## Rollback Procedures

### Automated Rollback Triggers

```yaml
rollback:
  triggers:
    - metric: error_rate
      threshold: 5%
      window: 5m

    - metric: latency_p95
      threshold: 2s
      window: 5m

    - metric: health_check_failures
      threshold: 3
      window: 1m

  actions:
    - switch_traffic_to_previous
    - notify_oncall
    - create_incident
```

### Manual Rollback

```bash
#!/bin/bash
# rollback.sh

# 1. Get previous version
PREVIOUS=$(get_previous_version)

# 2. Switch traffic immediately (blue-green)
switch_traffic_to $PREVIOUS_ENV

# Or redeploy previous version (rolling)
deploy_version $PREVIOUS

# 3. Verify
health_check_all

# 4. Notify
notify_team "Rolled back to $PREVIOUS"
```

### Database Rollback

```php
// Always have down() migration
public function down(): void
{
    Schema::table('users', function (Blueprint $table) {
        $table->dropColumn('new_field');
    });
}
```

## Environment Configuration

### Environment Matrix

```yaml
environments:
  development:
    replicas: 1
    resources: minimal
    auto_deploy: true

  staging:
    replicas: 2
    resources: medium
    auto_deploy: true
    feature_flags: all_enabled

  production:
    replicas: 4+
    resources: full
    auto_deploy: false
    requires_approval: true
    deployment_window: "Mon-Thu 09:00-16:00"
```

### Secrets Management

```yaml
# DO NOT: Hardcode secrets
database_password: "secret123"

# DO: Use environment variables
database_password: ${DATABASE_PASSWORD}

# DO: Use secret managers
database_password:
  vault: production/database
  key: password
```

## Deployment Checklist

### Pre-Deployment

- [ ] All tests passing
- [ ] Code review approved
- [ ] Database migrations tested
- [ ] Rollback plan documented
- [ ] Monitoring alerts configured
- [ ] Stakeholders notified

### During Deployment

- [ ] Health checks passing
- [ ] No error spike in metrics
- [ ] Latency within SLA
- [ ] Smoke tests passing
- [ ] Feature flags working

### Post-Deployment

- [ ] Verify functionality
- [ ] Check error rates
- [ ] Monitor performance
- [ ] Update documentation
- [ ] Clean up old versions

## References

For detailed information, load these reference files:

- `references/blue-green.md` — Blue-green implementation details
- `references/canary.md` — Canary release patterns
- `references/feature-flags.md` — Feature flag best practices
