---
name: acc-create-deploy-strategy
description: Generates deployment strategy configurations. Creates blue-green, canary, rolling deployment configs for GitHub Actions and GitLab CI with health checks and rollback procedures.
---

# Deployment Strategy Generator

Generates deployment configurations for zero-downtime deployments.

## Blue-Green Deployment

### GitHub Actions

```yaml
# .github/workflows/deploy-blue-green.yml
name: Blue-Green Deploy

on:
  push:
    tags: ['v*']
  workflow_dispatch:
    inputs:
      environment:
        description: 'Target environment'
        required: true
        type: choice
        options: [staging, production]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      image_tag: ${{ steps.meta.outputs.tags }}
    steps:
      - uses: actions/checkout@v4

      - name: Build and push image
        uses: docker/build-push-action@v5
        with:
          push: true
          tags: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: ${{ github.event.inputs.environment || 'production' }}
      url: ${{ steps.deploy.outputs.url }}
    steps:
      - uses: actions/checkout@v4

      - name: Determine target environment
        id: env
        run: |
          ACTIVE=$(curl -s https://api.example.com/active-env)
          if [ "$ACTIVE" = "blue" ]; then
            echo "target=green" >> $GITHUB_OUTPUT
            echo "url=https://green.example.com" >> $GITHUB_OUTPUT
          else
            echo "target=blue" >> $GITHUB_OUTPUT
            echo "url=https://blue.example.com" >> $GITHUB_OUTPUT
          fi

      - name: Deploy to inactive environment
        id: deploy
        env:
          TARGET: ${{ steps.env.outputs.target }}
          IMAGE: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
        run: |
          # Deploy to target environment
          ssh deploy@${{ secrets.DEPLOY_HOST }} << EOF
            docker pull $IMAGE
            docker-compose -f docker-compose.$TARGET.yml up -d
          EOF
          echo "url=${{ steps.env.outputs.url }}" >> $GITHUB_OUTPUT

      - name: Health check
        run: |
          for i in {1..30}; do
            if curl -sf "${{ steps.env.outputs.url }}/health"; then
              echo "Health check passed"
              exit 0
            fi
            sleep 10
          done
          echo "Health check failed"
          exit 1

      - name: Run smoke tests
        run: |
          npm run test:smoke -- --base-url="${{ steps.env.outputs.url }}"

      - name: Switch traffic
        if: success()
        run: |
          curl -X POST https://api.example.com/switch-traffic \
            -H "Authorization: Bearer ${{ secrets.DEPLOY_TOKEN }}" \
            -d '{"target": "${{ steps.env.outputs.target }}"}'

      - name: Rollback on failure
        if: failure()
        run: |
          echo "Deployment failed, keeping traffic on current environment"
          curl -X POST https://api.example.com/rollback \
            -H "Authorization: Bearer ${{ secrets.DEPLOY_TOKEN }}"
```

See `references/templates.md` for: Blue-Green GitLab CI, Canary GitHub Actions, Canary GitLab CI, Rolling Kubernetes, Rolling Docker Swarm configurations.

## Health Check Endpoints

```php
<?php
// src/Api/Action/HealthAction.php

declare(strict_types=1);

namespace App\Api\Action;

use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;

final readonly class HealthAction
{
    public function __construct(
        private DatabaseHealthChecker $database,
        private CacheHealthChecker $cache,
        private QueueHealthChecker $queue,
    ) {}

    public function ready(ServerRequestInterface $request): ResponseInterface
    {
        $checks = [
            'database' => $this->database->check(),
            'cache' => $this->cache->check(),
            'queue' => $this->queue->check(),
        ];

        $healthy = !in_array(false, $checks, true);

        return new JsonResponse(
            [
                'status' => $healthy ? 'healthy' : 'unhealthy',
                'checks' => $checks,
                'timestamp' => (new DateTimeImmutable())->format('c'),
            ],
            $healthy ? 200 : 503
        );
    }

    public function live(ServerRequestInterface $request): ResponseInterface
    {
        return new JsonResponse([
            'status' => 'alive',
            'timestamp' => (new DateTimeImmutable())->format('c'),
        ]);
    }
}
```

## Generation Instructions

1. **Identify deployment target:**
   - Kubernetes / Docker Swarm / VMs
   - Cloud provider (AWS, GCP, Azure)
   - CI platform (GitHub, GitLab)

2. **Select strategy:**
   - Blue-Green: Instant switch, 2x resources
   - Canary: Gradual rollout, metrics-based
   - Rolling: Gradual replace, minimal resources

3. **Configure health checks:**
   - Readiness probe (can accept traffic)
   - Liveness probe (is alive)
   - Startup probe (is ready to be probed)

4. **Set up monitoring:**
   - Error rate thresholds
   - Latency thresholds
   - Custom metrics

5. **Define rollback triggers:**
   - Automatic on health check failure
   - Manual option always available

## Usage

Provide:
- Deployment target (K8s, Swarm, VMs)
- Strategy (blue-green, canary, rolling)
- CI platform (GitHub, GitLab)
- Health check endpoints
- Rollback criteria

The generator will:
1. Create deployment workflow
2. Configure health checks
3. Set up traffic management
4. Add monitoring hooks
5. Implement rollback procedures
