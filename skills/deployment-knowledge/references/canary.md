# Canary Deployment Patterns

Detailed patterns for canary releases in PHP 8.4 projects with Docker, Kubernetes, and automated analysis.

## Concept and Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                     CANARY RELEASE FLOW                             │
│                                                                     │
│  Phase 1: 10%     Phase 2: 25%     Phase 3: 50%     Phase 4: 100% │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐  │
│  │ Stable   │90%  │ Stable   │75%  │ Stable   │50%  │          │  │
│  │ v1.2.3   │     │ v1.2.3   │     │ v1.2.3   │     │ Promoted │  │
│  └──────────┘     └──────────┘     └──────────┘     │ v1.2.4   │  │
│  ┌────┐           ┌──────┐         ┌──────────┐     │  100%    │  │
│  │ v2 │10%        │ v2   │25%      │ v1.2.4   │50%  └──────────┘  │
│  └────┘           └──────┘         └──────────┘                    │
│     │                │                  │                │         │
│     ▼                ▼                  ▼                ▼         │
│  [Analyze]        [Analyze]          [Analyze]       [Complete]    │
│  10min            30min              1h              Full rollout   │
└─────────────────────────────────────────────────────────────────────┘
```

A small percentage of traffic is routed to the new version. Metrics are monitored at each stage. If metrics degrade, traffic is rolled back. If metrics hold, traffic percentage increases until full promotion.

## Nginx Weighted Traffic Splitting

### Percentage-Based Upstream

```nginx
# /etc/nginx/conf.d/canary.conf

# Canary weight file (updated by deploy script)
# Format: single integer 0-100
# Read by Lua or included as variable

upstream stable_backend {
    server php-stable:9000;
}

upstream canary_backend {
    server php-canary:9000;
}

split_clients "$request_id" $backend_pool {
    10%    canary_backend;
    *      stable_backend;
}

server {
    listen 80;
    server_name example.com;

    root /var/www/html/public;

    # Add canary header for debugging
    add_header X-Served-By $backend_pool always;

    location / {
        try_files $uri /index.php$is_args$args;
    }

    location ~ \.php$ {
        fastcgi_pass $backend_pool;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        include fastcgi_params;

        # Pass canary info to PHP
        fastcgi_param HTTP_X_CANARY_SLOT $backend_pool;
    }
}
```

### Cookie-Based Sticky Canary

```nginx
# Ensure user stays on the same backend during session

map $cookie_canary_slot $force_backend {
    "canary"  canary_backend;
    "stable"  stable_backend;
    default   "";
}

split_clients "$remote_addr$http_user_agent" $random_backend {
    10%    canary_backend;
    *      stable_backend;
}

map $force_backend $selected_backend {
    ""      $random_backend;
    default $force_backend;
}

server {
    listen 80;
    server_name example.com;

    location ~ \.php$ {
        fastcgi_pass $selected_backend;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        include fastcgi_params;

        # Set sticky cookie
        add_header Set-Cookie "canary_slot=$selected_backend; Path=/; Max-Age=3600" always;
    }
}
```

## Kubernetes Canary with Nginx Ingress

### Weight-Based Canary Ingress

```yaml
# stable-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: app-stable
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
    - host: example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: app-stable
                port:
                  number: 80
---
# canary-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: app-canary
  annotations:
    nginx.ingress.kubernetes.io/canary: "true"
    nginx.ingress.kubernetes.io/canary-weight: "10"
spec:
  ingressClassName: nginx
  rules:
    - host: example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: app-canary
                port:
                  number: 80
```

### Header-Based Canary (for QA testing)

```yaml
# canary-ingress-header.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: app-canary-header
  annotations:
    nginx.ingress.kubernetes.io/canary: "true"
    nginx.ingress.kubernetes.io/canary-by-header: "X-Canary"
    nginx.ingress.kubernetes.io/canary-by-header-value: "true"
spec:
  ingressClassName: nginx
  rules:
    - host: example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: app-canary
                port:
                  number: 80
```

```bash
# QA can force canary access:
curl -H "X-Canary: true" https://example.com/api/orders
```

## Kubernetes Canary with Istio

### VirtualService Traffic Splitting

```yaml
# istio-virtual-service.yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: app-vs
spec:
  hosts:
    - example.com
  gateways:
    - app-gateway
  http:
    - match:
        - headers:
            x-canary:
              exact: "true"
      route:
        - destination:
            host: app-canary
            port:
              number: 80
    - route:
        - destination:
            host: app-stable
            port:
              number: 80
          weight: 90
        - destination:
            host: app-canary
            port:
              number: 80
          weight: 10
---
# destination-rule.yaml
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: app-dr
spec:
  host: app-stable
  trafficPolicy:
    connectionPool:
      http:
        h2UpgradePolicy: DEFAULT
        maxRequestsPerConnection: 100
    outlierDetection:
      consecutive5xxErrors: 3
      interval: 10s
      baseEjectionTime: 30s
```

### Progressive Weight Update Script

```bash
#!/bin/bash
# canary-promote.sh — progressively increase canary traffic

set -euo pipefail

NAMESPACE="${NAMESPACE:-production}"
STAGES=(10 25 50 75 100)
ANALYSIS_DURATION=(600 1800 3600 1800 0)  # seconds to wait at each stage

for i in "${!STAGES[@]}"; do
    WEIGHT=${STAGES[$i]}
    STABLE_WEIGHT=$((100 - WEIGHT))
    WAIT=${ANALYSIS_DURATION[$i]}

    echo "Setting canary weight to ${WEIGHT}%..."

    kubectl -n "$NAMESPACE" patch virtualservice app-vs --type merge -p "
spec:
  http:
  - route:
    - destination:
        host: app-stable
        port:
          number: 80
      weight: ${STABLE_WEIGHT}
    - destination:
        host: app-canary
        port:
          number: 80
      weight: ${WEIGHT}
"

    if [[ "$WEIGHT" -eq 100 ]]; then
        echo "Canary promoted to 100%. Deployment complete."
        break
    fi

    echo "Waiting ${WAIT}s for analysis at ${WEIGHT}%..."
    sleep "$WAIT"

    # Check metrics before proceeding
    if ! ./scripts/canary-analysis.sh; then
        echo "ERROR: Canary analysis failed at ${WEIGHT}%, rolling back"
        kubectl -n "$NAMESPACE" patch virtualservice app-vs --type merge -p "
spec:
  http:
  - route:
    - destination:
        host: app-stable
        port:
          number: 80
      weight: 100
    - destination:
        host: app-canary
        port:
          number: 80
      weight: 0
"
        exit 1
    fi
done
```

## Monitoring Metrics for Canary Validation

### PHP Prometheus Metrics Middleware

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Monitoring\Middleware;

use Prometheus\CollectorRegistry;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\MiddlewareInterface;
use Psr\Http\Server\RequestHandlerInterface;

final readonly class CanaryMetricsMiddleware implements MiddlewareInterface
{
    public function __construct(
        private CollectorRegistry $registry,
        private string $slot,
    ) {}

    public function process(
        ServerRequestInterface $request,
        RequestHandlerInterface $handler,
    ): ResponseInterface {
        $startTime = microtime(true);

        try {
            $response = $handler->handle($request);

            $this->recordMetrics(
                method: $request->getMethod(),
                path: $request->getUri()->getPath(),
                statusCode: $response->getStatusCode(),
                duration: microtime(true) - $startTime,
            );

            return $response;
        } catch (\Throwable $e) {
            $this->recordMetrics(
                method: $request->getMethod(),
                path: $request->getUri()->getPath(),
                statusCode: 500,
                duration: microtime(true) - $startTime,
            );
            throw $e;
        }
    }

    private function recordMetrics(
        string $method,
        string $path,
        int $statusCode,
        float $duration,
    ): void {
        $labels = [$method, $path, (string) $statusCode, $this->slot];

        // Request counter
        $this->registry
            ->getOrRegisterCounter(
                'app',
                'http_requests_total',
                'Total HTTP requests',
                ['method', 'path', 'status', 'slot'],
            )
            ->inc($labels);

        // Latency histogram
        $this->registry
            ->getOrRegisterHistogram(
                'app',
                'http_request_duration_seconds',
                'HTTP request duration',
                ['method', 'path', 'status', 'slot'],
                [0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
            )
            ->observe($duration, $labels);

        // 5xx counter
        if ($statusCode >= 500) {
            $this->registry
                ->getOrRegisterCounter(
                    'app',
                    'http_server_errors_total',
                    'Total 5xx errors',
                    ['method', 'path', 'slot'],
                )
                ->inc([$method, $path, $this->slot]);
        }
    }
}
```

### Canary Analysis with Prometheus Queries

```yaml
# canary-analysis-config.yaml
analysis:
  # Each metric must pass for canary to proceed
  metrics:
    - name: error_rate
      query: |
        sum(rate(app_http_server_errors_total{slot="canary"}[5m]))
        /
        sum(rate(app_http_requests_total{slot="canary"}[5m]))
        * 100
      threshold: 1.0
      comparison: less_than
      description: "5xx error rate must be below 1%"

    - name: latency_p99
      query: |
        histogram_quantile(0.99,
          sum(rate(app_http_request_duration_seconds_bucket{slot="canary"}[5m])) by (le)
        )
      threshold: 0.5
      comparison: less_than
      description: "p99 latency must be below 500ms"

    - name: latency_p95
      query: |
        histogram_quantile(0.95,
          sum(rate(app_http_request_duration_seconds_bucket{slot="canary"}[5m])) by (le)
        )
      threshold: 0.25
      comparison: less_than
      description: "p95 latency must be below 250ms"

    - name: success_rate
      query: |
        sum(rate(app_http_requests_total{slot="canary",status=~"2.."}[5m]))
        /
        sum(rate(app_http_requests_total{slot="canary"}[5m]))
        * 100
      threshold: 99.0
      comparison: greater_than
      description: "Success rate must be above 99%"

    - name: canary_vs_stable_error_ratio
      query: |
        (
          sum(rate(app_http_server_errors_total{slot="canary"}[5m]))
          / sum(rate(app_http_requests_total{slot="canary"}[5m]))
        )
        /
        (
          sum(rate(app_http_server_errors_total{slot="stable"}[5m]))
          / sum(rate(app_http_requests_total{slot="stable"}[5m]))
        )
      threshold: 1.5
      comparison: less_than
      description: "Canary error rate must not exceed 1.5x stable error rate"

  duration: 10m
  interval: 1m
  min_requests: 100

  on_failure: rollback
  on_success: promote
```

### Automated Canary Analysis Script

```bash
#!/bin/bash
# canary-analysis.sh — query Prometheus and evaluate canary health

set -euo pipefail

PROMETHEUS_URL="${PROMETHEUS_URL:-http://prometheus:9090}"
CONFIG_FILE="${1:-canary-analysis-config.yaml}"

echo "Running canary analysis..."

# Error rate check
ERROR_RATE=$(curl -sf "${PROMETHEUS_URL}/api/v1/query" \
    --data-urlencode 'query=sum(rate(app_http_server_errors_total{slot="canary"}[5m])) / sum(rate(app_http_requests_total{slot="canary"}[5m])) * 100' \
    | jq -r '.data.result[0].value[1] // "0"')

echo "Error rate: ${ERROR_RATE}%"
if (( $(echo "$ERROR_RATE > 1.0" | bc -l) )); then
    echo "FAIL: Error rate ${ERROR_RATE}% exceeds threshold 1.0%"
    exit 1
fi

# P99 latency check
P99_LATENCY=$(curl -sf "${PROMETHEUS_URL}/api/v1/query" \
    --data-urlencode 'query=histogram_quantile(0.99, sum(rate(app_http_request_duration_seconds_bucket{slot="canary"}[5m])) by (le))' \
    | jq -r '.data.result[0].value[1] // "0"')

echo "P99 latency: ${P99_LATENCY}s"
if (( $(echo "$P99_LATENCY > 0.5" | bc -l) )); then
    echo "FAIL: P99 latency ${P99_LATENCY}s exceeds threshold 0.5s"
    exit 1
fi

# Success rate check
SUCCESS_RATE=$(curl -sf "${PROMETHEUS_URL}/api/v1/query" \
    --data-urlencode 'query=sum(rate(app_http_requests_total{slot="canary",status=~"2.."}[5m])) / sum(rate(app_http_requests_total{slot="canary"}[5m])) * 100' \
    | jq -r '.data.result[0].value[1] // "100"')

echo "Success rate: ${SUCCESS_RATE}%"
if (( $(echo "$SUCCESS_RATE < 99.0" | bc -l) )); then
    echo "FAIL: Success rate ${SUCCESS_RATE}% below threshold 99.0%"
    exit 1
fi

echo "PASS: All canary metrics within thresholds"
exit 0
```

## Rollback Criteria and Procedure

### Automatic Rollback Triggers

```yaml
# canary-rollback-policy.yaml
rollback:
  automatic_triggers:
    - metric: error_rate_5xx
      threshold: 2%
      window: 2m
      action: immediate_rollback

    - metric: latency_p99
      threshold: 1s
      window: 3m
      action: immediate_rollback

    - metric: pod_restart_count
      threshold: 3
      window: 5m
      action: immediate_rollback

    - metric: oom_kill_count
      threshold: 1
      window: 5m
      action: immediate_rollback

  manual_triggers:
    - on_call_engineer
    - deployment_dashboard

  rollback_actions:
    - set_canary_weight_to_zero
    - scale_down_canary_replicas
    - notify_slack_channel
    - create_incident_ticket
    - preserve_canary_logs
```

### Rollback Script

```bash
#!/bin/bash
# canary-rollback.sh

set -euo pipefail

NAMESPACE="${NAMESPACE:-production}"
REASON="${1:-manual rollback}"

echo "ROLLBACK: Reason: ${REASON}"

# 1. Remove canary traffic immediately
echo "Removing canary traffic..."
kubectl -n "$NAMESPACE" patch ingress app-canary \
    -p '{"metadata":{"annotations":{"nginx.ingress.kubernetes.io/canary-weight":"0"}}}'

# 2. Scale down canary
echo "Scaling down canary deployment..."
kubectl -n "$NAMESPACE" scale deployment app-canary --replicas=0

# 3. Verify stable is handling all traffic
sleep 5
STABLE_PODS=$(kubectl -n "$NAMESPACE" get pods -l app=myapp,slot=stable --field-selector=status.phase=Running -o name | wc -l)
echo "Stable pods running: ${STABLE_PODS}"

# 4. Preserve canary logs for investigation
echo "Saving canary logs..."
kubectl -n "$NAMESPACE" logs -l app=myapp,slot=canary --tail=1000 > "/tmp/canary-rollback-$(date +%Y%m%d-%H%M%S).log" 2>/dev/null || true

# 5. Notify
echo "Canary rollback complete. Reason: ${REASON}"
```

## GitHub Actions Canary Workflow

```yaml
# .github/workflows/canary-deploy.yml
name: Canary Deploy

on:
  workflow_dispatch:
    inputs:
      version:
        description: 'Version to deploy'
        required: true
      max_weight:
        description: 'Maximum canary weight before full promotion'
        type: choice
        options: ["10", "25", "50", "100"]
        default: "50"

env:
  NAMESPACE: production
  REGISTRY: registry.example.com

jobs:
  canary-deploy:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4

      - name: Deploy canary pods
        run: |
          kubectl -n $NAMESPACE set image deployment/app-canary \
            php-fpm=${{ env.REGISTRY }}/app:${{ inputs.version }}
          kubectl -n $NAMESPACE rollout status deployment/app-canary --timeout=120s

      - name: Stage 1 — 10% traffic
        run: |
          kubectl -n $NAMESPACE patch ingress app-canary \
            -p '{"metadata":{"annotations":{"nginx.ingress.kubernetes.io/canary-weight":"10"}}}'
          echo "Canary at 10%, waiting 10 minutes for analysis..."
          sleep 600

      - name: Analyze stage 1
        run: ./scripts/canary-analysis.sh

      - name: Stage 2 — 25% traffic
        if: inputs.max_weight >= 25
        run: |
          kubectl -n $NAMESPACE patch ingress app-canary \
            -p '{"metadata":{"annotations":{"nginx.ingress.kubernetes.io/canary-weight":"25"}}}'
          echo "Canary at 25%, waiting 30 minutes for analysis..."
          sleep 1800

      - name: Analyze stage 2
        if: inputs.max_weight >= 25
        run: ./scripts/canary-analysis.sh

      - name: Stage 3 — 50% traffic
        if: inputs.max_weight >= 50
        run: |
          kubectl -n $NAMESPACE patch ingress app-canary \
            -p '{"metadata":{"annotations":{"nginx.ingress.kubernetes.io/canary-weight":"50"}}}'
          echo "Canary at 50%, waiting 1 hour for analysis..."
          sleep 3600

      - name: Analyze stage 3
        if: inputs.max_weight >= 50
        run: ./scripts/canary-analysis.sh

      - name: Promote to 100%
        if: inputs.max_weight == 100
        run: |
          echo "Promoting canary to stable..."
          kubectl -n $NAMESPACE set image deployment/app-stable \
            php-fpm=${{ env.REGISTRY }}/app:${{ inputs.version }}
          kubectl -n $NAMESPACE rollout status deployment/app-stable --timeout=120s

          # Remove canary traffic
          kubectl -n $NAMESPACE patch ingress app-canary \
            -p '{"metadata":{"annotations":{"nginx.ingress.kubernetes.io/canary-weight":"0"}}}'

      - name: Rollback on failure
        if: failure()
        run: |
          echo "Canary failed, rolling back..."
          kubectl -n $NAMESPACE patch ingress app-canary \
            -p '{"metadata":{"annotations":{"nginx.ingress.kubernetes.io/canary-weight":"0"}}}'
          kubectl -n $NAMESPACE scale deployment app-canary --replicas=0

      - name: Notify result
        if: always()
        run: |
          STATUS="${{ job.status }}"
          curl -X POST "${{ secrets.SLACK_WEBHOOK }}" \
            -H 'Content-Type: application/json' \
            -d "{\"text\":\"Canary deploy ${{ inputs.version }}: ${STATUS}\"}"
```

## Docker Compose Canary Setup

```yaml
# docker-compose.canary.yml
services:
  nginx:
    image: nginx:1.27-alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx/canary.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      php-stable:
        condition: service_healthy
      php-canary:
        condition: service_healthy

  php-stable:
    image: ${REGISTRY}/app:${STABLE_VERSION}
    environment:
      APP_ENV: production
      APP_SLOT: stable
    deploy:
      replicas: 3
    healthcheck:
      test: ["CMD", "php-fpm-healthcheck"]
      interval: 10s
      timeout: 5s
      retries: 3

  php-canary:
    image: ${REGISTRY}/app:${CANARY_VERSION}
    environment:
      APP_ENV: production
      APP_SLOT: canary
    deploy:
      replicas: 1
    healthcheck:
      test: ["CMD", "php-fpm-healthcheck"]
      interval: 10s
      timeout: 5s
      retries: 3
```

## Detection Patterns

```bash
# Find canary deployment configurations
Grep: "canary|canary-weight|canary_backend|split_clients" --glob "*.conf" --glob "*.yml" --glob "*.yaml"

# Check for canary Kubernetes Ingress annotations
Grep: "canary.*true|canary-weight|canary-by-header" --glob "*.yaml" --glob "*.yml"

# Find Istio traffic splitting
Grep: "VirtualService|weight:|DestinationRule" --glob "*.yaml"

# Check for canary analysis scripts
Grep: "canary.analysis|canary.metrics|error_rate.*threshold" --glob "*.sh" --glob "*.yml"

# Find Prometheus canary queries
Grep: "slot.*canary|app_http_requests_total.*canary" --glob "*.yaml" --glob "*.yml"

# Check for canary rollback logic
Grep: "canary.*rollback|canary-weight.*0|scale.*canary.*0" --glob "*.sh" --glob "*.yml"
```

## Summary Table

| Phase | Traffic | Duration | Success Criteria |
|-------|---------|----------|------------------|
| **1. Deploy canary** | 0% (pods only) | 2-5 min | Pods healthy, readiness probe passes |
| **2. Initial canary** | 10% | 10 min | Error rate < 1%, p99 < 500ms, success > 99% |
| **3. Expand canary** | 25% | 30 min | Error rate < 1%, p99 < 500ms, no OOM kills |
| **4. Half traffic** | 50% | 1 hour | Error rate < 0.5%, p99 < 400ms, stable resource usage |
| **5. Pre-promote** | 75% | 30 min | All metrics within SLA, no anomalies |
| **6. Full promotion** | 100% | - | Update stable deployment, remove canary |
| **Rollback** | 0% canary | Instant | Set weight to 0, scale down canary pods |
| **Post-mortem** | - | - | Save canary logs, analyze failure cause |
