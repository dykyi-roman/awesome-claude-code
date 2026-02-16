---
name: acc-create-deptrac-config
description: Generates DEPTRAC configurations for PHP projects. Creates deptrac.yaml with DDD layer rules, bounded context separation, and dependency constraints.
---

# DEPTRAC Configuration Generator

Generates optimized DEPTRAC configurations for architectural dependency analysis.

## Generated Files

```
deptrac.yaml              # Main configuration
deptrac-baseline.yaml     # Violation baseline (if needed)
```

## Configuration by Architecture

### DDD Layered Architecture

```yaml
# deptrac.yaml
deptrac:
  paths:
    - ./src

  layers:
    #############################################
    # Domain Layer (innermost)
    #############################################
    - name: Domain
      collectors:
        - type: directory
          value: src/Domain/.*

    # Domain sublayers
    - name: Domain.Entity
      collectors:
        - type: directory
          value: src/Domain/.*/Entity/.*

    - name: Domain.ValueObject
      collectors:
        - type: directory
          value: src/Domain/.*/ValueObject/.*

    - name: Domain.Event
      collectors:
        - type: directory
          value: src/Domain/.*/Event/.*

    - name: Domain.Repository
      collectors:
        - type: directory
          value: src/Domain/.*/Repository/.*

    - name: Domain.Service
      collectors:
        - type: directory
          value: src/Domain/.*/Service/.*

    #############################################
    # Application Layer
    #############################################
    - name: Application
      collectors:
        - type: directory
          value: src/Application/.*

    - name: Application.UseCase
      collectors:
        - type: directory
          value: src/Application/.*/UseCase/.*

    - name: Application.Command
      collectors:
        - type: directory
          value: src/Application/.*/Command/.*

    - name: Application.Query
      collectors:
        - type: directory
          value: src/Application/.*/Query/.*

    - name: Application.DTO
      collectors:
        - type: directory
          value: src/Application/.*/DTO/.*

    #############################################
    # Infrastructure Layer
    #############################################
    - name: Infrastructure
      collectors:
        - type: directory
          value: src/Infrastructure/.*

    - name: Infrastructure.Persistence
      collectors:
        - type: directory
          value: src/Infrastructure/Persistence/.*

    - name: Infrastructure.Messaging
      collectors:
        - type: directory
          value: src/Infrastructure/Messaging/.*

    - name: Infrastructure.External
      collectors:
        - type: directory
          value: src/Infrastructure/External/.*

    #############################################
    # Presentation Layer (outermost)
    #############################################
    - name: Presentation
      collectors:
        - type: directory
          value: src/(Api|Web|Console)/.*

    - name: Presentation.Api
      collectors:
        - type: directory
          value: src/Api/.*

    - name: Presentation.Web
      collectors:
        - type: directory
          value: src/Web/.*

    - name: Presentation.Console
      collectors:
        - type: directory
          value: src/Console/.*

  #############################################
  # Dependency Rules
  #############################################
  ruleset:
    # Domain has NO dependencies (except language primitives)
    Domain: []
    Domain.Entity: []
    Domain.ValueObject: []
    Domain.Event: []
    Domain.Repository: []  # Only interfaces
    Domain.Service:
      - Domain.Entity
      - Domain.ValueObject
      - Domain.Event
      - Domain.Repository

    # Application depends only on Domain
    Application:
      - Domain
    Application.UseCase:
      - Domain
      - Application.DTO
      - Application.Command
      - Application.Query
    Application.Command:
      - Domain
    Application.Query:
      - Domain
    Application.DTO:
      - Domain.ValueObject  # Can use VOs for type safety

    # Infrastructure implements Domain interfaces
    Infrastructure:
      - Domain
      - Application
    Infrastructure.Persistence:
      - Domain.Entity
      - Domain.Repository
      - Domain.ValueObject
    Infrastructure.Messaging:
      - Domain.Event
      - Application.Command
    Infrastructure.External:
      - Domain
      - Application

    # Presentation depends on Application
    Presentation:
      - Application
      - Domain  # For DTOs, VOs in responses
    Presentation.Api:
      - Application.UseCase
      - Application.DTO
      - Domain.ValueObject
    Presentation.Web:
      - Application.UseCase
      - Application.DTO
    Presentation.Console:
      - Application.UseCase
      - Application.Command
```

See `references/examples.md` for: Bounded Context separation, Hexagonal Architecture, Advanced Collectors (class name, interface, attribute, combined), Baseline management, CI configuration (GitHub/GitLab), output formats, common violations and fixes.

## Generation Instructions

1. **Analyze project:**
   - Identify architecture style (DDD, Hexagonal, etc.)
   - Map directory structure
   - Find bounded contexts

2. **Define layers:**
   - Start with main layers (Domain, Application, Infrastructure, Presentation)
   - Add sublayers if needed
   - Create bounded context layers if multi-context

3. **Define rules:**
   - Domain depends on nothing
   - Each layer depends only on inner layers
   - Cross-context only via SharedKernel/Events

4. **Handle violations:**
   - Generate baseline for existing violations
   - Plan refactoring to remove violations

## Usage

Provide:
- Project path
- Architecture style (DDD/Hexagonal/Layered)
- Bounded contexts (if any)
- Current violations to baseline (optional)

The generator will:
1. Analyze directory structure
2. Create appropriate layers
3. Define dependency rules
4. Generate baseline if needed
