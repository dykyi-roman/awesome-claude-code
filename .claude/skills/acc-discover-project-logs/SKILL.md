---
name: acc-discover-project-logs
description: Discovers log files in PHP projects. Knows standard paths for Laravel, Symfony, CodeIgniter, Yii2/Yii3, PHP-FPM, Docker, CI/CD, web servers, and databases. Parses framework configs to extract custom log paths. Scores and prioritizes findings.
---

# Project Log Discovery

Discovers and prioritizes log files across PHP project ecosystems. Provides Glob/Grep patterns for auto-detection, parses framework configs for custom paths, and scores results by relevance.

## Discovery Strategy (3 Steps)

```
Step 1: Auto-discover — Glob/Grep by known framework paths
Step 2: Config-based — Parse framework config files for custom log paths
Step 3: Ask user — If nothing found, report back to coordinator for user interaction
```

**Important:** Specialist agents (bug-hunter, ci-debugger, etc.) do NOT have `AskUserQuestion` tool. If no logs found, the agent must report "No logs found automatically" back to the coordinator. The coordinator (command-level, opus model) handles user interaction via `AskUserQuestion`.

### Fallback AskUserQuestion Template (for coordinators)

```
Question: "Log files not found automatically. Where are your project logs?"
Options:
  - "storage/logs/" (Laravel)
  - "var/log/" (Symfony)
  - "writable/logs/" (CodeIgniter 4)
  - "runtime/logs/" (Yii2/Yii3)
  [+ Other for custom path]
```

## Framework Log Paths

### Laravel

```
Glob patterns:
  storage/logs/*.log
  storage/logs/laravel.log
  storage/logs/laravel-*.log

Config file: config/logging.php
Extract: 'path' => env('LOG_PATH', storage_path('logs/laravel.log'))
```

**Config parsing:**
```
Grep pattern: /'path'\s*=>\s*(.+)/
File: config/logging.php
Look for: channels → single/daily → path value
Also check: LOG_CHANNEL in .env for active channel
```

### Symfony

```
Glob patterns:
  var/log/*.log
  var/log/dev.log
  var/log/prod.log
  var/log/test.log

Config file: config/packages/monolog.yaml (or monolog.php)
Extract: path: '%kernel.logs_dir%/%kernel.environment%.log'
```

**Config parsing:**
```
Grep pattern: /path:\s*['"]?(.+?)['"]?$/
File: config/packages/monolog.yaml
Look for: handlers → main → path
Default: var/log/{environment}.log
```

### CodeIgniter

```
CI3:
  application/logs/*.log
  application/logs/log-*.php

CI4:
  writable/logs/*.log
  writable/logs/log-*.log

Config file (CI4): app/Config/Logger.php
Extract: public string $path = WRITEPATH . 'logs/'
```

**Config parsing:**
```
Grep pattern: /\$path\s*=\s*(.+);/
File: app/Config/Logger.php
Default: writable/logs/
```

### Yii2

```
Glob patterns:
  runtime/logs/*.log
  runtime/logs/app.log

Config file: config/web.php (or config/main.php)
Extract: 'log' component → targets → FileTarget → logFile
```

**Config parsing:**
```
Grep pattern: /'logFile'\s*=>\s*(.+)/
File: config/web.php, config/main.php, common/config/main.php
Look for: 'components' → 'log' → 'targets' → class FileTarget
Default: @runtime/logs/app.log
```

### Yii3

```
Glob patterns:
  runtime/logs/*.log
  runtime/logs/app.log

Config: di-config (config/common/di/logger.php or similar)
Extract: LogTarget configuration, FileRotator paths
```

**Config parsing:**
```
Grep pattern: /FileRotator|FileTarget|->logFile/
Files: config/common/di/*.php, config/params.php
Default: runtime/logs/
```

### Generic PHP

```
Glob patterns:
  logs/*.log
  log/*.log
  *.log (root only — limit to top-level, exclude vendor/)
  tmp/logs/*.log
  data/logs/*.log
```

## Infrastructure Log Paths

### PHP-FPM

```
Config detection:
  Grep: /slowlog\s*=\s*(.+)/ in /usr/local/etc/php-fpm.d/*.conf
  Grep: /error_log\s*=\s*(.+)/ in /usr/local/etc/php-fpm.d/*.conf
  Grep: /php_admin_value\[error_log\]/ in php-fpm pool configs

Common paths:
  /var/log/php-fpm/*.log
  /var/log/php-fpm/error.log
  /var/log/php-fpm/slow.log
  /var/log/php-fpm/www-error.log
  /var/log/php8.4-fpm.log
```

### Docker

```
Detection:
  # Running containers
  docker compose logs --tail=100 [service] 2>/dev/null
  docker logs --tail=100 [container] 2>/dev/null

  # Mounted log volumes
  Grep: /volumes:/ in docker-compose*.yml
  Look for: ./logs:/var/log or similar volume mounts

  # Inside containers
  /var/log/nginx/*.log
  /var/log/php-fpm/*.log
  /proc/1/fd/1 (stdout), /proc/1/fd/2 (stderr)
```

### CI/CD Build Artifacts

```
Glob patterns:
  build/logs/*.log
  build/logs/*.xml
  build/logs/clover.xml
  build/logs/junit.xml
  build/reports/*.xml
  build/reports/*.html
  var/phpstan/*.json
  .phpunit.result.cache

PHPUnit output:
  Grep: /outputFile|logfile/ in phpunit.xml*
  build/logs/phpunit.log
  build/logs/testdox.txt

PHPStan output:
  Grep: /reportUnmatchedIgnoredErrors|tmpDir/ in phpstan.neon*
```

### Web Server

```
Nginx:
  /var/log/nginx/access.log
  /var/log/nginx/error.log
  docker/nginx/logs/*.log

Apache:
  /var/log/apache2/error.log
  /var/log/httpd/error_log
```

### Database

```
MySQL slow query log:
  Grep: /slow_query_log_file/ in my.cnf, docker-compose*.yml
  /var/log/mysql/slow-query.log
  /var/lib/mysql/*-slow.log

PostgreSQL:
  Grep: /log_directory|logging_collector/ in postgresql.conf
  /var/log/postgresql/*.log
  pg_log/*.log
```

## Discovery Implementation

### Quick Scan (Glob-based)

Run these Glob patterns in order of priority:

```
# Priority 1: Framework logs (most likely useful)
storage/logs/*.log          # Laravel
var/log/*.log               # Symfony
writable/logs/*.log         # CodeIgniter 4
runtime/logs/*.log          # Yii2/Yii3
application/logs/*.log      # CodeIgniter 3

# Priority 2: Generic logs
logs/*.log
log/*.log

# Priority 3: Build/CI artifacts
build/logs/*
build/reports/*

# Priority 4: Infrastructure (if Docker context)
docker/*/logs/*
```

### Deep Scan (Config-based)

If quick scan finds nothing:

```
# Step 1: Detect framework
Grep: /laravel\/framework/ in composer.json → Laravel
Grep: /symfony\/framework-bundle/ in composer.json → Symfony
Grep: /codeigniter4\/framework/ in composer.json → CodeIgniter 4
Grep: /yiisoft\/yii2/ in composer.json → Yii2
Grep: /yiisoft\/yii-/ in composer.json → Yii3 (multiple yiisoft/* packages)

# Step 2: Parse framework config for log path
[Use framework-specific config parsing from above]

# Step 3: Check .env for log overrides
Grep: /LOG_CHANNEL|LOG_PATH|LOG_DIR|APP_LOG/ in .env, .env.example
```

## Scoring and Prioritization

Sort discovered logs by score (higher = more relevant):

| Factor | Score |
|--------|-------|
| Modified in last 1 hour | +50 |
| Modified in last 24 hours | +30 |
| Modified in last 7 days | +10 |
| Contains "error" or "exception" in name | +20 |
| Framework main log (laravel.log, dev.log) | +15 |
| Slow query / slow log | +15 |
| File size > 0 bytes | +10 |
| File size > 1MB (may have useful data) | +5 |
| Generic name (app.log) | +5 |

**Reading strategy for large files:**
- Files > 10KB: Read last 500 lines (`Read` tool with offset to end)
- Files > 1MB: Read last 1000 lines only
- Use Grep with timestamp/exception patterns for targeted extraction

## Output Format

```markdown
## Discovered Log Files

| # | Path | Framework | Type | Size | Modified | Score |
|---|------|-----------|------|------|----------|-------|
| 1 | storage/logs/laravel.log | Laravel | App | 245KB | 2 min ago | 95 |
| 2 | storage/logs/laravel-2025-01-15.log | Laravel | App (daily) | 1.2MB | 1 hour ago | 80 |
| 3 | var/log/nginx/error.log | - | Web server | 12KB | 5 min ago | 70 |
| 4 | build/logs/phpunit.log | - | CI/Test | 34KB | 2 days ago | 25 |

**Discovery method:** Auto-detect (Laravel detected via composer.json)
**Config path:** config/logging.php → channel: daily
**Recommended:** Start with #1 (highest score, most recent errors)
```

## Integration Notes

- This skill is **read-only** — it discovers and reports, never modifies
- Works with `Read`, `Grep`, `Glob` tools available to all agents
- For Docker container logs, `Bash` tool is needed (`docker compose logs`)
- Prioritize application logs over infrastructure logs for bug diagnosis
- Prioritize infrastructure logs for Docker/performance diagnosis
