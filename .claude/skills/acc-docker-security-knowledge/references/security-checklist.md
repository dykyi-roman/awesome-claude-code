# Docker Security Checklist

Comprehensive security checklist for PHP Docker deployments organized by category.

## Build Security

- [ ] Use multi-stage builds to minimize final image size
- [ ] Pin base image versions with SHA256 digest or specific tags
- [ ] Use official or verified publisher images only
- [ ] Enable BuildKit (`DOCKER_BUILDKIT=1`)
- [ ] Use `--mount=type=secret` for build-time secrets
- [ ] Never use `ARG` or `ENV` for sensitive data in Dockerfile
- [ ] Remove build tools and dev dependencies from production stage
- [ ] Verify `composer.lock` integrity before install
- [ ] Use `.dockerignore` to exclude sensitive files (`.env`, `.git`, tests)
- [ ] Minimize RUN layers and clean package manager caches
- [ ] Do not install unnecessary packages (`--no-install-recommends`)
- [ ] Use `COPY` instead of `ADD` (unless extracting archives)

## Image Security

- [ ] Scan images for vulnerabilities before deployment (Trivy, Grype)
- [ ] Set maximum vulnerability severity threshold (fail on CRITICAL)
- [ ] Generate and store SBOM for each release
- [ ] Sign images with Docker Content Trust or cosign
- [ ] Use minimal base images (Alpine preferred)
- [ ] Remove shells and package managers from production images when possible
- [ ] Ensure no secrets or credentials exist in any image layer
- [ ] Audit image history (`docker history`) before publishing
- [ ] Set image labels with maintainer and version metadata
- [ ] Use private registry with access controls

## Runtime Security

- [ ] Run containers as non-root user (`USER` directive)
- [ ] Drop all capabilities (`cap_drop: ALL`)
- [ ] Add only required capabilities explicitly
- [ ] Enable `no-new-privileges` security option
- [ ] Use read-only root filesystem (`read_only: true`)
- [ ] Mount tmpfs for writable directories (`/tmp`, `/var/run`)
- [ ] Set memory and CPU limits for all containers
- [ ] Configure restart policies (`unless-stopped` or `on-failure`)
- [ ] Set appropriate `ulimits` (nofile, nproc)
- [ ] Disable privileged mode (`privileged: false`)
- [ ] Use seccomp profiles (default or custom)
- [ ] Set PID limits to prevent fork bombs

## Network Security

- [ ] Segment networks (frontend, backend, database)
- [ ] Use internal networks for backend services
- [ ] Never use `network_mode: host` in production
- [ ] Expose only necessary ports
- [ ] Use TLS/SSL for all inter-service communication
- [ ] Configure DNS resolution to internal only
- [ ] Implement network policies for Kubernetes deployments
- [ ] Use reverse proxy (nginx) for external traffic
- [ ] Disable inter-container communication where not needed (`icc=false`)
- [ ] Monitor network traffic for anomalies

## Secrets Management

- [ ] Use Docker secrets or external vault (HashiCorp Vault, AWS Secrets Manager)
- [ ] Never store secrets in environment variables in Dockerfile
- [ ] Rotate secrets on a regular schedule
- [ ] Use different secrets for each environment (dev, staging, prod)
- [ ] Encrypt secrets at rest
- [ ] Limit secret access to services that need them
- [ ] Audit secret access regularly
- [ ] Use build secrets (`--mount=type=secret`) for build-time credentials
- [ ] Remove `.env` files from images via `.dockerignore`

## Supply Chain Security

- [ ] Use only trusted and verified base images
- [ ] Lock dependency versions (composer.lock, package-lock.json)
- [ ] Verify checksums for downloaded binaries in Dockerfile
- [ ] Scan third-party dependencies for known vulnerabilities
- [ ] Monitor for new CVEs in base images and dependencies
- [ ] Automate image rebuilds when base image is updated
- [ ] Use private mirrors for package repositories
- [ ] Implement image admission policies in orchestration platform
- [ ] Review and audit Dockerfile changes in code review

## Monitoring and Logging

- [ ] Enable centralized logging (stdout/stderr to log aggregator)
- [ ] Never log sensitive data (passwords, tokens, PII)
- [ ] Monitor container resource usage (CPU, memory, disk)
- [ ] Set up alerts for abnormal container behavior
- [ ] Audit container events (start, stop, exec, attach)
- [ ] Enable Docker daemon audit logging
- [ ] Monitor for unauthorized image pulls or pushes
- [ ] Track container drift from base image

## PHP-Specific Security

- [ ] Disable `expose_php` in php.ini
- [ ] Set `display_errors=Off` in production
- [ ] Configure `open_basedir` restriction
- [ ] Disable dangerous functions (`exec`, `system`, `passthru`, etc.)
- [ ] Set `session.cookie_secure=1` and `session.cookie_httponly=1`
- [ ] Enable OPcache with `validate_timestamps=0` in production
- [ ] Use `--no-dev` flag for Composer in production
- [ ] Remove Xdebug and other debug tools from production images
