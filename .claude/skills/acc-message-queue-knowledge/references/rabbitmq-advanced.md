# RabbitMQ Advanced Patterns Reference

## Queue Types Comparison

| Queue Type | Durability | Replication | Performance | Use Case |
|-----------|-----------|-------------|-------------|----------|
| Classic | Durable/Transient | Mirroring (deprecated) | Highest throughput | Legacy, simple workloads |
| Quorum | Always durable | Raft consensus (majority) | Good throughput | Production default (3.8+) |
| Stream | Always durable | Raft-based | High throughput, append-only | Log-like, fan-out, replay |

### Quorum Queues (Recommended Default)

```php
// Declare quorum queue
$channel->queue_declare(
    queue: 'orders',
    durable: true,
    arguments: new AMQPTable([
        'x-queue-type' => 'quorum',
        'x-delivery-limit' => 5,  // max redeliveries before dead-letter
    ]),
);
```

Quorum queue advantages:
- Automatic leader election on node failure
- Data safety (Raft consensus)
- Poison message handling (delivery limit)
- Built-in dead-lettering

### Stream Queues (3.9+)

```php
// Declare stream queue
$channel->queue_declare(
    queue: 'events',
    durable: true,
    arguments: new AMQPTable([
        'x-queue-type' => 'stream',
        'x-max-length-bytes' => 5_000_000_000, // 5GB retention
        'x-stream-max-segment-size-bytes' => 500_000_000, // 500MB segments
    ]),
);

// Consumer with offset
$channel->basic_consume(
    queue: 'events',
    arguments: new AMQPTable([
        'x-stream-offset' => 'first', // or 'last', timestamp, offset number
    ]),
);
```

## Exchange Topologies

### Direct Exchange (Point-to-Point)

```
Producer → Direct Exchange → [routing_key=order.created] → Queue A
                           → [routing_key=order.paid]    → Queue B
```

### Topic Exchange (Pattern Matching)

```
Producer → Topic Exchange → [order.*]       → Queue A (all order events)
                          → [order.created] → Queue B (only created)
                          → [*.paid]        → Queue C (all payment events)
                          → [#]             → Queue D (all events / audit log)
```

Wildcards:
- `*` — matches exactly one word
- `#` — matches zero or more words

### Fanout Exchange (Broadcast)

```
Producer → Fanout Exchange → Queue A (Service 1)
                           → Queue B (Service 2)
                           → Queue C (Service 3)
```

### Headers Exchange (Attribute Matching)

```
Producer (headers: {format: pdf, type: report})
    → Headers Exchange
        → Queue A (match: format=pdf)
        → Queue B (match: type=report, format=pdf, x-match=all)
```

### PHP Exchange Declaration

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Messaging\RabbitMQ;

final readonly class ExchangeConfigurator
{
    public function __construct(
        private AMQPChannel $channel,
    ) {}

    public function configureDomainEvents(): void
    {
        // Main topic exchange for domain events
        $this->channel->exchange_declare(
            exchange: 'domain.events',
            type: 'topic',
            durable: true,
        );

        // Dead letter exchange
        $this->channel->exchange_declare(
            exchange: 'domain.events.dlx',
            type: 'fanout',
            durable: true,
        );

        // Order events queue
        $this->channel->queue_declare(
            queue: 'order-service.events',
            durable: true,
            arguments: new AMQPTable([
                'x-queue-type' => 'quorum',
                'x-dead-letter-exchange' => 'domain.events.dlx',
                'x-delivery-limit' => 5,
            ]),
        );

        $this->channel->queue_bind(
            queue: 'order-service.events',
            exchange: 'domain.events',
            routing_key: 'order.*',
        );
    }
}
```

## Priority Queues and TTL

### Priority Queue

```php
// Declare with max priority
$channel->queue_declare(
    queue: 'tasks',
    durable: true,
    arguments: new AMQPTable([
        'x-max-priority' => 10, // priority range 0-10
    ]),
);

// Publish with priority
$message = new AMQPMessage($payload, [
    'delivery_mode' => 2,
    'priority' => 8, // high priority
]);
$channel->basic_publish($message, '', 'tasks');
```

### Message TTL

```php
// Per-queue TTL (all messages)
$channel->queue_declare(
    queue: 'short-lived',
    durable: true,
    arguments: new AMQPTable([
        'x-message-ttl' => 60000, // 60 seconds
        'x-dead-letter-exchange' => 'expired.dlx',
    ]),
);

// Per-message TTL
$message = new AMQPMessage($payload, [
    'expiration' => '30000', // 30 seconds (string!)
]);
```

## Consumer Prefetch and Flow Control

### Prefetch Configuration

```php
// Per-consumer prefetch (recommended)
$channel->basic_qos(
    prefetch_size: 0,    // no size limit
    prefetch_count: 10,  // 10 unacked messages max
    a_global: false,     // per-consumer (not per-channel)
);
```

| Prefetch | Throughput | Latency | Memory |
|----------|-----------|---------|--------|
| 1 | Low | Lowest | Minimal |
| 10-50 | Good | Low | Moderate |
| 100+ | Highest | Higher | High |
| Unlimited (0) | Maximum | Unpredictable | Risk of OOM |

Recommendation: Start with prefetch=10, adjust based on processing time.

## RabbitMQ Cluster and High Availability

### Cluster Topology

```
┌─────────────────────────────────────────────┐
│              RabbitMQ Cluster                 │
│                                               │
│   Node 1 (leader)    Node 2        Node 3    │
│   ┌──────────┐      ┌──────────┐  ┌──────┐  │
│   │ Queue A  │      │ Queue A  │  │Queue A│  │
│   │ (leader) │      │ (follower)│  │(follwr)│  │
│   └──────────┘      └──────────┘  └──────┘  │
│                                               │
│   Quorum: writes succeed when majority ack   │
└─────────────────────────────────────────────┘
```

### Cluster Sizing

| Nodes | Fault Tolerance | Write Majority |
|-------|----------------|----------------|
| 3 | 1 node failure | 2 nodes must ack |
| 5 | 2 node failures | 3 nodes must ack |
| 7 | 3 node failures | 4 nodes must ack |

## Shovel and Federation (Multi-DC)

### Shovel

Moves messages from one broker/queue to another:

```
DC-1 RabbitMQ → Shovel → DC-2 RabbitMQ
(queue: orders)          (queue: orders-replica)
```

Use case: Cross-datacenter message replication.

### Federation

Links exchanges across brokers:

```
DC-1: exchange "events" ←→ Federation ←→ DC-2: exchange "events"
```

Use case: Multi-region pub/sub without full cluster.

## Monitoring

### Key Metrics

| Metric | Warning | Critical |
|--------|---------|----------|
| Queue depth | > 10K messages | > 100K messages |
| Consumer utilization | < 50% | < 20% |
| Unacked messages | > prefetch × 10 | Growing continuously |
| Memory usage | > 60% high watermark | > 80% |
| Disk free | < 2× memory high watermark | < 1GB |
| Connection count | > 80% of limit | > 95% |

### Prometheus Exporter

```yaml
# docker-compose.yml
rabbitmq:
  image: rabbitmq:3-management
  environment:
    RABBITMQ_PLUGINS: "rabbitmq_prometheus rabbitmq_management"
  ports:
    - "15692:15692"  # Prometheus metrics
    - "15672:15672"  # Management UI
```

### PHP Health Check

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Monitoring;

final readonly class RabbitMqHealthCheck implements HealthCheckInterface
{
    public function __construct(
        private AMQPStreamConnection $connection,
    ) {}

    public function name(): string
    {
        return 'rabbitmq';
    }

    public function check(): HealthCheckResult
    {
        try {
            if (!$this->connection->isConnected()) {
                return HealthCheckResult::unhealthy('Connection lost');
            }

            $channel = $this->connection->channel();
            $channel->close();

            return HealthCheckResult::healthy();
        } catch (\Throwable $e) {
            return HealthCheckResult::unhealthy($e->getMessage());
        }
    }
}
```
