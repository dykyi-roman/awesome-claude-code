# Features

## Priority 1 — Enterprise / Integration Patterns (5 skills)

- `acc-create-unit-of-work` — Unit of Work (transactional consistency)
  Host: acc-integration-generator | Command: /acc-generate-patterns
- `acc-create-message-broker-adapter` — Adapters for RabbitMQ/Kafka/SQS
  Host: acc-integration-generator | Command: /acc-generate-patterns
- `acc-create-idempotent-consumer` — Idempotent Consumer / message deduplication
  Host: acc-integration-generator | Command: /acc-generate-patterns
- `acc-create-dead-letter-queue` — Dead Letter Queue handler
  Host: acc-integration-generator | Command: /acc-generate-patterns
- `acc-create-timeout` — Timeout pattern generator (auditor acc-check-timeout-strategy exists, need creator)
  Host: acc-stability-generator | Command: /acc-generate-patterns

## Priority 2 — Knowledge Skills (4 skills)

- `acc-microservices-knowledge` — Service mesh, API gateway, service discovery
  Referenced by: acc-structural-auditor, acc-architecture-generator
- `acc-api-design-knowledge` — REST/GraphQL best practices, Richardson Maturity, RFC 7807
  Referenced by: acc-integration-generator
- `acc-message-queue-knowledge` — RabbitMQ/Kafka patterns, exchange types, consumer groups
  Referenced by: acc-integration-generator, acc-cqrs-auditor
- `acc-caching-strategies-knowledge` — TTL, invalidation, distributed caching, Redis patterns
  Referenced by: acc-stability-generator