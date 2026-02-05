Features:
* CI Fixes command
* Docker сommand

## Structural Patterns (GoF)
- `acc-create-adapter` — Adapter pattern (обёртка для несовместимых интерфейсов)
- `acc-create-facade` — Facade pattern (упрощённый интерфейс к сложной подсистеме)
- `acc-create-proxy` — Proxy pattern (контроль доступа, lazy loading, caching)
- `acc-create-composite` — Composite pattern (древовидные структуры)

## Enterprise / Integration Patterns
- `acc-create-unit-of-work` — Unit of Work (транзакционная согласованность)
- `acc-create-event-dispatcher` — Event Dispatcher / Event Bus
- `acc-create-message-broker-adapter` — Адаптеры для RabbitMQ/Kafka/SQS
- `acc-create-idempotency-handler` — Idempotent Consumer pattern
- `acc-create-dead-letter-handler` — Dead Letter Queue handler

## CQRS / Event Sourcing
- `acc-create-event-store` — Event Store implementation
- `acc-create-projection` — Event Sourcing Projections (rebuild read models)
- `acc-create-snapshot` — Snapshot pattern для агрегатов

## API / Infrastructure
- `acc-create-api-action` — REST/GraphQL контроллеры
- `acc-create-api-versioning` — API versioning strategy
- `acc-create-health-check` — Health Check endpoints
- `acc-create-cache-aside` — Cache-Aside pattern

## Observability
- `acc-create-correlation-context` — Correlation ID propagation
- `acc-create-audit-log` — Audit logging pattern

## Security
- `acc-create-authorization-policy` — Authorization policies
- `acc-create-input-validator` — Input validation / sanitization

## Knowledge Skills
- `acc-microservices-knowledge` — Microservices patterns (service mesh, API gateway)
- `acc-testing-knowledge` — Testing strategies (unit, integration, contract, e2e)
- `acc-api-design-knowledge` — REST/GraphQL best practices


3.2 Priority 2 — GoF Structural Patterns (6 skills)

acc-create-adapter      — Интеграция несовместимых интерфейсов                                                                                                        
acc-create-facade       — Упрощенный интерфейс к подсистеме                                                                                                           
acc-create-proxy        — Контроль доступа, lazy loading                                                                                                              
acc-create-composite    — Древовидные структуры                                                                                                                       
acc-create-bridge       — Развязка абстракции от реализации                                                                                                           
acc-create-flyweight    — Оптимизация памяти

3.3 Priority 3 — GoF Behavioral Patterns (4 skills)

acc-create-template-method  — Скелет алгоритма                                                                                                                        
acc-create-visitor          — Операции без изменения классов                                                                                                          
acc-create-iterator         — Последовательный доступ                                                                                                                 
acc-create-memento          — Сохранение состояния (undo/redo)

3.4 Priority 4 — Enterprise Patterns (4 skills)

acc-create-unit-of-work         — Транзакционная согласованность                                                                                                      
acc-create-idempotent-consumer  — Дедупликация сообщений                                                                                                              
acc-create-dead-letter-queue    — Обработка failed messages                                                                                                           
acc-create-timeout              — Таймауты для resilience

3.5 Priority 5 — Knowledge Skills (6 skills)

acc-security-knowledge          — OWASP Top 10                                                                                                                        
acc-api-design-knowledge        — REST/GraphQL best practices                                                                                                         
acc-message-queue-knowledge     — RabbitMQ/Kafka patterns                                                                                                             
acc-caching-strategies-knowledge — TTL, invalidation                                                                                                                  
acc-bounded-context-knowledge   — Strategic DDD

3.6 Priority 6 — New Audit Commands (4 commands)

/acc-audit-security     — OWASP compliance                                                                                                                            
/acc-audit-performance  — N+1 queries, bottlenecks                                                                                                                    
/acc-audit-testing      — Coverage analysis                                                                                                                           
/acc-audit-dependencies — Outdated packages, CVEs

3.7 Priority 7 — New Agents (4 agents)

acc-security-auditor      — Для /acc-audit-security                                                                                                                   
acc-performance-analyzer  — Для /acc-audit-performance                                                                                                                
acc-psr-auditor          — Для /acc-audit-psr (fix)                                                                                                                   
acc-testing-generator    — Генерация тестов           