---
name: acc-message-queue-knowledge
description: Message Queue knowledge base. Provides broker comparison, delivery guarantees, consumer groups, and advanced RabbitMQ/Kafka patterns for messaging audits and generation.
---

# Message Queue Knowledge Base

Quick reference for message broker operations and advanced messaging patterns. Focuses on broker-level operations — for event-driven patterns, see `acc-eda-knowledge`.

## Broker Comparison

| Feature | RabbitMQ | Apache Kafka | Amazon SQS | Redis Streams |
|---------|----------|-------------|------------|---------------|
| Model | Message queue | Event log | Message queue | Event log |
| Ordering | Per-queue FIFO | Per-partition | Best-effort (FIFO available) | Per-stream |
| Retention | Until consumed | Time/size-based | 4-14 days | Memory/size-based |
| Replay | No (once consumed) | Yes (offset seek) | No | Yes (ID-based) |
| Consumer Groups | Competing consumers | Native support | Not built-in | Native (XREADGROUP) |
| Throughput | ~50K msg/s | ~1M msg/s | ~3K msg/s per queue | ~100K msg/s |
| Latency | Sub-millisecond | Low milliseconds | 10-100ms | Sub-millisecond |
| Protocol | AMQP 0-9-1 | Custom (TCP) | HTTP/SQS API | RESP |
| Clustering | Quorum queues | Built-in (ZK/KRaft) | Managed | Redis Cluster |
| Best for | Task queues, RPC | Event streaming, logs | Serverless, AWS-native | Lightweight streaming |

## Message Delivery Guarantees

| Guarantee | Description | Implementation | Trade-off |
|-----------|-------------|----------------|-----------|
| At-most-once | Message may be lost | Fire-and-forget, no ack | Fastest, data loss possible |
| At-least-once | Message delivered 1+ times | Ack after processing | Requires idempotent consumers |
| Exactly-once | Message processed exactly once | Transactional + deduplication | Slowest, most complex |

### Achieving At-Least-Once in PHP

```php
// RabbitMQ: manual acknowledgment
$channel->basic_consume(
    queue: 'orders',
    no_ack: false,  // require explicit ack
    callback: function (AMQPMessage $msg) use ($channel): void {
        try {
            $this->handler->handle(json_decode($msg->getBody(), true));
            $channel->basic_ack($msg->getDeliveryTag());
        } catch (\Throwable $e) {
            $channel->basic_nack($msg->getDeliveryTag(), requeue: true);
        }
    },
);
```

## Consumer Groups Overview

| Broker | Mechanism | How It Works |
|--------|-----------|-------------|
| RabbitMQ | Competing consumers | Multiple consumers on same queue; broker distributes round-robin |
| Kafka | Consumer groups | Partitions assigned to group members; each partition read by one consumer |
| Redis Streams | XREADGROUP | Consumer group tracks last delivered ID per consumer |

## Ordering Guarantees

| Broker | Scope | Guarantee |
|--------|-------|-----------|
| RabbitMQ | Per-queue | Strict FIFO within single queue |
| RabbitMQ | Across queues | No ordering guarantee |
| Kafka | Per-partition | Strict ordering within partition |
| Kafka | Across partitions | No ordering guarantee |
| SQS Standard | Queue | Best-effort ordering |
| SQS FIFO | Message group | Strict FIFO within group |
| Redis Streams | Per-stream | Strict ordering by entry ID |

## When to Use Which Broker

| Scenario | Recommended | Why |
|----------|-------------|-----|
| Task distribution (email, image processing) | RabbitMQ | Flexible routing, competing consumers |
| Event streaming / audit log | Kafka | Immutable log, replay, high throughput |
| Simple async in AWS | SQS | Managed, no infrastructure |
| Lightweight pub/sub with low latency | Redis Streams | Already have Redis, minimal overhead |
| RPC / request-reply | RabbitMQ | Built-in reply-to, correlation ID |
| CDC (Change Data Capture) | Kafka | Log compaction, connector ecosystem |
| Prioritized processing | RabbitMQ | Native priority queues |
| Cross-region replication | Kafka | MirrorMaker, built-in replication |

## Detection Patterns

```bash
# RabbitMQ usage
Grep: "AMQPChannel|PhpAmqpLib|bunny|php-amqplib" --glob "**/*.php"
Grep: "RABBITMQ_|AMQP_" --glob "**/.env*"

# Kafka usage
Grep: "RdKafka|kafka|KafkaConsumer|KafkaProducer" --glob "**/*.php"
Grep: "KAFKA_" --glob "**/.env*"

# SQS usage
Grep: "SqsClient|aws/aws-sdk.*sqs" --glob "**/*.php"
Grep: "SQS_|AWS_SQS" --glob "**/.env*"

# Redis Streams
Grep: "XADD|XREAD|XREADGROUP|XACK" --glob "**/*.php"
Grep: "xAdd|xRead|xReadGroup" --glob "**/*.php"

# Consumer patterns
Grep: "basic_consume|consume\(|poll\(" --glob "**/*.php"
Grep: "basic_ack|basic_nack|commitAsync|xAck" --glob "**/*.php"

# Dead letter configuration
Grep: "dead.letter|x-dead-letter|DLQ|deadLetter" --glob "**/*.php"
```

## References

For detailed information, load these reference files:

- `references/rabbitmq-advanced.md` — Queue types, exchange topologies, clustering, monitoring, PHP patterns
- `references/kafka-advanced.md` — Partitioning, consumer groups, schema registry, exactly-once, PHP patterns
