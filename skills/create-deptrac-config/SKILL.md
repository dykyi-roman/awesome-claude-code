---
name: create-deptrac-config
description: Generates DEPTRAC configurations for PHP projects. Creates deptrac.yaml with layer rules for the project's architecture (Clean, Hexagonal, Layered, N-Tier, Package-by-Feature, MVC), bounded-context separation, and dependency constraints.
---

# DEPTRAC Configuration Generator

Generates [DEPTRAC](https://github.com/qossmic/deptrac) configurations for architectural dependency analysis. The deptrac config is architecture-specific by nature — its job is to enforce the dependency rules of a chosen architectural style. This skill ships a dedicated reference per supported architecture, each containing a complete drop-in `deptrac.yaml` plus architecture-specific notes and common violation fixes.

## Generated Files

```
deptrac.yaml              # Main configuration with layers and ruleset
deptrac-baseline.yaml     # Violation baseline (optional, generated on demand)
```

## Supported Architectures

One reference file per architecture. Each file is self-contained: folder structure, full `deptrac.yaml`, architecture-specific notes, and common violation fixes.

| Architecture | Knowledge skill | Defining trait | Reference |
|---|---|---|---|
| **Clean Architecture** | `acc:clean-arch-knowledge` | Source code dependencies point INWARD only; Application does NOT depend on Infrastructure (uses Ports + DI) | [clean.md](references/clean.md) |
| **Hexagonal (Ports & Adapters)** | `acc:hexagonal-knowledge` | Driving Ports under `Application/{Context}/Port/Input/`, Driven Ports under `Domain/{Context}/Port/Output/`, Adapters under `Infrastructure/Http/` and `Infrastructure/Persistence/` | [hexagonal.md](references/hexagonal.md) |
| **Layered (3-tier Domain-centric)** | `acc:layer-arch-knowledge` | Domain owns its persistence implementations (Repository abstraction + Doctrine impl side-by-side under `Domain/{Context}/Repository/`); Infrastructure stays generic | [layered.md](references/layered.md) |
| **N-Tier (4-tier Classical)** | `acc:n-tier-arch-knowledge` | Strict downward calls (Presentation → Application → Domain → Infrastructure); Repository interfaces in Domain, impls in Infrastructure | [n-tier.md](references/n-tier.md) |
| **Package-by-Feature** | combinable wrapper | Top-level partitioning by bounded context (feature); the chosen architectural style (Clean / Layered / Hexagonal / N-Tier) is applied INSIDE each `src/{Feature}/` folder. Not a standalone architecture — it wraps another. | [package-by-feature.md](references/package-by-feature.md) |
| **MVC** | — | Controllers call Models and choose Views; Models have no UI knowledge; Views render passively | [mvc.md](references/mvc.md) |

## Operational add-ons

| Concern | Reference |
|---|---|
| **Bounded-context separation** (overlay on Clean / Hexagonal / Layered / N-Tier) | [bounded-contexts.md](references/bounded-contexts.md) |
| **Advanced collectors, baseline management, CI integration, output formats** | [operations.md](references/operations.md) |

## Generation Instructions

1. **Detect or ask for the architecture style.** Read `composer.json` `autoload.psr-4` paths, scan top-level folders under `src/`, or ask the user. Match against the table above.

2. **Copy the matching reference's `deptrac.yaml`** as the starting point. Adjust:
   - `paths:` block to your actual source folder(s)
   - layer `value:` regexes to your folder naming (case, plural/singular)
   - ruleset entries for any project-specific allowed exceptions

3. **Multi-context projects** — choose between two layout styles:
   - **Layer-first** (`src/Domain/Order/`, `src/Application/Order/`, ...): merge layers and ruleset from [bounded-contexts.md](references/bounded-contexts.md) with the architecture's config. Both rulesets must be satisfied.
   - **Feature-first / Package-by-Feature** (`src/Order/Domain/`, `src/Order/Application/`, ...): use [package-by-feature.md](references/package-by-feature.md) — it shows PBF combined with each of the 4 inner architectures (Layered, Clean, Hexagonal, N-Tier).

4. **Generate a baseline** for legacy projects with existing violations:

   ```bash
   vendor/bin/deptrac analyse --baseline=deptrac-baseline.yaml
   ```

   Add `baseline: deptrac-baseline.yaml` to `deptrac.yaml`. See [operations.md → Baseline Management](references/operations.md#baseline-management).

5. **Wire into CI.** See [operations.md → CI Configuration](references/operations.md#ci-configuration) for GitHub Actions and GitLab CI snippets.

## Usage

Provide:
- Project path (or current directory)
- Architecture style (one from the table above; ask if unclear — refuse to guess if the directory structure is ambiguous)
- Bounded contexts list (if multi-context and architecture is not Package-by-Feature)
- Whether to generate a baseline for existing violations

The generator will:
1. Pick the matching architecture reference
2. Tailor the `paths:` and layer regexes to the project
3. Add bounded-context layers if requested
4. Optionally generate a baseline file
5. Optionally emit the CI snippet
