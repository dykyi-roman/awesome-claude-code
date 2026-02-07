---
name: acc-create-docker-healthcheck
description: Generates Docker health check scripts for PHP services. Creates PHP-FPM, Nginx, and custom endpoint health checks.
---

# Docker Health Check Generator

Generates health check scripts and configurations for PHP Docker containers.

## Generated Files

```
docker/healthcheck/
  php-fpm-healthcheck.sh    # PHP-FPM process health check
  http-healthcheck.sh       # HTTP endpoint health check
  combined-healthcheck.sh   # Combined multi-service check
```

## PHP-FPM Health Check (cgi-fcgi based)

```bash
#!/bin/bash
# php-fpm-healthcheck.sh
# Checks PHP-FPM status via /ping endpoint using cgi-fcgi
set -eo pipefail

FCGI_CONNECT="${FCGI_CONNECT:-localhost:9000}"
FCGI_STATUS_PATH="${FCGI_STATUS_PATH:-/ping}"
EXPECTED_RESPONSE="${EXPECTED_RESPONSE:-pong}"

if ! command -v cgi-fcgi &> /dev/null; then
    echo "ERROR: cgi-fcgi not found. Install libfcgi-bin."
    exit 1
fi

RESPONSE=$(SCRIPT_NAME="${FCGI_STATUS_PATH}" \
    SCRIPT_FILENAME="${FCGI_STATUS_PATH}" \
    REQUEST_METHOD=GET \
    cgi-fcgi -bind -connect "${FCGI_CONNECT}" 2>/dev/null)

if echo "${RESPONSE}" | grep -q "${EXPECTED_RESPONSE}"; then
    echo "OK: PHP-FPM is healthy"
    exit 0
else
    echo "FAIL: PHP-FPM returned unexpected response"
    exit 1
fi
```

### PHP-FPM Pool Configuration (required)

```ini
; /usr/local/etc/php-fpm.d/www.conf
; Enable ping/status endpoints
pm.status_path = /status
ping.path = /ping
ping.response = pong
```

## HTTP Endpoint Health Check (curl-based)

```bash
#!/bin/bash
# http-healthcheck.sh
# Checks application health via HTTP /health endpoint
set -eo pipefail

HEALTH_URL="${HEALTH_URL:-http://localhost:80/health}"
TIMEOUT="${HEALTH_TIMEOUT:-5}"
EXPECTED_STATUS="${EXPECTED_STATUS:-200}"

RESPONSE_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    --max-time "${TIMEOUT}" \
    --fail \
    "${HEALTH_URL}" 2>/dev/null) || true

if [ "${RESPONSE_CODE}" = "${EXPECTED_STATUS}" ]; then
    echo "OK: HTTP health check passed (${RESPONSE_CODE})"
    exit 0
else
    echo "FAIL: HTTP health check returned ${RESPONSE_CODE}, expected ${EXPECTED_STATUS}"
    exit 1
fi
```

## Combined Health Check Script

```bash
#!/bin/bash
# combined-healthcheck.sh
# Checks PHP-FPM process + custom application logic
set -eo pipefail

FCGI_CONNECT="${FCGI_CONNECT:-localhost:9000}"
HEALTH_URL="${HEALTH_URL:-http://localhost:80/health}"

# Check 1: PHP-FPM process is running
if ! pgrep -x "php-fpm" > /dev/null 2>&1; then
    echo "FAIL: PHP-FPM process not running"
    exit 1
fi

# Check 2: PHP-FPM responds to ping
PING_RESPONSE=$(SCRIPT_NAME=/ping \
    SCRIPT_FILENAME=/ping \
    REQUEST_METHOD=GET \
    cgi-fcgi -bind -connect "${FCGI_CONNECT}" 2>/dev/null || true)

if ! echo "${PING_RESPONSE}" | grep -q "pong"; then
    echo "FAIL: PHP-FPM not responding to ping"
    exit 1
fi

# Check 3: Application health endpoint
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    --max-time 5 "${HEALTH_URL}" 2>/dev/null || true)

if [ "${HTTP_CODE}" != "200" ]; then
    echo "FAIL: Application health endpoint returned ${HTTP_CODE}"
    exit 1
fi

echo "OK: All health checks passed"
exit 0
```

## Dockerfile HEALTHCHECK Instruction

```dockerfile
# Simple PHP-FPM health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD ["php-fpm-healthcheck"] || exit 1

# HTTP endpoint health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:80/health || exit 1

# Combined health check (copy script into image)
COPY docker/healthcheck/combined-healthcheck.sh /usr/local/bin/healthcheck
RUN chmod +x /usr/local/bin/healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["/usr/local/bin/healthcheck"]
```

## Docker Compose Health Check Format

```yaml
# docker-compose.yml
services:
  php-fpm:
    build: .
    healthcheck:
      test: ["CMD", "/usr/local/bin/healthcheck"]
      interval: 30s
      timeout: 5s
      start_period: 20s
      retries: 3

  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: "${DB_PASSWORD}"
      MYSQL_DATABASE: "${DB_NAME}"
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-u", "root", "-p${DB_PASSWORD}"]
      interval: 10s
      timeout: 5s
      start_period: 30s
      retries: 5

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: "${DB_NAME}"
      POSTGRES_USER: "${DB_USER}"
      POSTGRES_PASSWORD: "${DB_PASSWORD}"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER} -d ${DB_NAME}"]
      interval: 10s
      timeout: 5s
      start_period: 30s
      retries: 5

  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      start_period: 5s
      retries: 3

  rabbitmq:
    image: rabbitmq:3-management-alpine
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "-q", "check_running"]
      interval: 15s
      timeout: 10s
      start_period: 30s
      retries: 5
```

## Dependency Wait Pattern

```yaml
# docker-compose.yml — services wait for healthy dependencies
services:
  php-fpm:
    depends_on:
      mysql:
        condition: service_healthy
      redis:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy
```

## Generation Instructions

1. **Analyze project stack:**
   - Identify PHP-FPM version
   - Check for Nginx reverse proxy
   - List dependent services (MySQL, PostgreSQL, Redis, RabbitMQ)

2. **Generate health check scripts:**
   - PHP-FPM ping check for all setups
   - HTTP endpoint check if application exposes /health
   - Combined check for production deployments

3. **Configure Dockerfile:**
   - Add HEALTHCHECK instruction
   - Copy health check scripts
   - Set proper permissions (chmod +x)

4. **Configure docker-compose:**
   - Add healthcheck blocks for each service
   - Use `depends_on` with `condition: service_healthy`
   - Tune intervals for each service type

## Usage

Provide:
- Services in the stack (PHP-FPM, MySQL, Redis, etc.)
- Health endpoint URL (if application provides one)
- Desired check intervals and thresholds
- Deployment target (development/production)

The generator will:
1. Create appropriate health check scripts
2. Add Dockerfile HEALTHCHECK instructions
3. Configure docker-compose healthcheck blocks
4. Set up dependency ordering with health conditions
