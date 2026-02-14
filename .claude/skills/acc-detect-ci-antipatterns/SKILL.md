---
name: acc-detect-ci-antipatterns
description: Detects CI/CD antipatterns in pipeline configurations. Identifies slow pipelines, security issues, maintenance problems, and provides remediation guidance.
---

# CI Antipattern Detector

Detects common CI/CD antipatterns and provides remediation guidance.

## When to Use

- Reviewing GitHub Actions workflow files
- Auditing CI pipeline performance (slow builds)
- Checking CI security configuration
- Reducing pipeline maintenance burden
- Improving build reliability

## Analysis Approach

1. Parse CI configuration files (`.github/workflows/*.yml`)
2. Apply detection rules by category (Performance, Security, Maintenance, Reliability)
3. Calculate impact per antipattern (time cost, risk level)
4. Generate prioritized fix recommendations

## Detection Rules

| ID | Antipattern | Detection | Category |
|----|-------------|-----------|----------|
| PERF-001 | Sequential jobs | `needs` on independent jobs | Performance |
| PERF-002 | No caching | Missing `actions/cache` | Performance |
| PERF-003 | Duplicate installs | Multiple `composer install` | Performance |
| SEC-001 | Secrets in logs | `echo.*secrets\.` | Security |
| SEC-002 | Mutable actions | `uses:.*@(main\|master\|v\d)$` | Security |
| SEC-003 | No permissions | Missing `permissions:` | Security |
| SEC-004 | Unsafe PR target | `pull_request_target` + untrusted checkout | Security |
| MAINT-001 | Duplicated config | Similar job definitions | Maintenance |
| MAINT-002 | Hardcoded values | Repeated version strings | Maintenance |
| MAINT-003 | No workflow reuse | Identical steps across workflows | Maintenance |
| REL-001 | No timeouts | Missing `timeout-minutes` | Reliability |
| REL-002 | No health checks | Services without `options:` | Reliability |
| REL-003 | No retry | Network ops without retry logic | Reliability |

## Severity Classification

| Category | Severity |
|----------|----------|
| Security (SEC-*) | Critical |
| Performance (PERF-*) | Major |
| Reliability (REL-*) | Major |
| Maintenance (MAINT-*) | Minor |

## Output Format

```markdown
# CI Antipattern Analysis

**File:** `.github/workflows/ci.yml`
**Total Antipatterns:** N

## Summary by Category

| Category | Count | Impact |
|----------|-------|--------|
| Performance | N | +X min/build |
| Security | N | Risk level |
| Maintenance | N | Technical debt |
| Reliability | N | Flaky builds |

## Detected Antipatterns

### [ID]: [Title]
**Severity:** Critical/Major/Minor
**Impact:** [Specific impact]
**Location:** Lines X-Y

**Current:**
[Problematic configuration]

**Fix:**
[Corrected configuration]

## Estimated Improvements

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Build time | X min | Y min | -Z% |
| Security score | C | A | +N grades |

## Remediation Priority

1. **Immediate:** Security issues
2. **This sprint:** Performance issues
3. **Next sprint:** Maintenance issues
```

## Usage

Provide:
- Path to CI configuration
- Specific categories to focus on (optional)

The detector will:
1. Parse configuration
2. Apply detection rules
3. Calculate impact
4. Generate prioritized fixes

## References

- `references/patterns.md` — detailed antipattern examples with problematic and fixed YAML configurations for all categories (Performance, Security, Maintenance, Reliability)
