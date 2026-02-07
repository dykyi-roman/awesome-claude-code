# Deployment Strategy Templates

## Blue-Green — GitLab CI

```yaml
# .gitlab-ci.yml - Blue-Green
stages:
  - build
  - deploy
  - switch
  - rollback

variables:
  REGISTRY: $CI_REGISTRY_IMAGE

build:
  stage: build
  image: docker:24
  services:
    - docker:24-dind
  script:
    - docker build -t $REGISTRY:$CI_COMMIT_SHA .
    - docker push $REGISTRY:$CI_COMMIT_SHA

.deploy_template: &deploy_template
  stage: deploy
  image: alpine:latest
  before_script:
    - apk add --no-cache curl openssh-client
  script:
    - |
      ssh deploy@$DEPLOY_HOST << EOF
        docker pull $REGISTRY:$CI_COMMIT_SHA
        docker-compose -f docker-compose.$TARGET_ENV.yml up -d
      EOF
    - |
      for i in $(seq 1 30); do
        curl -sf "https://$TARGET_ENV.example.com/health" && exit 0
        sleep 10
      done
      exit 1

deploy:blue:
  <<: *deploy_template
  variables:
    TARGET_ENV: blue
  rules:
    - if: $DEPLOY_TARGET == "blue"

deploy:green:
  <<: *deploy_template
  variables:
    TARGET_ENV: green
  rules:
    - if: $DEPLOY_TARGET == "green"

switch:traffic:
  stage: switch
  image: alpine:latest
  script:
    - |
      curl -X POST https://api.example.com/switch-traffic \
        -H "Authorization: Bearer $DEPLOY_TOKEN" \
        -d "{\"target\": \"$DEPLOY_TARGET\"}"
  when: manual
  needs: [deploy:blue, deploy:green]

rollback:
  stage: rollback
  image: alpine:latest
  script:
    - |
      curl -X POST https://api.example.com/rollback \
        -H "Authorization: Bearer $DEPLOY_TOKEN"
  when: manual
```

## Canary Deployment — GitHub Actions

```yaml
# .github/workflows/deploy-canary.yml
name: Canary Deploy

on:
  push:
    branches: [main]

jobs:
  deploy-canary:
    runs-on: ubuntu-latest
    environment: canary
    steps:
      - uses: actions/checkout@v4

      - name: Deploy canary (5%)
        id: canary
        run: |
          # Deploy to canary instances
          kubectl set image deployment/app app=$IMAGE --namespace=canary
          kubectl rollout status deployment/app --namespace=canary

      - name: Configure traffic split (5%)
        run: |
          kubectl apply -f - <<EOF
          apiVersion: split.smi-spec.io/v1alpha1
          kind: TrafficSplit
          metadata:
            name: app-canary
          spec:
            service: app
            backends:
            - service: app-stable
              weight: 95
            - service: app-canary
              weight: 5
          EOF

      - name: Monitor canary (10 minutes)
        id: monitor
        run: |
          END=$(($(date +%s) + 600))
          while [ $(date +%s) -lt $END ]; do
            ERROR_RATE=$(curl -s "http://prometheus:9090/api/v1/query?query=rate(http_requests_total{status=~'5..'}[1m])" | jq '.data.result[0].value[1]')
            if (( $(echo "$ERROR_RATE > 0.01" | bc -l) )); then
              echo "Error rate too high: $ERROR_RATE"
              echo "rollback=true" >> $GITHUB_OUTPUT
              exit 1
            fi
            sleep 30
          done
          echo "Canary healthy"

      - name: Promote canary (25%)
        if: success()
        run: |
          kubectl apply -f - <<EOF
          apiVersion: split.smi-spec.io/v1alpha1
          kind: TrafficSplit
          metadata:
            name: app-canary
          spec:
            service: app
            backends:
            - service: app-stable
              weight: 75
            - service: app-canary
              weight: 25
          EOF

      - name: Monitor promotion (15 minutes)
        run: |
          sleep 900
          # Additional monitoring...

      - name: Full rollout
        if: success()
        run: |
          kubectl set image deployment/app-stable app=$IMAGE
          kubectl delete trafficsplit app-canary

      - name: Rollback on failure
        if: failure()
        run: |
          kubectl rollout undo deployment/app --namespace=canary
          kubectl delete trafficsplit app-canary || true
```

## Canary Deployment — GitLab CI

```yaml
# .gitlab-ci.yml - Canary
stages:
  - build
  - canary
  - promote
  - rollback

canary:5:
  stage: canary
  script:
    - kubectl set image deployment/app-canary app=$IMAGE
    - kubectl rollout status deployment/app-canary
    - |
      kubectl patch service app -p '
        {"spec":{"selector":null}}
      '
    - |
      kubectl apply -f - <<EOF
      apiVersion: split.smi-spec.io/v1alpha1
      kind: TrafficSplit
      metadata:
        name: app-canary
      spec:
        service: app
        backends:
        - service: app-stable
          weight: 95
        - service: app-canary
          weight: 5
      EOF
  environment:
    name: canary
    on_stop: rollback:canary

monitor:canary:
  stage: canary
  needs: [canary:5]
  script:
    - sleep 600
    - |
      ERROR_RATE=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=rate(http_requests_total{status=~'5..'}[5m])" | jq -r '.data.result[0].value[1]')
      if (( $(echo "$ERROR_RATE > 0.01" | bc -l) )); then
        echo "Error rate too high"
        exit 1
      fi

promote:25:
  stage: promote
  needs: [monitor:canary]
  script:
    - |
      kubectl apply -f - <<EOF
      apiVersion: split.smi-spec.io/v1alpha1
      kind: TrafficSplit
      metadata:
        name: app-canary
      spec:
        service: app
        backends:
        - service: app-stable
          weight: 75
        - service: app-canary
          weight: 25
      EOF
  when: manual

promote:full:
  stage: promote
  needs: [promote:25]
  script:
    - kubectl set image deployment/app-stable app=$IMAGE
    - kubectl delete trafficsplit app-canary
  when: manual

rollback:canary:
  stage: rollback
  script:
    - kubectl rollout undo deployment/app-canary
    - kubectl delete trafficsplit app-canary || true
  when: manual
  environment:
    name: canary
    action: stop
```

## Rolling Deployment — Kubernetes

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
spec:
  replicas: 4
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: app
        image: myapp:latest
        ports:
        - containerPort: 8080
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8080
          initialDelaySeconds: 15
          periodSeconds: 20
```

## Rolling Deployment — Docker Swarm

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  app:
    image: myapp:${VERSION}
    deploy:
      replicas: 4
      update_config:
        parallelism: 1
        delay: 10s
        failure_action: rollback
        monitor: 30s
        max_failure_ratio: 0.1
      rollback_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
        max_attempts: 3
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```
