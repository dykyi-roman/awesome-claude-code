---
description: Generate or rewrite tests for PHP file/folder. Creates unit tests, integration tests, builders, mocks following DDD/CQRS patterns.
allowed-tools: Task
model: sonnet
argument-hint: <path> [-- additional instructions]
---

# Generate Tests

Invoke the `acc-test-generator` agent to create tests for PHP code.

## Input Parsing

Parse `$ARGUMENTS` to extract path and optional meta-instructions:

```
Format: <path> [-- <meta-instructions>]

Examples:
- /acc-generate-test src/Domain/Order/Order.php
- /acc-generate-test src/Domain/Order/ -- only unit tests, skip integration
- /acc-generate-test src/Service/PaymentService.php -- include edge cases for null payments
- /acc-generate-test src/ -- create builders for all entities
- /acc-generate-test src/Application/ -- focus on happy path scenarios
```

**Parsing rules:**
1. Split `$ARGUMENTS` by ` -- ` (space-dash-dash-space)
2. First part = **path** (required)
3. Second part = **meta-instructions** (optional, customization)

## Usage

```
/acc-generate-test <path> [-- instructions]
```

## Examples

```bash
# Generate tests for a single class
/acc-generate-test src/Domain/Order/Order.php

# Generate tests for a folder
/acc-generate-test src/Domain/Order/

# Generate with specific focus
/acc-generate-test src/Domain/Order/ -- focus on invariant violations

# Generate tests for Application layer
/acc-generate-test src/Application/PlaceOrder/
```

## What It Generates

### For Domain Layer

| Class Type | Generated |
|------------|-----------|
| Value Object | Unit test (validation, equality) |
| Entity | Unit test (state, transitions, events) |
| Aggregate | Unit test (invariants, consistency) |
| Domain Service | Unit test with Fakes |
| Repository Interface | — (impl tested separately) |

### For Application Layer

| Class Type | Generated |
|------------|-----------|
| Command Handler | Unit test with mocked repos |
| Query Handler | Unit test |
| Use Case | Unit test |

### For Infrastructure Layer

| Class Type | Generated |
|------------|-----------|
| Repository Implementation | Integration test |
| HTTP Client | Integration test |
| Cache Adapter | Integration test |

### Test Helpers (as needed)

- **Builders** — for complex object construction
- **Mothers** — for common test scenarios
- **Fakes** — InMemory repositories
- **Stubs** — for external services

## Execution

Use the Task tool to invoke the test generator agent:

```
Task tool with subagent_type="acc-test-generator"
prompt: "Generate tests for $ARGUMENTS. Analyze the code, determine test type (unit/integration), create appropriate tests following AAA pattern, PHPUnit 11 attributes, and proper naming. Include edge cases and exception paths."
```

## Output

The agent will:
1. Analyze the source code
2. Determine appropriate test types
3. Check for existing test helpers
4. Generate test files
5. Report generated files with paths

## Generated File Structure

```
tests/
├── Unit/
│   └── Domain/
│       └── Order/
│           ├── OrderTest.php
│           ├── OrderIdTest.php
│           └── OrderStatusTest.php
├── Integration/
│   └── Infrastructure/
│       └── DoctrineOrderRepositoryTest.php
├── Builder/
│   └── OrderBuilder.php
├── Mother/
│   └── OrderMother.php
└── Fake/
    └── InMemoryOrderRepository.php
```

## Test Quality Rules

Generated tests follow:
- One behavior per test
- AAA pattern (Arrange-Act-Assert)
- Descriptive naming (`test_{method}_{scenario}_{expected}`)
- PHPUnit 11 attributes (`#[Group]`, `#[CoversClass]`)
- No logic in tests (no if/for/while)
- ≤3 mocks per test
- Real Value Objects (no mocking)
- Fakes for repositories (not mocks)
