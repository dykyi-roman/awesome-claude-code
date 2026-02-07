---
name: acc-docker-orchestration-knowledge
description: Docker orchestration knowledge base. Provides patterns for Swarm, Kubernetes basics, service scaling, and load balancing for PHP.
---

# Docker Orchestration Knowledge Base

Quick reference for container orchestration patterns with PHP applications.

## Docker Swarm

### Core Concepts

```
+---------------------------------------------------------------------------+
|                       DOCKER SWARM ARCHITECTURE                            |
+---------------------------------------------------------------------------+
|                                                                            |
|   Manager Nodes (Raft consensus)                                           |
|   +--------------------------------------------------------------------+  |
|   | Schedule tasks | Maintain state | Serve API | Manage secrets       |  |
|   +--------------------------------------------------------------------+  |
|            |                    |                    |                      |
|            v                    v                    v                      |
|   Worker Nodes                                                             |
|   +----------------+  +----------------+  +----------------+              |
|   | Task: php (1)  |  | Task: php (2)  |  | Task: php (3)  |              |
|   | Task: nginx(1) |  | Task: nginx(2) |  | Task: worker(1)|              |
|   +----------------+  +----------------+  +----------------+              |
|                                                                            |
|   Overlay Network (encrypted)                                              |
|   +--------------------------------------------------------------------+  |
|   | Service discovery | Load balancing | DNS resolution                |  |
|   +--------------------------------------------------------------------+  |
|                                                                            |
+---------------------------------------------------------------------------+
```

### Stack Deployment

```yaml
# docker-stack.yml
version: "3.8"

services:
  nginx:
    image: myregistry/nginx:latest
    ports:
      - "80:80"
      - "443:443"
    deploy:
      replicas: 2
      placement:
        constraints:
          - node.role == worker
      update_config:
        parallelism: 1
        delay: 10s
    networks:
      - frontend
      - backend

  php:
    image: myregistry/php-app:latest
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
      update_config:
        parallelism: 1
        delay: 15s
        order: start-first
        failure_action: rollback
    secrets:
      - db_password
      - app_key
    networks:
      - backend

  postgres:
    image: postgres:16-alpine
    deploy:
      replicas: 1
      placement:
        constraints:
          - node.labels.storage == ssd
    volumes:
      - db-data:/var/lib/postgresql/data
    networks:
      - backend

networks:
  frontend:
    driver: overlay
  backend:
    driver: overlay
    internal: true

volumes:
  db-data:
    driver: local

secrets:
  db_password:
    external: true
  app_key:
    external: true
```

```bash
# Deploy stack
docker stack deploy -c docker-stack.yml myapp

# Scale service
docker service scale myapp_php=5

# Update service image
docker service update --image myregistry/php-app:v2 myapp_php

# Rollback service
docker service rollback myapp_php
```

## Kubernetes Overview

### PHP Application Resources

```
+---------------------------------------------------------------------------+
|                    KUBERNETES RESOURCES FOR PHP                             |
+---------------------------------------------------------------------------+
|                                                                            |
|   Ingress  -->  Service  -->  Deployment  -->  Pod                         |
|   (L7 LB)      (L4 LB)      (Replicas)       (Container)                  |
|                                                                            |
|   ConfigMap     Secret       HPA              PDB                          |
|   (php.ini)     (db creds)   (Auto-scale)     (Disruption budget)          |
|                                                                            |
+---------------------------------------------------------------------------+
```

### Deployment Manifest

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: php-app
  labels:
    app: php-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: php-app
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: php-app
    spec:
      containers:
        - name: php-fpm
          image: myregistry/php-app:latest
          ports:
            - containerPort: 9000
          resources:
            requests:
              cpu: "250m"
              memory: "256Mi"
            limits:
              cpu: "1000m"
              memory: "512Mi"
          livenessProbe:
            exec:
              command: ["php-fpm-healthcheck"]
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            exec:
              command: ["php-fpm-healthcheck"]
            initialDelaySeconds: 5
            periodSeconds: 5
          envFrom:
            - configMapRef:
                name: php-config
          volumeMounts:
            - name: php-ini
              mountPath: /usr/local/etc/php/conf.d/custom.ini
              subPath: custom.ini
      volumes:
        - name: php-ini
          configMap:
            name: php-ini-config
```

### Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: php-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: php-app
  minReplicas: 3
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
```

## Scaling PHP-FPM

### Horizontal Scaling

| Factor | Consideration |
|--------|--------------|
| **Replicas** | Start with 3, scale based on CPU/memory metrics |
| **Stateless** | No local sessions, use Redis/Memcached |
| **Shared storage** | Use object storage (S3) for uploads |
| **Database** | Connection pooling, read replicas |
| **Cache** | Centralized Redis, not per-container |

### FPM Pool Tuning Per Container

```ini
; For containers with 512MB memory limit
pm = dynamic
pm.max_children = 15
pm.start_servers = 5
pm.min_spare_servers = 3
pm.max_spare_servers = 10
pm.max_requests = 1000
```

Formula: `max_children = (container_memory - overhead) / avg_process_memory`

## Load Balancing Patterns

| Pattern | Layer | Tool | Use Case |
|---------|-------|------|----------|
| **Round Robin** | L4/L7 | Nginx, HAProxy | Default, equal distribution |
| **Least Connections** | L4 | Nginx, HAProxy | Varying request durations |
| **IP Hash** | L7 | Nginx | Sticky sessions (avoid if possible) |
| **Weighted** | L4/L7 | Nginx, HAProxy | Mixed capacity nodes |

### Nginx Load Balancer

```nginx
upstream php-app {
    least_conn;
    server php-1:9000 weight=3;
    server php-2:9000 weight=3;
    server php-3:9000 weight=1 backup;
    keepalive 32;
}
```

## Service Discovery

| Platform | Mechanism | DNS |
|----------|-----------|-----|
| **Docker Compose** | Built-in DNS | Service name resolves to container IP |
| **Docker Swarm** | VIP + DNS RR | Service name resolves to virtual IP |
| **Kubernetes** | ClusterIP Service | `service.namespace.svc.cluster.local` |

## Rolling Updates

### Zero-Downtime Deployment Checklist

- [ ] Health checks configured (liveness + readiness)
- [ ] Graceful shutdown handling (SIGTERM/SIGQUIT)
- [ ] `order: start-first` (start new before stopping old)
- [ ] Connection draining period (stop_grace_period)
- [ ] Database migrations run before deployment
- [ ] Backward-compatible API changes
- [ ] Session persistence via external store

### Blue-Green with Docker

```bash
# Deploy green alongside blue
docker compose -f docker-compose.green.yml up -d

# Run health checks on green
curl -f http://green.internal/health

# Switch traffic (update nginx upstream)
docker exec nginx nginx -s reload

# Remove blue after verification
docker compose -f docker-compose.blue.yml down
```

## Config and Secret Management

| Platform | Config | Secrets |
|----------|--------|---------|
| **Compose** | `.env` files, environment | `secrets:` (file-based) |
| **Swarm** | `docker config` | `docker secret` (encrypted Raft) |
| **Kubernetes** | `ConfigMap` | `Secret` (base64, use sealed-secrets) |

## Detection Patterns

```bash
# Find orchestration configurations
Glob: **/docker-stack*.yml
Glob: **/k8s/**/*.yaml
Glob: **/kubernetes/**/*.yaml

# Check for scaling readiness
Grep: "replicas|maxReplicas|scale" --glob "**/*.yml" --glob "**/*.yaml"
Grep: "session.save_handler.*redis" --glob "**/php*.ini"
Grep: "healthcheck|livenessProbe|readinessProbe" --glob "**/*.yml" --glob "**/*.yaml"
```
