# PHP Docker Image Variants Comparison

Detailed comparison of all official PHP Docker image variants for informed selection.

## Full Comparison Matrix

| Variant | Base OS | Approx Size | PHP SAPI | Web Server | Best For |
|---------|---------|-------------|----------|------------|----------|
| `php:8.4-fpm` | Debian Bookworm | ~480MB | FPM | None (pair with Nginx) | Production web apps |
| `php:8.4-fpm-alpine` | Alpine 3.20 | ~80MB | FPM | None (pair with Nginx) | Size-optimized production |
| `php:8.4-cli` | Debian Bookworm | ~450MB | CLI | None | Workers, cron, scripts |
| `php:8.4-cli-alpine` | Alpine 3.20 | ~50MB | CLI | None | Lightweight CLI tasks |
| `php:8.4-apache` | Debian Bookworm | ~500MB | Apache module | Apache 2.4 | Simple deployments |
| `php:8.4-zts` | Debian Bookworm | ~460MB | CLI (ZTS) | None | Parallel processing |
| `php:8.4-zts-alpine` | Alpine 3.20 | ~85MB | CLI (ZTS) | None | Parallel + small image |
| `php:8.4-fpm-bookworm` | Debian Bookworm | ~480MB | FPM | None | Explicit Debian version |
| `php:8.4-fpm-bullseye` | Debian Bullseye | ~470MB | FPM | None | Legacy Debian compat |

## Detailed Pros and Cons

### php:8.4-fpm (Debian)

**Pros:**
- Full glibc compatibility — all PHP extensions work without issues
- Comprehensive debugging tools available (strace, gdb, ldd)
- Locale and multibyte string support works out of the box
- gRPC, protobuf, and other native extensions compile cleanly
- Largest community support and documentation

**Cons:**
- Large image size (~480MB uncompressed)
- More CVEs reported (due to more installed packages)
- Slower pull times in CI/CD

**Use when:** Full compatibility required, enterprise environments, gRPC usage.

### php:8.4-fpm-alpine

**Pros:**
- Small image size (~80MB uncompressed, ~30MB compressed)
- Fewer CVEs reported due to minimal package set
- Fast pull times, lower registry storage costs
- Quick container startup

**Cons:**
- musl libc may cause subtle issues (DNS, iconv, locale)
- Some PECL extensions need additional patches
- Limited debugging tools
- GNU libiconv workaround needed for some charsets

**Use when:** Standard PHP apps, microservices, Kubernetes environments.

### php:8.4-cli / php:8.4-cli-alpine

**Pros:**
- No FPM overhead — lighter for non-web workloads
- Ideal for queue consumers, cron jobs, CLI tools
- Can serve as build stage base for multi-stage builds

**Cons:**
- No built-in process manager (must use supervisord or similar for workers)
- Not suitable for direct web serving

**Use when:** Queue workers, scheduled tasks, artisan commands, build stages.

### php:8.4-apache

**Pros:**
- All-in-one: Apache + PHP in a single container
- Simplest setup — no separate web server needed
- `.htaccess` support out of the box
- Good for legacy apps migrating to Docker

**Cons:**
- Larger image size (~500MB)
- Apache is heavier than Nginx for static content
- Less flexible than FPM + Nginx separation
- Harder to scale web and PHP independently

**Use when:** Simple deployments, legacy migration, development environments.

### php:8.4-zts / php:8.4-zts-alpine

**Pros:**
- Thread-safe build — required for `parallel` extension
- Enables true multi-threading in PHP
- Good for CPU-bound parallel workloads

**Cons:**
- Slight performance overhead from thread safety mechanisms
- Not all extensions are thread-safe
- Smaller ecosystem of tested configurations

**Use when:** Parallel processing, multi-threaded PHP workers.

## Size Comparison Summary

```
php:8.4-apache          ████████████████████████████████████████████████████  ~500MB
php:8.4-fpm             ███████████████████████████████████████████████████   ~480MB
php:8.4-zts             ██████████████████████████████████████████████████    ~460MB
php:8.4-cli             █████████████████████████████████████████████████     ~450MB
php:8.4-zts-alpine      ████████                                              ~85MB
php:8.4-fpm-alpine      ███████                                               ~80MB
php:8.4-cli-alpine      █████                                                 ~50MB
```

## Recommended Combinations

| Environment | Image | Reason |
|-------------|-------|--------|
| Production (Kubernetes) | `php:8.4-fpm-alpine` | Small footprint, horizontal scaling |
| Production (VM/bare metal) | `php:8.4-fpm` | Full compatibility, fewer edge cases |
| Development | `php:8.4-fpm` or `php:8.4-fpm-alpine` | Match production base |
| CI/CD build stage | `php:8.4-cli-alpine` | Fast pulls, test execution |
| Queue workers | `php:8.4-cli-alpine` | Minimal overhead for background jobs |
| Legacy migration | `php:8.4-apache` | Simplest path from traditional hosting |
| Data processing | `php:8.4-zts-alpine` | Parallel extension support |
