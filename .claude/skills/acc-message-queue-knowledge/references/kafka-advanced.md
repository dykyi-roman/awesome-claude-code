# Kafka Advanced Patterns Reference

## Partitioning Strategies

### Key-Based Partitioning (Default)

```
Messages with same key → same partition → guaranteed ordering

Key: "order-123" → hash("order-123") % partitions → Partition 2
Key: "order-456" → hash("order-456") % partitions → Partition 0
Key: null        → round-robin across partitions
```

| Strategy | Ordering | Distribution | Use Case |
|----------|----------|-------------|----------|
| Key-based | Per key | May be uneven | Events per entity (order ID) |
| Round-robin | None | Even | Independent messages, max throughput |
| Custom | Per logic | Controlled | Geographic, priority-based |

### Custom Partitioner

```php
// RdKafka custom partitioner
$conf = new \RdKafka\Conf();
$conf->set('partitioner', 'murmur2_random'); // or 'consistent_random'

// Manual partition assignment
$topic->producev(
    partition: RD_KAFKA_PARTITION_UA, // auto-assign
    msgflags: 0,
    payload: $payload,
    key: $orderId, // partition by order ID
);
```

### Partition Count Guidelines

| Messages/sec | Recommended Partitions | Reasoning |
|-------------|----------------------|-----------|
| < 1K | 3-6 | Minimum for HA |
| 1K-10K | 6-12 | Good parallelism |
| 10K-100K | 12-30 | High parallelism |
| > 100K | 30-100+ | Max throughput |

Rule of thumb: partitions >= max(expected consumers, throughput / consumer_capacity).

## Consumer Group Coordination

### Partition Assignment

```
Consumer Group "order-service" (3 consumers, 6 partitions):

Consumer 1: [Partition 0, Partition 1]
Consumer 2: [Partition 2, Partition 3]
Consumer 3: [Partition 4, Partition 5]
```

### Rebalancing Triggers

| Trigger | What Happens |
|---------|-------------|
| Consumer joins group | Partitions redistributed |
| Consumer leaves/crashes | Its partitions reassigned |
| New partitions added | Partitions redistributed |
| Consumer heartbeat timeout | Consumer considered dead |

### Rebalancing Strategies

| Strategy | Description | When |
|----------|-------------|------|
| Eager (default) | Revoke all, reassign all | Simple, brief unavailability |
| Cooperative (sticky) | Only reassign needed partitions | Minimal disruption |
| Static membership | Consumer keeps assignment across restarts | Stateful consumers |

### PHP Consumer Group

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Messaging\Kafka;

final class KafkaConsumerWorker
{
    private \RdKafka\KafkaConsumer $consumer;

    public function __construct(
        private readonly string $groupId,
        private readonly string $brokers,
        private readonly MessageHandlerInterface $handler,
    ) {
        $conf = new \RdKafka\Conf();
        $conf->set('group.id', $this->groupId);
        $conf->set('metadata.broker.list', $this->brokers);
        $conf->set('auto.offset.reset', 'earliest');
        $conf->set('enable.auto.commit', 'false'); // manual commit
        $conf->set('partition.assignment.strategy', 'cooperative-sticky');
        $conf->set('session.timeout.ms', '30000');
        $conf->set('heartbeat.interval.ms', '10000');
        $conf->set('max.poll.interval.ms', '300000');

        $this->consumer = new \RdKafka\KafkaConsumer($conf);
    }

    /**
     * @param list<string> $topics
     */
    public function run(array $topics): void
    {
        $this->consumer->subscribe($topics);

        while (true) {
            $message = $this->consumer->consume(timeout_ms: 1000);

            if ($message === null || $message->err === RD_KAFKA_RESP_ERR__PARTITION_EOF) {
                continue;
            }

            if ($message->err === RD_KAFKA_RESP_ERR__TIMED_OUT) {
                continue;
            }

            if ($message->err !== RD_KAFKA_RESP_ERR_NO_ERROR) {
                throw new \RuntimeException($message->errstr());
            }

            $this->handler->handle($message->payload, $message->key, $message->headers ?? []);
            $this->consumer->commit($message); // sync commit after processing
        }
    }
}
```

## Offset Management

### Auto-Commit vs Manual

| Mode | Config | Safety | Use Case |
|------|--------|--------|----------|
| Auto-commit | `enable.auto.commit=true` | At-most-once risk | Non-critical data |
| Sync commit | `commitSync()` after processing | At-least-once | Default recommendation |
| Async commit | `commitAsync()` after processing | At-least-once (slight risk) | High throughput |
| Transactional | `sendOffsetsToTransaction()` | Exactly-once | Critical data |

### Offset Seek and Reset

```php
// Seek to specific offset
$this->consumer->seek($topicPartition, offset: 1000, timeout_ms: 5000);

// Seek to timestamp
$topicPartitions = $this->consumer->offsetsForTimes([
    new \RdKafka\TopicPartition('orders', 0, $timestamp_ms),
], timeout_ms: 5000);
$this->consumer->assign($topicPartitions);
```

### Offset Reset Policies

| Policy | `auto.offset.reset` | Behavior |
|--------|---------------------|----------|
| Earliest | `earliest` | Start from beginning |
| Latest | `latest` | Start from end (default) |
| None | `none` | Throw error if no committed offset |

## Schema Registry and Schema Evolution

### Schema Registry Overview

```
Producer → Schema Registry (register/validate) → Kafka Broker
                    ↕
Consumer → Schema Registry (fetch schema) → Deserialize
```

### Compatibility Modes

| Mode | Rule | Safe Changes |
|------|------|-------------|
| BACKWARD | New schema can read old data | Add optional fields, remove fields |
| FORWARD | Old schema can read new data | Add fields, remove optional fields |
| FULL | Both backward and forward | Add/remove optional fields only |
| NONE | No compatibility check | Any change (dangerous) |

### Avro Schema Example

```json
{
    "type": "record",
    "name": "OrderCreated",
    "namespace": "com.example.events",
    "fields": [
        {"name": "order_id", "type": "string"},
        {"name": "customer_id", "type": "string"},
        {"name": "total_cents", "type": "long"},
        {"name": "currency", "type": "string", "default": "USD"},
        {"name": "created_at", "type": "string"}
    ]
}
```

### Schema Evolution Best Practices

1. **Always use a schema** — Avro, Protobuf, or JSON Schema
2. **Set compatibility mode** — BACKWARD for consumers, FORWARD for producers
3. **Never remove required fields** — make them optional first
4. **Use defaults for new fields** — allows old consumers to read new data
5. **Version schemas** — track changes in schema registry

## Exactly-Once Semantics

### Idempotent Producer

```php
$conf = new \RdKafka\Conf();
$conf->set('enable.idempotence', 'true');       // deduplicate at broker
$conf->set('acks', 'all');                       // wait for all replicas
$conf->set('max.in.flight.requests.per.connection', '5'); // max with idempotence
```

### Transactional Producer + Consumer

```php
// Producer side
$producer = new \RdKafka\Producer($conf);
$producer->initTransactions(timeout_ms: 10000);

$producer->beginTransaction();
$topic->produce(RD_KAFKA_PARTITION_UA, 0, $payload1);
$topic->produce(RD_KAFKA_PARTITION_UA, 0, $payload2);
$producer->commitTransaction(timeout_ms: 10000);

// Consumer side: read_committed isolation
$consumerConf->set('isolation.level', 'read_committed');
```

### Exactly-Once Pattern

```
1. Consumer reads message from input topic
2. Begin transaction
3. Process message → produce to output topic
4. Commit consumer offsets within transaction
5. Commit transaction (atomic)
```

## Performance Tuning

### Producer Tuning

| Parameter | Default | Recommendation | Effect |
|-----------|---------|---------------|--------|
| `batch.size` | 16KB | 64KB-256KB | Larger batches = higher throughput |
| `linger.ms` | 0 | 5-50ms | Wait for batch fill |
| `compression.type` | none | `lz4` or `snappy` | Reduce network/disk |
| `acks` | 1 | `all` for safety | Durability vs latency |
| `buffer.memory` | 32MB | 64-128MB | Producer buffer |

### Consumer Tuning

| Parameter | Default | Recommendation | Effect |
|-----------|---------|---------------|--------|
| `fetch.min.bytes` | 1 | 1KB-1MB | Wait for data batch |
| `fetch.max.wait.ms` | 500 | 100-500ms | Max wait for fetch |
| `max.poll.records` | 500 | 100-1000 | Records per poll |
| `max.poll.interval.ms` | 300000 | Adjust to processing time | Rebalance timeout |
| `session.timeout.ms` | 45000 | 10000-30000 | Failure detection speed |

### Compression Comparison

| Algorithm | Ratio | CPU (compress) | CPU (decompress) | Recommended |
|-----------|-------|---------------|-------------------|-------------|
| None | 1x | — | — | Lowest latency |
| LZ4 | 2-3x | Low | Very low | Default choice |
| Snappy | 2-3x | Low | Low | Alternative to LZ4 |
| ZSTD | 3-5x | Medium | Low | Best ratio |
| GZIP | 3-5x | High | Medium | Legacy |

## PHP RdKafka Advanced Configuration

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Messaging\Kafka;

final readonly class KafkaConfigFactory
{
    public static function createProducerConfig(
        string $brokers,
        string $clientId,
    ): \RdKafka\Conf {
        $conf = new \RdKafka\Conf();
        $conf->set('metadata.broker.list', $brokers);
        $conf->set('client.id', $clientId);
        $conf->set('enable.idempotence', 'true');
        $conf->set('acks', 'all');
        $conf->set('compression.type', 'lz4');
        $conf->set('batch.size', '65536');      // 64KB
        $conf->set('linger.ms', '10');
        $conf->set('retries', '3');
        $conf->set('retry.backoff.ms', '100');
        $conf->set('delivery.timeout.ms', '30000');

        // Error callback
        $conf->setErrorCb(function ($kafka, $err, $reason): void {
            throw new \RuntimeException(
                sprintf('Kafka error: %s (reason: %s)', rd_kafka_err2str($err), $reason),
            );
        });

        return $conf;
    }

    public static function createConsumerConfig(
        string $brokers,
        string $groupId,
        string $clientId,
    ): \RdKafka\Conf {
        $conf = new \RdKafka\Conf();
        $conf->set('metadata.broker.list', $brokers);
        $conf->set('group.id', $groupId);
        $conf->set('client.id', $clientId);
        $conf->set('auto.offset.reset', 'earliest');
        $conf->set('enable.auto.commit', 'false');
        $conf->set('partition.assignment.strategy', 'cooperative-sticky');
        $conf->set('session.timeout.ms', '30000');
        $conf->set('heartbeat.interval.ms', '10000');
        $conf->set('max.poll.interval.ms', '300000');
        $conf->set('fetch.min.bytes', '1024');    // 1KB
        $conf->set('fetch.max.wait.ms', '500');

        return $conf;
    }
}
```
