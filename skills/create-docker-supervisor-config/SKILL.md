---
name: acc-create-docker-supervisor-config
description: Generates Supervisor configuration for Docker PHP containers. Creates process management configs for workers, schedulers, and multi-process setups.
---

# Docker Supervisor Configuration Generator

Generates Supervisor configurations for managing multiple processes in PHP Docker containers.

## Generated Files

```
docker/supervisor/
  supervisord.conf            # Main Supervisor configuration
  conf.d/php-fpm.conf         # PHP-FPM program definition
  conf.d/worker.conf          # Queue worker program definition
  conf.d/scheduler.conf       # Scheduler program definition
```

## Main supervisord.conf

```ini
; supervisord.conf
[supervisord]
nodaemon=true
user=root
logfile=/var/log/supervisor/supervisord.log
logfile_maxbytes=10MB
logfile_backups=3
loglevel=info
pidfile=/var/run/supervisord.pid

[unix_http_server]
file=/var/run/supervisor.sock
chmod=0700

[rpcinterface:supervisor]
supervisor.rpcinterface_factory=supervisor.rpcinterface:make_main_rpcinterface

[supervisorctl]
serverurl=unix:///var/run/supervisor.sock

[include]
files=/etc/supervisor/conf.d/*.conf
```

## PHP-FPM Program

```ini
; conf.d/php-fpm.conf
[program:php-fpm]
command=php-fpm --nodaemonize
autostart=true
autorestart=true
priority=10
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
stopwaitsecs=30
stopsignal=QUIT
```

## Queue Worker Program (Multiple Instances)

```ini
; conf.d/worker.conf
; Runs multiple worker instances via numprocs
[program:worker]
process_name=%(program_name)s_%(process_num)02d
command=php bin/console messenger:consume async --memory-limit=128M --time-limit=3600 --limit=1000 -vv
numprocs=2
autostart=true
autorestart=true
priority=20
startsecs=5
startretries=3
stopwaitsecs=60
stopsignal=TERM
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
```

## Scheduler Program (Cron-like)

```ini
; conf.d/scheduler.conf
[program:scheduler]
command=/bin/bash -c "while true; do php bin/console app:scheduler:run >> /var/log/scheduler.log 2>&1; sleep 60; done"
autostart=true
autorestart=true
priority=30
startsecs=0
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
```

## Symfony Messenger Worker Configuration

```ini
; conf.d/messenger-worker.conf
; Symfony Messenger — multiple transports with different priorities

[program:messenger-async]
process_name=%(program_name)s_%(process_num)02d
command=php bin/console messenger:consume async --memory-limit=128M --time-limit=3600 -vv
numprocs=2
autostart=true
autorestart=true
priority=20
startsecs=5
startretries=3
stopwaitsecs=60
stopsignal=TERM
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0

[program:messenger-priority]
process_name=%(program_name)s_%(process_num)02d
command=php bin/console messenger:consume priority --memory-limit=256M --time-limit=3600 -vv
numprocs=1
autostart=true
autorestart=true
priority=15
startsecs=5
startretries=3
stopwaitsecs=120
stopsignal=TERM
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0

[program:messenger-failed-retry]
command=/bin/bash -c "while true; do php bin/console messenger:failed:retry --force --limit=10 2>&1; sleep 300; done"
autostart=true
autorestart=true
priority=25
startsecs=0
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
```

## Laravel Queue Worker Configuration

```ini
; conf.d/laravel-worker.conf

[program:laravel-worker]
process_name=%(program_name)s_%(process_num)02d
command=php artisan queue:work redis --queue=high,default,low --memory=128 --timeout=60 --tries=3 --max-jobs=1000 --max-time=3600 --sleep=3
numprocs=2
autostart=true
autorestart=true
priority=20
startsecs=5
startretries=3
stopwaitsecs=60
stopsignal=TERM
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0

[program:laravel-scheduler]
command=/bin/bash -c "while true; do php artisan schedule:run >> /dev/null 2>&1; sleep 60; done"
autostart=true
autorestart=true
priority=30
startsecs=0
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0

[program:laravel-horizon]
command=php artisan horizon
autostart=true
autorestart=true
priority=15
startsecs=10
stopwaitsecs=30
stopsignal=TERM
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
```

## Dockerfile Additions for Supervisor

```dockerfile
# ─── Supervisor Installation ────────────────────────────
# Alpine-based image
RUN apk add --no-cache supervisor

# Debian-based image
# RUN apt-get update && apt-get install -y supervisor && rm -rf /var/lib/apt/lists/*

# Create directories
RUN mkdir -p /var/log/supervisor /etc/supervisor/conf.d

# Copy Supervisor configuration
COPY docker/supervisor/supervisord.conf /etc/supervisor/supervisord.conf
COPY docker/supervisor/conf.d/ /etc/supervisor/conf.d/

# Start Supervisor as the main process
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]
```

## Docker Compose with Supervisor

```yaml
services:
  # All-in-one container: PHP-FPM + Worker + Scheduler
  app:
    build:
      context: .
      dockerfile: Dockerfile
    command: ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]
    volumes:
      - ./docker/supervisor/conf.d:/etc/supervisor/conf.d:ro
    environment:
      - APP_ENV=prod

  # Alternative: Separate containers (recommended for production)
  web:
    build: .
    command: ["php-fpm", "--nodaemonize"]

  worker:
    build: .
    command: ["php", "bin/console", "messenger:consume", "async", "--memory-limit=128M", "-vv"]
    deploy:
      replicas: 2

  scheduler:
    build: .
    command: ["/bin/bash", "-c", "while true; do php bin/console app:scheduler:run; sleep 60; done"]
```

## Process Group Management

```ini
; Group workers for batch control
[group:workers]
programs=messenger-async,messenger-priority
priority=20

; supervisorctl commands:
; supervisorctl start workers:*
; supervisorctl stop workers:*
; supervisorctl restart workers:*
; supervisorctl status
```

## Generation Instructions

1. **Identify processes needed:**
   - PHP-FPM (web requests)
   - Queue workers (Symfony Messenger / Laravel Queue)
   - Scheduler (cron replacement)
   - Custom daemons

2. **Choose deployment model:**
   - All-in-one (Supervisor manages all): simpler, good for small projects
   - Separate containers (one process each): recommended for production

3. **Generate configurations:**
   - Main supervisord.conf
   - Per-process conf.d/ files
   - Dockerfile additions

4. **Tune parameters:**
   - numprocs for worker concurrency
   - memory-limit and time-limit for workers
   - stopwaitsecs for graceful shutdown
   - startretries for resilience

## Usage

Provide:
- Framework (Symfony/Laravel)
- Processes to manage (web, workers, scheduler)
- Worker count and memory limits
- Deployment model (all-in-one or separate)

The generator will:
1. Create supervisord.conf with proper settings
2. Generate per-process configuration files
3. Add Dockerfile instructions for Supervisor
4. Configure logging to stdout/stderr for Docker
