---
name: microservices-knowledge
description: Microservices Architecture knowledge base. Provides service decomposition, communication patterns, API gateway, service discovery, and data management guidelines for architecture audits and generation.
---

# Microservices Architecture Knowledge Base

Quick reference for microservices architecture patterns and PHP implementation guidelines.

## Core Principles

### Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────────┐
│                     MICROSERVICES ARCHITECTURE                           │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌──────────┐     ┌──────────────────┐     ┌──────────────────┐        │
│   │  Client   │────▶│   API Gateway    │────▶│   Service A      │        │
│   │          │     │  (Routing/Auth)   │     │  (Own Database)  │        │
│   └──────────┘     └──────────────────┘     └──────────────────┘        │
│                           │                       │                      │
│                           │                       │ async                │
│                    ┌──────▼──────┐          ┌─────▼──────────┐          │
│                    │  Service B  │          │  Message Broker │          │
│                    │ (Own DB)    │◀─────────│  (Events/Cmds)  │          │
│                    └─────────────┘          └────────────────┘          │
│                                                                          │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   Decomposition Strategies:                                              │
│   • By Business Capability    - Align with bounded contexts             │
│   • By Subdomain (DDD)        - Core, Supporting, Generic               │
│   • Strangler Fig              - Incremental migration from monolith    │
│                                                                          │
│   Communication:                                                         │
│   • Synchronous  - REST, gRPC, GraphQL (request-response)              │
│   • Asynchronous - Message queues, event streaming                      │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

## Service Communication Patterns

| Pattern | Type | Use When | Trade-off |
|---------|------|----------|-----------|
| REST | Sync | CRUD, simple queries | Easy but coupling |
| gRPC | Sync | Internal service-to-service, performance-critical | Fast but schema coupling |
| GraphQL | Sync | Client-driven queries, BFF | Flexible but complex |
| Message Queue | Async | Reliable delivery, work distribution | Decoupled but eventual consistency |
| Event Streaming | Async | Real-time, event sourcing, audit trails | Scalable but complex ordering |
| Request-Reply | Async | Async request needing response | Decoupled but higher latency |

## API Gateway Patterns

| Pattern | Description | When to Use |
|---------|-------------|-------------|
| Simple Proxy | Routes requests to services | Small number of services |
| Gateway Aggregation | Combines multiple service calls | Reduce client round-trips |
| BFF (Backend for Frontend) | Gateway per client type | Mobile vs Web vs API clients |
| Gateway Offloading | Auth, rate limiting, TLS | Cross-cutting concerns |

## Service Discovery

| Approach | How It Works | Example |
|----------|-------------|---------|
| Client-side | Client queries registry, selects instance | Netflix Eureka |
| Server-side | Load balancer queries registry | AWS ALB, Kubernetes |
| DNS-based | DNS SRV records resolve to instances | Consul DNS, CoreDNS |
| Platform-native | Container orchestrator handles routing | Kubernetes Services |

## Data Management

| Pattern | Description | Consistency |
|---------|-------------|-------------|
| Database per Service | Each service owns its data | Strong (within service) |
| Shared Database | Services share one database | Strong (anti-pattern!) |
| Saga | Distributed transaction via events | Eventual |
| CQRS | Separate read/write models | Eventual |
| Event Sourcing | Events as source of truth | Eventual |
| API Composition | Query multiple services, merge results | Eventual |

## When to Use Microservices vs Monolith

| Factor | Monolith | Microservices |
|--------|----------|---------------|
| Team size | < 10 developers | > 10, multiple teams |
| Domain complexity | Simple/moderate | Complex, many bounded contexts |
| Scalability needs | Uniform scaling | Independent scaling per component |
| Deployment frequency | Infrequent, coordinated | Frequent, independent |
| Technology diversity | Single stack | Polyglot needed |
| Organizational maturity | Starting out | DevOps culture, CI/CD mature |

## Detection Patterns

```bash
# Service boundary indicators
Grep: "HttpClient|GuzzleHttp|curl_init" --glob "**/Infrastructure/**/*.php"
Grep: "grpc|protobuf" --glob "**/*.php"

# API Gateway patterns
Grep: "X-Forwarded|X-Request-ID|X-Correlation" --glob "**/*.php"
Glob: **/Gateway/**/*.php

# Service discovery
Grep: "ServiceDiscovery|ServiceRegistry|consul|etcd" --glob "**/*.php"
Grep: "KUBERNETES_SERVICE|SERVICE_HOST" --glob "**/*.env*"

# Database per service
Grep: "DATABASE_URL|DB_CONNECTION" --glob "**/*.env*"
Grep: "DATABASE_HOST|DB_HOST" --glob "**/docker-compose*.yml"

# Inter-service communication
Grep: "AMQPChannel|RabbitMQ|Kafka|SQS" --glob "**/Infrastructure/**/*.php"
Grep: "EventPublisher|MessageBus" --glob "**/*.php"
```

## Advanced Patterns

### Strangler Fig Pattern

Incrementally migrate from monolith to microservices:

```
Phase 1: Proxy all traffic through gateway
Phase 2: Extract one feature to service, route via gateway
Phase 3: Repeat until monolith is empty shell
Phase 4: Decommission monolith

┌─────────┐     ┌──────────┐     ┌──────────────┐
│  Client  │────▶│ Gateway  │────▶│  New Service  │  (extracted)
│          │     │ (Router) │     └──────────────┘
│          │     │          │────▶┌──────────────┐
│          │     │          │     │  Monolith     │  (shrinking)
└─────────┘     └──────────┘     └──────────────┘
```

**Migration Decision:**

| Factor | Extract First | Keep in Monolith |
|--------|--------------|------------------|
| Change frequency | High | Low |
| Team ownership | Dedicated team | Shared |
| Scaling needs | Independent scaling | Uniform |
| Technology fit | Different stack needed | Same stack fine |

### API Gateway Aggregation Patterns

| Pattern | When | Example |
|---------|------|---------|
| Simple proxy | 1:1 route mapping | `/users` → User Service |
| Aggregation | Client needs data from N services | Order + Customer + Payment |
| BFF | Different clients need different data | Mobile vs Web vs API |
| Offloading | Cross-cutting concerns | Auth, rate limiting, TLS |

### Database-Per-Service Trade-offs

| Aspect | Shared DB | DB per Service |
|--------|-----------|----------------|
| Consistency | ACID transactions | Saga/eventual |
| Querying | JOIN across domains | API composition |
| Independence | Coupled deployments | Independent |
| Complexity | Low | High |
| Schema changes | Coordinated | Independent |

## References

For detailed information, load these reference files:

- `references/patterns.md` — Service mesh, API gateway implementations, service discovery details, data consistency, Strangler Fig, database-per-service
- `references/antipatterns.md` — Distributed monolith, shared database, missing boundaries, chatty communication
