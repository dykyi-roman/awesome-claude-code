# Blue-Green Deployment Patterns

Detailed patterns for zero-downtime blue-green deployments in PHP 8.4 projects with Docker and Kubernetes.

## Concept and Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    BLUE-GREEN DEPLOYMENT FLOW                       │
│                                                                     │
│  Phase 1: Deploy          Phase 2: Verify          Phase 3: Switch  │
│  ┌──────────┐             ┌──────────┐             ┌──────────┐    │
│  │ Blue v1  │──active──▶  │ Blue v1  │──active──▶  │ Blue v1  │    │
│  │ (active) │             │ (active) │             │ (idle)   │    │
│  └──────────┘             └──────────┘             └──────────┘    │
│  ┌──────────┐             ┌──────────┐             ┌──────────┐    │
│  │ Green    │──deploy──▶  │ Green v2 │──health──▶  │ Green v2 │    │
│  │ (idle)   │    v2       │ (idle)   │   check     │ (active) │    │
│  └──────────┘             └──────────┘             └──────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

Two identical environments run in parallel. Only one receives production traffic at a time. The inactive environment receives the new version, gets verified, then traffic switches instantly.

## Docker Compose Blue-Green Setup

### docker-compose.blue-green.yml

```yaml
services:
  nginx:
    image: nginx:1.27-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/blue-green.conf:/etc/nginx/conf.d/default.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      php-blue:
        condition: service_healthy
      php-green:
        condition: service_healthy
    networks:
      - frontend

  php-blue:
    image: ${REGISTRY}/app:${BLUE_VERSION:-latest}
    environment:
      APP_ENV: production
      APP_SLOT: blue
    healthcheck:
      test: ["CMD", "php-fpm-healthcheck"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 30s
    networks:
      - frontend
      - backend

  php-green:
    image: ${REGISTRY}/app:${GREEN_VERSION:-latest}
    environment:
      APP_ENV: production
      APP_SLOT: green
    healthcheck:
      test: ["CMD", "php-fpm-healthcheck"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 30s
    networks:
      - frontend
      - backend

  mysql:
    image: mysql:8.4
    networks:
      - backend

  redis:
    image: redis:7-alpine
    networks:
      - backend

networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true
```

## Nginx Traffic Switching Configuration

### nginx/blue-green.conf

```nginx
# Active upstream is controlled by a shared file
# Updated atomically during traffic switch

upstream blue_backend {
    server php-blue:9000;
}

upstream green_backend {
    server php-green:9000;
}

# Map active slot to upstream
map $active_slot $backend {
    "blue"  blue_backend;
    "green" green_backend;
    default blue_backend;
}

server {
    listen 80;
    server_name example.com;

    root /var/www/html/public;
    index index.php;

    # Read active slot from file (updated by deploy script)
    set_by_lua_block $active_slot {
        local f = io.open("/etc/nginx/active-slot", "r")
        if f then
            local slot = f:read("*l")
            f:close()
            return slot
        end
        return "blue"
    }

    location / {
        try_files $uri /index.php$is_args$args;
    }

    location ~ \.php$ {
        fastcgi_pass $backend;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        include fastcgi_params;
    }

    # Health endpoint for external monitoring
    location /health {
        access_log off;
        fastcgi_pass $backend;
        fastcgi_param SCRIPT_FILENAME $document_root/index.php;
        include fastcgi_params;
    }
}
```

### Simple Nginx Switch (without Lua)

```nginx
# Option: use include-based switching
# Active file is symlinked by deploy script

# /etc/nginx/conf.d/upstream-active.conf -> upstream-blue.conf
include /etc/nginx/conf.d/upstream-active.conf;

server {
    listen 80;
    server_name example.com;

    location ~ \.php$ {
        fastcgi_pass active_backend;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        include fastcgi_params;
    }
}
```

```bash
# upstream-blue.conf
# upstream active_backend { server php-blue:9000; }

# upstream-green.conf
# upstream active_backend { server php-green:9000; }

# Switch traffic:
ln -sf /etc/nginx/conf.d/upstream-green.conf /etc/nginx/conf.d/upstream-active.conf
nginx -s reload
```

## Kubernetes Blue-Green Deployment

### Service and Deployment Manifests

```yaml
# deployment-blue.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-blue
  labels:
    app: myapp
    slot: blue
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
      slot: blue
  template:
    metadata:
      labels:
        app: myapp
        slot: blue
        version: v1.2.3
    spec:
      containers:
        - name: php-fpm
          image: registry.example.com/app:v1.2.3
          ports:
            - containerPort: 9000
          readinessProbe:
            httpGet:
              path: /health/ready
              port: 8080
            initialDelaySeconds: 10
            periodSeconds: 5
          livenessProbe:
            httpGet:
              path: /health/live
              port: 8080
            initialDelaySeconds: 15
            periodSeconds: 10
          resources:
            requests:
              cpu: 250m
              memory: 256Mi
            limits:
              cpu: 500m
              memory: 512Mi
---
# deployment-green.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-green
  labels:
    app: myapp
    slot: green
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
      slot: green
  template:
    metadata:
      labels:
        app: myapp
        slot: green
        version: v1.2.4
    spec:
      containers:
        - name: php-fpm
          image: registry.example.com/app:v1.2.4
          ports:
            - containerPort: 9000
          readinessProbe:
            httpGet:
              path: /health/ready
              port: 8080
            initialDelaySeconds: 10
            periodSeconds: 5
          livenessProbe:
            httpGet:
              path: /health/live
              port: 8080
            initialDelaySeconds: 15
            periodSeconds: 10
---
# service.yaml — switch by changing selector
apiVersion: v1
kind: Service
metadata:
  name: app-service
spec:
  selector:
    app: myapp
    slot: blue  # Change to "green" for traffic switch
  ports:
    - port: 80
      targetPort: 9000
```

### Traffic Switch Script (kubectl)

```bash
#!/bin/bash
# k8s-blue-green-switch.sh

set -euo pipefail

NAMESPACE="${NAMESPACE:-production}"
SERVICE_NAME="app-service"
TARGET_SLOT="${1:?Usage: $0 <blue|green>}"

echo "Switching traffic to ${TARGET_SLOT}..."

# Verify target deployment is healthy
READY=$(kubectl -n "$NAMESPACE" get deployment "app-${TARGET_SLOT}" \
    -o jsonpath='{.status.readyReplicas}')
DESIRED=$(kubectl -n "$NAMESPACE" get deployment "app-${TARGET_SLOT}" \
    -o jsonpath='{.spec.replicas}')

if [[ "$READY" != "$DESIRED" ]]; then
    echo "ERROR: app-${TARGET_SLOT} not ready (${READY}/${DESIRED} pods)"
    exit 1
fi

# Switch service selector
kubectl -n "$NAMESPACE" patch service "$SERVICE_NAME" \
    -p "{\"spec\":{\"selector\":{\"slot\":\"${TARGET_SLOT}\"}}}"

echo "Traffic switched to ${TARGET_SLOT}"

# Verify switch
kubectl -n "$NAMESPACE" get endpoints "$SERVICE_NAME"
```

## Health Check Verification Before Switch

### PHP Health Check Controller

```php
<?php

declare(strict_types=1);

namespace App\Presentation\Api\Action;

use App\Infrastructure\HealthCheck\HealthCheckRunner;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;

final readonly class ReadinessAction
{
    public function __construct(
        private HealthCheckRunner $healthCheckRunner,
    ) {}

    public function __invoke(ServerRequestInterface $request): ResponseInterface
    {
        $results = $this->healthCheckRunner->runAll();
        $allHealthy = array_reduce(
            $results,
            static fn(bool $carry, array $result): bool => $carry && $result['healthy'],
            true,
        );

        $statusCode = $allHealthy ? 200 : 503;

        return new JsonResponse(
            data: [
                'status' => $allHealthy ? 'ready' : 'not_ready',
                'checks' => $results,
                'slot' => $_ENV['APP_SLOT'] ?? 'unknown',
                'version' => $_ENV['APP_VERSION'] ?? 'unknown',
                'timestamp' => (new \DateTimeImmutable())->format('c'),
            ],
            status: $statusCode,
        );
    }
}
```

### Deploy Script with Health Verification

```bash
#!/bin/bash
# blue-green-deploy.sh

set -euo pipefail

VERSION="${1:?Usage: $0 <version>}"
MAX_RETRIES=30
RETRY_INTERVAL=10

# Determine active and inactive slots
ACTIVE_SLOT=$(cat /etc/nginx/active-slot 2>/dev/null || echo "blue")
if [[ "$ACTIVE_SLOT" == "blue" ]]; then
    INACTIVE_SLOT="green"
else
    INACTIVE_SLOT="blue"
fi

echo "Active: ${ACTIVE_SLOT}, Deploying to: ${INACTIVE_SLOT}"

# 1. Deploy new version to inactive slot
export "${INACTIVE_SLOT^^}_VERSION=${VERSION}"
docker compose -f docker-compose.blue-green.yml up -d "php-${INACTIVE_SLOT}"

# 2. Wait for health check
echo "Waiting for health check..."
for i in $(seq 1 "$MAX_RETRIES"); do
    HEALTH=$(curl -sf "http://php-${INACTIVE_SLOT}:8080/health/ready" 2>/dev/null || echo '{}')
    STATUS=$(echo "$HEALTH" | jq -r '.status // "unknown"')

    if [[ "$STATUS" == "ready" ]]; then
        echo "Health check passed on attempt ${i}"
        break
    fi

    if [[ "$i" -eq "$MAX_RETRIES" ]]; then
        echo "ERROR: Health check failed after ${MAX_RETRIES} attempts"
        docker compose -f docker-compose.blue-green.yml stop "php-${INACTIVE_SLOT}"
        exit 1
    fi

    echo "Attempt ${i}/${MAX_RETRIES}: status=${STATUS}, retrying in ${RETRY_INTERVAL}s..."
    sleep "$RETRY_INTERVAL"
done

# 3. Run smoke tests against inactive slot
echo "Running smoke tests..."
if ! ./scripts/smoke-test.sh "http://php-${INACTIVE_SLOT}:8080"; then
    echo "ERROR: Smoke tests failed, aborting deployment"
    docker compose -f docker-compose.blue-green.yml stop "php-${INACTIVE_SLOT}"
    exit 1
fi

# 4. Switch traffic
echo "${INACTIVE_SLOT}" > /etc/nginx/active-slot
nginx -s reload
echo "Traffic switched to ${INACTIVE_SLOT}"

# 5. Post-switch verification
sleep 5
ERROR_RATE=$(curl -sf "http://localhost/metrics" | grep error_rate | awk '{print $2}')
if (( $(echo "$ERROR_RATE > 5" | bc -l) )); then
    echo "ERROR: High error rate detected (${ERROR_RATE}%), rolling back"
    echo "${ACTIVE_SLOT}" > /etc/nginx/active-slot
    nginx -s reload
    exit 1
fi

echo "Deployment of ${VERSION} to ${INACTIVE_SLOT} completed successfully"
```

## Database Migration Considerations

### Backward-Compatible Migration Strategy

```
Deploy Sequence (4 phases):

Phase 1: Add new column          Phase 2: Dual-write
┌─────────────┐                  ┌─────────────┐
│ Blue (v1)   │ ◀── traffic      │ Blue (v1)   │
│ reads: name │                  │ writes: name │
└─────────────┘                  └─────────────┘
┌─────────────┐                  ┌─────────────┐
│ Green (v1a) │                  │ Green (v2)  │ ◀── traffic
│ + full_name │ migration        │ writes: both│
└─────────────┘                  └─────────────┘

Phase 3: Switch reads            Phase 4: Drop old column
┌─────────────┐                  ┌─────────────┐
│ Blue (v3)   │ ◀── traffic      │ Blue (v4)   │ ◀── traffic
│ reads: both │                  │ no old col  │
└─────────────┘                  └─────────────┘
```

### PHP Migration Runner

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Migration;

final readonly class BlueGreenMigrationValidator
{
    public function __construct(
        private \PDO $pdo,
    ) {}

    /**
     * Verify migration is backward-compatible before allowing traffic switch.
     */
    public function validateBackwardCompatibility(string $migrationId): bool
    {
        // Check no columns were dropped
        $droppedColumns = $this->getDroppedColumns($migrationId);
        if (count($droppedColumns) > 0) {
            throw new \RuntimeException(sprintf(
                'Migration %s drops columns [%s]. This is not backward-compatible. '
                . 'Use a multi-phase migration strategy instead.',
                $migrationId,
                implode(', ', $droppedColumns),
            ));
        }

        // Check no column types were changed
        $changedTypes = $this->getChangedColumnTypes($migrationId);
        if (count($changedTypes) > 0) {
            throw new \RuntimeException(sprintf(
                'Migration %s changes column types [%s]. '
                . 'Add a new column instead and migrate data separately.',
                $migrationId,
                implode(', ', $changedTypes),
            ));
        }

        return true;
    }
}
```

## Rollback Procedure

```bash
#!/bin/bash
# rollback.sh — instant rollback by switching back to previous active slot

set -euo pipefail

CURRENT_ACTIVE=$(cat /etc/nginx/active-slot)
if [[ "$CURRENT_ACTIVE" == "blue" ]]; then
    ROLLBACK_TO="green"
else
    ROLLBACK_TO="blue"
fi

echo "Rolling back: switching traffic from ${CURRENT_ACTIVE} to ${ROLLBACK_TO}"

# Verify rollback target is still healthy
HEALTH=$(curl -sf "http://php-${ROLLBACK_TO}:8080/health/ready" || echo '{}')
STATUS=$(echo "$HEALTH" | jq -r '.status // "unknown"')

if [[ "$STATUS" != "ready" ]]; then
    echo "WARNING: Rollback target ${ROLLBACK_TO} is not healthy (status=${STATUS})"
    echo "Attempting to restart..."
    docker compose -f docker-compose.blue-green.yml restart "php-${ROLLBACK_TO}"
    sleep 15
fi

# Switch traffic
echo "${ROLLBACK_TO}" > /etc/nginx/active-slot
nginx -s reload

echo "Rolled back to ${ROLLBACK_TO}"
echo "Verify: curl -sf http://localhost/health/ready | jq ."
```

## GitHub Actions Blue-Green Workflow

```yaml
# .github/workflows/blue-green-deploy.yml
name: Blue-Green Deploy

on:
  workflow_dispatch:
    inputs:
      version:
        description: 'Version to deploy (e.g., v1.2.4)'
        required: true
      environment:
        description: 'Target environment'
        type: choice
        options: [staging, production]
        default: staging

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: ${{ inputs.environment }}
    steps:
      - uses: actions/checkout@v4

      - name: Determine active slot
        id: slot
        run: |
          ACTIVE=$(ssh deploy@${{ vars.DEPLOY_HOST }} "cat /etc/nginx/active-slot" 2>/dev/null || echo "blue")
          if [[ "$ACTIVE" == "blue" ]]; then
            echo "inactive=green" >> "$GITHUB_OUTPUT"
          else
            echo "inactive=blue" >> "$GITHUB_OUTPUT"
          fi
          echo "active=${ACTIVE}" >> "$GITHUB_OUTPUT"

      - name: Deploy to inactive slot
        run: |
          ssh deploy@${{ vars.DEPLOY_HOST }} << 'DEPLOY'
            export VERSION=${{ inputs.version }}
            export SLOT=${{ steps.slot.outputs.inactive }}
            docker pull ${{ vars.REGISTRY }}/app:${VERSION}
            docker compose -f docker-compose.blue-green.yml up -d php-${SLOT}
          DEPLOY

      - name: Wait for health check
        run: |
          SLOT=${{ steps.slot.outputs.inactive }}
          for i in $(seq 1 30); do
            STATUS=$(ssh deploy@${{ vars.DEPLOY_HOST }} \
              "curl -sf http://php-${SLOT}:8080/health/ready | jq -r .status" 2>/dev/null || echo "unknown")
            if [[ "$STATUS" == "ready" ]]; then
              echo "Health check passed"
              exit 0
            fi
            echo "Attempt ${i}/30: ${STATUS}"
            sleep 10
          done
          echo "::error::Health check failed"
          exit 1

      - name: Run smoke tests
        run: |
          SLOT=${{ steps.slot.outputs.inactive }}
          ssh deploy@${{ vars.DEPLOY_HOST }} "./scripts/smoke-test.sh http://php-${SLOT}:8080"

      - name: Switch traffic
        run: |
          SLOT=${{ steps.slot.outputs.inactive }}
          ssh deploy@${{ vars.DEPLOY_HOST }} << SWITCH
            echo "${SLOT}" > /etc/nginx/active-slot
            nginx -s reload
          SWITCH

      - name: Post-switch verification
        run: |
          sleep 10
          STATUS=$(ssh deploy@${{ vars.DEPLOY_HOST }} \
            "curl -sf http://localhost/health/ready | jq -r .status")
          if [[ "$STATUS" != "ready" ]]; then
            echo "::error::Post-switch health check failed, initiating rollback"
            ROLLBACK=${{ steps.slot.outputs.active }}
            ssh deploy@${{ vars.DEPLOY_HOST }} << ROLLBACK
              echo "${ROLLBACK}" > /etc/nginx/active-slot
              nginx -s reload
            ROLLBACK
            exit 1
          fi

      - name: Notify deployment
        if: success()
        run: |
          curl -X POST "${{ secrets.SLACK_WEBHOOK }}" \
            -H 'Content-Type: application/json' \
            -d "{\"text\":\"Deployed ${{ inputs.version }} to ${{ inputs.environment }} (slot: ${{ steps.slot.outputs.inactive }})\"}"

      - name: Notify rollback
        if: failure()
        run: |
          curl -X POST "${{ secrets.SLACK_WEBHOOK }}" \
            -H 'Content-Type: application/json' \
            -d "{\"text\":\"ROLLBACK: ${{ inputs.version }} deployment to ${{ inputs.environment }} failed\"}"
```

## Detection Patterns

```bash
# Find blue-green deployment configurations
Grep: "blue.*green|green.*blue|active.slot|ACTIVE_SLOT" --glob "*.yml" --glob "*.yaml" --glob "*.sh"

# Check for blue-green Docker Compose setup
Grep: "php-blue|php-green|APP_SLOT" --glob "docker-compose*.yml"

# Find Nginx traffic switching configs
Grep: "upstream.*blue|upstream.*green|active_slot|active_backend" --glob "*.conf"

# Check Kubernetes blue-green selectors
Grep: "slot:.*blue|slot:.*green" --glob "*.yaml" --glob "*.yml"

# Find deployment switch scripts
Grep: "switch_traffic|nginx.*reload|active-slot" --glob "*.sh"

# Check for health verification in deploy scripts
Grep: "health.*ready|health_check|smoke.test" --glob "*.sh" --glob "*.yml"
```

## Summary Table

| Phase | Action | Verify |
|-------|--------|--------|
| **1. Prepare** | Identify active/inactive slot | `cat /etc/nginx/active-slot` |
| **2. Deploy** | Deploy new version to inactive slot | Image pulled, container started |
| **3. Migrate DB** | Run backward-compatible migrations only | No dropped columns, no type changes |
| **4. Health Check** | Poll `/health/ready` on inactive slot | HTTP 200, all checks pass |
| **5. Smoke Test** | Run critical path tests against inactive | All smoke tests pass |
| **6. Switch** | Update Nginx upstream / K8s Service selector | Traffic flows to new slot |
| **7. Verify** | Monitor error rate, latency, 5xx count | Error rate < 1%, latency within SLA |
| **8. Rollback** | Switch traffic back to previous slot | Previous slot still healthy |
| **9. Cleanup** | Scale down old slot (optional) | Old slot stopped or kept as hot standby |
