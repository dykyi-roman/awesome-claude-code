---
name: acc-docker-scanning-knowledge
description: Docker image scanning knowledge base. Provides vulnerability detection, compliance checking, and SBOM generation for PHP container images.
---

# Docker Image Scanning Knowledge Base

Quick reference for vulnerability scanning and compliance checking in PHP container images.

## Scanning Tools Comparison

| Tool | Type | License | Strengths |
|------|------|---------|-----------|
| **Trivy** | CLI, CI, Operator | Apache 2.0 | OS + app deps, IaC, SBOM, fast |
| **Grype** | CLI, CI | Apache 2.0 | Fast, Syft integration, accurate |
| **Snyk** | CLI, CI, IDE, Web | Commercial | Deep analysis, fix suggestions |
| **Docker Scout** | CLI, Desktop | Commercial | Docker-native, real-time, policy |

## Trivy

### Basic Scanning

```bash
# Scan image for vulnerabilities
trivy image myapp:latest

# Scan with severity filter
trivy image --severity HIGH,CRITICAL myapp:latest

# Scan and fail on threshold (for CI)
trivy image --exit-code 1 --severity CRITICAL myapp:latest

# Scan with specific format
trivy image --format json --output results.json myapp:latest
trivy image --format table myapp:latest
trivy image --format sarif --output results.sarif myapp:latest
```

### Scanning Dockerfile

```bash
# Scan Dockerfile for misconfigurations
trivy config Dockerfile

# Scan entire project config
trivy config .
```

### SBOM Generation

```bash
# Generate SBOM in CycloneDX format
trivy image --format cyclonedx --output sbom.json myapp:latest

# Generate SBOM in SPDX format
trivy image --format spdx-json --output sbom.spdx.json myapp:latest
```

## Grype

### Basic Scanning

```bash
# Scan image
grype myapp:latest

# Fail on severity
grype myapp:latest --fail-on high

# Output as JSON
grype myapp:latest -o json > results.json

# Scan from SBOM
syft myapp:latest -o spdx-json > sbom.json
grype sbom:sbom.json
```

### Syft SBOM Generation

```bash
# Generate SBOM with Syft
syft myapp:latest -o cyclonedx-json > sbom.cyclonedx.json
syft myapp:latest -o spdx-json > sbom.spdx.json
syft myapp:latest -o table
```

## Docker Scout

```bash
# Analyze image vulnerabilities
docker scout cves myapp:latest

# Get fix recommendations
docker scout recommendations myapp:latest

# Compare two images
docker scout compare myapp:latest myapp:previous

# View SBOM
docker scout sbom myapp:latest
```

## CI Integration Patterns

### GitHub Actions

```yaml
name: Security Scan

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build image
        run: docker build -t myapp:${{ github.sha }} .

      - name: Trivy vulnerability scan
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: myapp:${{ github.sha }}
          format: sarif
          output: trivy-results.sarif
          severity: CRITICAL,HIGH
          exit-code: 1

      - name: Upload scan results
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: trivy-results.sarif

      - name: Generate SBOM
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: myapp:${{ github.sha }}
          format: cyclonedx
          output: sbom.json

      - name: Upload SBOM
        uses: actions/upload-artifact@v4
        with:
          name: sbom
          path: sbom.json
```

### GitLab CI

```yaml
container_scanning:
  stage: test
  image:
    name: aquasec/trivy:latest
    entrypoint: [""]
  variables:
    IMAGE: $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  script:
    - trivy image --exit-code 0 --format template --template "@/contrib/gitlab.tpl" --output gl-container-scanning-report.json $IMAGE
    - trivy image --exit-code 1 --severity CRITICAL $IMAGE
  artifacts:
    reports:
      container_scanning: gl-container-scanning-report.json
  allow_failure: false
```

## SBOM Formats

| Format | Standard | Use Case |
|--------|----------|----------|
| **CycloneDX** | OWASP | Security-focused, VEX support |
| **SPDX** | Linux Foundation | License compliance, legal |
| **Syft JSON** | Anchore | Tool-specific, detailed |

### PHP-Specific SBOM Content

An SBOM for a PHP container should include:

| Component | Source | Example |
|-----------|--------|---------|
| OS packages | Alpine apk / Debian apt | `libzip`, `icu-libs` |
| PHP extensions | `docker-php-ext-install` | `pdo_mysql`, `opcache` |
| Composer packages | `composer.lock` | `symfony/http-kernel` |
| Node packages | `package-lock.json` | Build-time only |
| Binary tools | Installed in Dockerfile | `composer`, `nginx` |

## Compliance Policies

### Severity Classification

| Severity | CVSS | Action | SLA |
|----------|------|--------|-----|
| **Critical** | 9.0-10.0 | Block deployment, fix immediately | 24 hours |
| **High** | 7.0-8.9 | Block deployment, prioritize fix | 7 days |
| **Medium** | 4.0-6.9 | Allow deployment, schedule fix | 30 days |
| **Low** | 0.1-3.9 | Allow deployment, backlog | 90 days |
| **Negligible** | 0.0 | Allow deployment, info only | N/A |

### Policy Configuration (Trivy)

```yaml
# .trivy.yaml
severity:
  - CRITICAL
  - HIGH

exit-code: 1

ignore-unfixed: true

ignorefile: .trivyignore
```

```
# .trivyignore
# Accepted risks with justification
CVE-2023-XXXXX  # Mitigated by WAF rules, not exploitable in our context
CVE-2023-YYYYY  # Fix not available, monitoring for update
```

## Fix Strategies

| Strategy | When | Example |
|----------|------|---------|
| **Upgrade base image** | OS-level CVE | `FROM php:8.4-fpm-alpine3.20` |
| **Update PHP version** | PHP CVE | `FROM php:8.4.3-fpm-alpine` |
| **Update Composer deps** | Library CVE | `composer update --with-dependencies` |
| **Pin fixed version** | Specific package | `apk add libcurl=8.5.0-r0` |
| **Remove package** | Unnecessary dep | Remove from Dockerfile |
| **Accept risk** | No fix available | Document in `.trivyignore` |

## Automated Scanning Workflow

```
+---------------------------------------------------------------------------+
|                    SCANNING WORKFLOW                                        |
+---------------------------------------------------------------------------+
|                                                                            |
|   Developer Push                                                           |
|       |                                                                    |
|       v                                                                    |
|   Build Image --> Scan Image --> Generate SBOM --> Policy Check             |
|       |               |               |               |                    |
|       |          +----+----+          |          +----+----+               |
|       |          | Pass    | Fail     |          | Pass    | Fail          |
|       |          v         v          |          v         v               |
|       |       Continue   Block PR     |       Deploy    Block Deploy       |
|       |          |                    |          |                          |
|       v          v                    v          v                          |
|   Push to    Merge to            Store SBOM   Production                   |
|   Registry   Main Branch         in Registry  Monitoring                   |
|                                                                            |
+---------------------------------------------------------------------------+
```

## Detection Patterns

```bash
# Find scanning configurations
Glob: **/.trivy.yaml
Glob: **/.trivyignore
Glob: **/.grype.yaml
Glob: **/.snyk

# Check CI for scanning steps
Grep: "trivy|grype|snyk|docker scout" --glob "**/.github/workflows/*.yml"
Grep: "container_scanning|security_scan" --glob "**/.gitlab-ci.yml"

# Find SBOM artifacts
Glob: **/sbom*.json
Glob: **/*.spdx.json
Glob: **/*.cyclonedx.json
```
