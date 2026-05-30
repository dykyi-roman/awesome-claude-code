---
name: check-architecture-neutrality
description: Audits plugin skill files (SKILL.md, references/*.md, assets/*.md) for architecture bias. Verifies content works across all supported architectures (Clean, Hexagonal, Layered 3-tier, N-Tier, Package-by-Feature, MVC) except for explicitly architecture-specific skills. Catches universal claims that only hold in one architecture, layer-prefixed namespaces/paths, invented folder names, and per-architecture conventions misrepresented as DDD universals.
---

# Architecture Neutrality Checker

This skill detects architecture bias in plugin skill content. It checks that skill files do not assert one architecture's rules across all architectures, and that they align with the per-architecture conventions documented in the `*-arch-knowledge` skills.

Run this skill before merging new or rewritten skill content, and as part of release-quality audits for the plugin itself.

## What "architecture-neutral" means

Skill content is **architecture-neutral** when its prose, examples, detection patterns, and rules either:

1. Apply universally across **Clean Architecture**, **Hexagonal**, **Layered 3-tier (Domain-centric)**, **N-Tier (4-tier Classical)**, **Package-by-Feature**, and **MVC** — or
2. Explicitly qualify per-architecture differences (e.g. "in Clean / Hexagonal X is a violation; in Layered 3-tier it is a project choice").

Skill content is **biased** when it asserts as universal something that is in fact one architecture's rule (e.g. "Repository implementations live in Infrastructure" — Clean / Hexagonal / N-Tier yes, Layered 3-tier no).

## Exempt skills

These skills are intentionally architecture-specific and are NOT checked:

```
skills/clean-arch-knowledge/
skills/hexagonal-knowledge/
skills/layer-arch-knowledge/
skills/n-tier-arch-knowledge/
skills/microservices-knowledge/
skills/detect-architecture-pattern/
skills/check-bounded-contexts/
skills/check-leaky-abstractions/
```

These framework-knowledge skills are light-touch — framework-conventional paths are kept:

```
skills/symfony-knowledge/
skills/laravel-knowledge/
skills/yii-knowledge/
skills/codeigniter-knowledge/
skills/no-framework-knowledge/
```

These carve-outs are intentional (the bias IS the lesson):

```
skills/psr-autoloading-knowledge/      # PSR-4 namespace mechanics — App\Domain\... conventional form is the topic
skills/ci-tools-knowledge/             # PHPStan/Psalm/Rector layer-enforcement DSL examples
skills/architecture-doc-template/      # Framework-conventional doc shape
skills/grasp-knowledge/                # GRASP teaching context using Repository as canonical example
skills/create-deptrac-config/          # Per-architecture references explicitly cover one architecture each
skills/create-phpstan-config/          # Light-touch — DSL examples kept
skills/create-psalm-config/            # Light-touch — DSL examples kept
skills/create-rector-config/           # Light-touch — DSL examples kept
```

## Violation categories

Each category corresponds to a rule in `CORRECTION_PLAN.md` Section 3 (the source of truth for these rules).

| ID | Rule | What to detect | Severity |
|---|---|---|---|
| **V1** | No "Evans" as authority in prose | `\bEvans\b` outside `## References` bibliographic citations | Warning |
| **V2** | Repository is one pattern, not interface/impl split | "Repository Interface" / "Repository Implementation" as section titles or universal framing | Critical |
| **V3** | No invented layer names | "Application-orchestration port", "Domain-level contract", "Adapter Concern", "Entry-Point Concern" | Critical |
| **V4** | No internal/private project names | Any internal codename or private project reference appearing in public plugin content | Critical |
| **N1/N2** | No layer-prefixed namespaces in examples | `^namespace (Domain\|Application\|Infrastructure\|Presentation)\\` (without `App\` prefix is the reduced form — these full-form ones indicate bulk-script residual) | Warning |
| **N3** | No biased `src/{Layer}/` paths | `src/(Domain\|Application\|Infrastructure\|Presentation)/` in `**File:**` headers | Critical |
| **N5** | Test namespaces reduced | `Tests\\Unit\\(Domain\|Application\|Infrastructure\|Presentation)\\` in references | Warning |
| **P3** | No false universals | "Domain has no infrastructure dependencies" / "no framework imports in Domain" stated as universal | Critical |
| **P7** | No layer-port misclassifications | "Application layer port" / "Domain layer contract" / "Application-orchestration port" | Critical |
| **P9** | Per-architecture Repository placement | "Repository implementations in Infrastructure" as universal | Critical |
| **A1** | Folder names match the matching `*-arch-knowledge` skill | Invented `src/Adapters/`, `src/Frameworks/`, `Infrastructure/Adapter/Driving/`, `src/Port/Inbound/` | Critical |
| **A2** | Per-architecture content gets per-architecture files | A single `references/examples.md` containing 3+ architectures' configs/rules | Warning |
| **A6** | PBF is a wrapping pattern, not standalone | "PBF's public surface" or treating `Event/` + `Port/` as PBF-defining | Warning |

## Detection patterns

### V1 — Evans as authority
```bash
Grep: "\bEvans\b" --glob "skills/**/*.md"
# Manual review needed: bibliographic citations in ## References sections are OK;
# Authority invocations in prose ("Evans says...") are violations.
```

### V2 — Repository interface/implementation split
```bash
Grep: "Repository [Ii]nterfaces?\b" --glob "skills/**/*.md"
Grep: "Repository [Ii]mplementations?\b" --glob "skills/**/*.md"
# Filter: exempt skills, deptrac-config (per-architecture references), psr-autoloading,
# architecture-doc-template, grasp-knowledge (carve-out content).
```

### V3 — Invented layer names
```bash
Grep: "Application[- ]orchestration port|Domain[- ]level (port|contract)|Adapter [Cc]oncern|Entry[- ][Pp]oint [Cc]oncern" --glob "skills/**/*.md"
```

### V4 — Internal/private project names

Maintain the list of forbidden internal project names in a private location outside the repo (do not document them here — that would itself violate V4). At audit time, run a grep for each name on the list against the skill files:

```bash
# For each {forbidden-name} on the maintainer's private list:
Grep: "{forbidden-name}" --glob "skills/**/*.md"
```

If a name on the list appears in any non-exempt skill file, it is a Critical violation.

### N1/N2 — Bulk-script residual full namespaces
```bash
# These should have been reduced; finding them indicates bulk-script residual.
Grep: "^namespace (Domain|Application|Infrastructure|Presentation)\\\\" --glob "skills/**/*.md"
Grep: "^use App\\\\(Domain|Application|Infrastructure|Presentation)\\\\" --glob "skills/**/*.md"
```

### N3 — Biased src/ paths in headers
```bash
Grep: "\\*\\*(File|Path):\\*\\* \`src/(Domain|Application|Infrastructure|Presentation)/" --glob "skills/**/*.md"
# Or just paths inline:
Grep: "src/(Domain|Application|Infrastructure|Presentation)/" --glob "skills/**/*.md"
# Filter: deptrac DSL examples (intentional), architecture-specific sections
# explicitly labeled as such (e.g. "in Clean / N-Tier this lands at src/Infrastructure/...").
```

### N5 — Biased test namespaces / paths
```bash
Grep: "namespace Tests\\\\Unit\\\\(Domain|Application|Infrastructure|Presentation)\\\\" --glob "skills/**/*.md"
Grep: "tests/Unit/(Domain|Application|Infrastructure|Presentation)/" --glob "skills/**/*.md"
```

### P3 — False universals
```bash
Grep: "Domain has no (external |framework |infrastructure )?dependenc|domain has zero|no framework imports in (the )?[Dd]omain" --glob "skills/**/*.md"
Grep: "The (project|architecture) follows .* where domain (code|layer) has\\s*no" --glob "skills/**/*.md"
# Manual review: per-architecture qualified statements are OK; universals are violations.
```

### P7 — Layer-port misclassifications
```bash
Grep: "Application layer port|Domain layer contract|Application[- ]orchestration port|Domain[- ]level (port|contract)" --glob "skills/**/*.md"
```

### P9 — Universal Repository placement
```bash
Grep: "Repository [Ii]mplementations? in Infrastructure" --glob "skills/**/*.md"
# Filter: explicitly per-architecture statements ("In Clean / N-Tier, Repository
# implementations live in Infrastructure") are OK.
```

### A1 — Invented folder names
Check each architecture-specific output (deptrac, phpstan, psalm, rector configs; ACL examples) against the matching `*-arch-knowledge` skill's folder convention.

```bash
# Common invented names that don't appear in any *-arch-knowledge skill
Grep: "src/Adapters/|src/Frameworks/" --glob "skills/**/*.md"
Grep: "Infrastructure/Adapter/(Driving|Driven|Primary|Secondary)" --glob "skills/**/*.md"
Grep: "src/Port/(Inbound|Outbound)" --glob "skills/**/*.md"
```

If found, cross-reference the matching `*-arch-knowledge` skill — the skill should use folder names that actually appear there.

### A2 — Monolithic multi-architecture examples files
```bash
# Find references/examples.md files that mention 3+ architectures
for f in skills/create-*/references/examples.md; do
  hits=$(grep -cE "Clean Architecture|Hexagonal|Layered 3-tier|N-Tier|Package-by-Feature|MVC" "$f")
  if [ "$hits" -ge 3 ]; then
    echo "$f: $hits architectures mentioned — consider splitting per A2"
  fi
done
```

For multi-architecture generators (deptrac config, phpstan config, etc.), per A2 each architecture should get its own `references/{architecture}.md`.

### A6 — PBF treated as standalone architecture
```bash
Grep: "PBF.*public surface|public surface (Event|Port)|Event/.*Port/.*public surface" --glob "skills/**/*.md"
# PBF wraps an inner architecture. The "public surface" concept is Modular Monolith,
# not Package-by-Feature per se. PBF's actual defining trait is bounded-context-at-top.
```

## Generation Process

### Step 1 — Identify scope
- Single skill folder: `skills/{name}/` — check that skill's files only.
- Whole plugin: `skills/` — check all skills minus the exempt list above.

### Step 2 — Load exempt list
Skip the explicit exempt list (architecture-specific + framework-knowledge + carve-out skills).

### Step 3 — Run each detection pattern
Execute the grep / glob commands for V1–V4, N1/N2/N3/N5, P3/P7/P9, A1/A2/A6.

### Step 4 — Filter false positives
- Lines explicitly labeled as architecture-specific (e.g. "# CLEAN / N-TIER projects only:" preceding a grep example).
- Detection-pattern documentation inside other check-* skills (the grep examples themselves contain biased strings).
- Bibliographic citations in `## References` sections.
- Code comments inside YAML config blocks that are themselves architecture-specific examples (e.g. deptrac layer definitions).

### Step 5 — Produce report
Group findings by file, by rule, and by severity. Total count + per-rule breakdown. Status PASS if zero criticals.

## Output format

```
Architecture Neutrality Audit — {scope}

Files scanned:    {count}
Files exempt:     {count}
Total violations: {n}  (Critical: {c}, Warning: {w})

Per-rule breakdown:
  V1 Evans authority:                  {n}
  V2 Repository interface/impl:        {n}
  V3 Invented layer names:             {n}
  V4 Internal project names:           {n}
  N1/N2 Layer-prefixed namespaces:     {n}
  N3 Biased src/ paths:                {n}
  N5 Biased test namespaces/paths:     {n}
  P3 False universals:                 {n}
  P7 Layer-port misclassifications:    {n}
  P9 Universal Repository placement:   {n}
  A1 Invented folder names:            {n}
  A2 Monolithic multi-arch examples:   {n}
  A6 PBF treated as standalone:        {n}

Critical findings:
| File | Line | Rule | Issue |
|---|---|---|---|
| skills/{X}/SKILL.md | 42 | V2 | "Repository Interface" section title without per-architecture qualifier |
| ... | ... | ... | ... |

Warnings:
| File | Line | Rule | Issue |
|---|---|---|---|
| ... | ... | ... | ... |

Status: PASS / FAIL
(FAIL if any Critical violation found.)
```

## Architecture knowledge skills (reference)

When validating A1 (folder-name correctness), cross-reference against the matching skill:

| Architecture | Skill | Canonical folder layout |
|---|---|---|
| Clean | `acc:clean-arch-knowledge` | `Domain/`, `Application/`, `Infrastructure/`, `Presentation/` |
| Hexagonal | `acc:hexagonal-knowledge` | `Domain/{Context}/Port/Output/`, `Application/{Context}/Port/Input/`, `Infrastructure/{Http,Console,Messaging,Persistence,External}/` |
| Layered 3-tier (Domain-centric) | `acc:layer-arch-knowledge` | `Application/{Http,Console,DI,...}/`, `Domain/{Context}/{Model,Handler,Repository,Repository/Doctrine,Service,Component,...}/`, `Infrastructure/` (generic) |
| N-Tier (4-tier Classical) | `acc:n-tier-arch-knowledge` | `Presentation/`, `Application/`, `Domain/`, `Infrastructure/` |
| Microservices | `acc:microservices-knowledge` | Service-level concerns; not file-level layering |

For generic structures (no dedicated knowledge skill):
- **Package-by-Feature** — `src/{Feature}/` outermost; inner architecture's folders inside.
- **MVC** — `Model/`, `View/`, `Controller/`.

## Usage

Provide:
- Target: a single skill folder path, or "all" for full plugin scan
- Severity threshold: "critical" (fail on critical only) or "any" (fail on any violation)

The skill will:
1. Resolve the exempt list and skip exempt skills
2. Run each detection pattern
3. Filter known false positives
4. Produce a structured report
5. Return PASS / FAIL

Intended use:
- During plugin development — verify a new or edited skill before commit
- As part of release-quality audits before tagging
- In CI, gating PRs that modify skill content
