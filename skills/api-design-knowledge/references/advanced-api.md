# Advanced API Patterns Reference

## Cursor-Based Pagination for High-Load

### Offset vs Cursor Comparison

| Aspect | Offset-Based | Cursor-Based |
|--------|-------------|--------------|
| URL | `?page=5&per_page=20` | `?cursor=abc123&limit=20` |
| Performance at scale | Degrades (OFFSET N) | Constant (WHERE id > X) |
| Consistency | Misses/duplicates on insert | Stable, no gaps |
| Random page access | Yes (go to page 50) | No (sequential only) |
| Total count | Easy (`COUNT(*)`) | Expensive or unavailable |
| Use case | Admin panels, small data | Feeds, large datasets |

### PHP Cursor Pagination Implementation

```php
<?php

declare(strict_types=1);

namespace Pagination;

final readonly class CursorPaginator
{
    public function __construct(
        private \PDO $pdo,
    ) {}

    /**
     * @return CursorPage<array>
     */
    public function paginate(
        string $table,
        ?string $cursor,
        int $limit = 20,
        string $orderColumn = 'id',
        string $direction = 'ASC',
    ): CursorPage {
        $params = [];
        $where = '';

        if ($cursor !== null) {
            $decodedCursor = $this->decodeCursor($cursor);
            $operator = $direction === 'ASC' ? '>' : '<';
            $where = sprintf('WHERE %s %s :cursor_value', $orderColumn, $operator);
            $params['cursor_value'] = $decodedCursor;
        }

        $sql = sprintf(
            'SELECT * FROM %s %s ORDER BY %s %s LIMIT :limit',
            $table,
            $where,
            $orderColumn,
            $direction,
        );

        $stmt = $this->pdo->prepare($sql);
        $stmt->bindValue('limit', $limit + 1, \PDO::PARAM_INT);
        foreach ($params as $key => $value) {
            $stmt->bindValue($key, $value);
        }
        $stmt->execute();

        $items = $stmt->fetchAll(\PDO::FETCH_ASSOC);
        $hasMore = count($items) > $limit;

        if ($hasMore) {
            array_pop($items);
        }

        $nextCursor = $hasMore && !empty($items)
            ? $this->encodeCursor($items[array_key_last($items)][$orderColumn])
            : null;

        return new CursorPage(
            items: $items,
            nextCursor: $nextCursor,
            hasMore: $hasMore,
        );
    }

    private function encodeCursor(mixed $value): string
    {
        return base64_encode((string) $value);
    }

    private function decodeCursor(string $cursor): string
    {
        return base64_decode($cursor, true) ?: throw new \InvalidArgumentException('Invalid cursor');
    }
}
```

### Cursor Page Response

```php
<?php

declare(strict_types=1);

namespace Pagination;

/**
 * @template T
 */
final readonly class CursorPage
{
    /**
     * @param list<T> $items
     */
    public function __construct(
        public array $items,
        public ?string $nextCursor,
        public bool $hasMore,
    ) {}

    public function toArray(): array
    {
        return [
            'data' => $this->items,
            'pagination' => [
                'next_cursor' => $this->nextCursor,
                'has_more' => $this->hasMore,
            ],
        ];
    }
}
```

## API Rate Limiting at Application Level

### Token Bucket Algorithm

```php
<?php

declare(strict_types=1);

namespace RateLimiting;

final readonly class RedisTokenBucket
{
    public function __construct(
        private \Redis $redis,
    ) {}

    public function attempt(string $key, int $maxTokens, int $refillRate, int $windowSeconds): RateLimitResult
    {
        $luaScript = <<<'LUA'
        local key = KEYS[1]
        local max_tokens = tonumber(ARGV[1])
        local refill_rate = tonumber(ARGV[2])
        local now = tonumber(ARGV[3])
        local window = tonumber(ARGV[4])

        local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
        local tokens = tonumber(bucket[1]) or max_tokens
        local last_refill = tonumber(bucket[2]) or now

        local elapsed = now - last_refill
        tokens = math.min(max_tokens, tokens + elapsed * refill_rate)

        local allowed = 0
        if tokens >= 1 then
            tokens = tokens - 1
            allowed = 1
        end

        redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
        redis.call('EXPIRE', key, window)

        return {allowed, math.ceil(tokens), math.ceil((1 - tokens) / refill_rate)}
        LUA;

        $result = $this->redis->eval(
            $luaScript,
            [$key, $maxTokens, $refillRate, time(), $windowSeconds],
            1,
        );

        return new RateLimitResult(
            allowed: (bool) $result[0],
            remainingTokens: (int) $result[1],
            retryAfterSeconds: $result[0] ? 0 : (int) $result[2],
        );
    }
}
```

### Sliding Window Counter

```php
<?php

declare(strict_types=1);

namespace RateLimiting;

final readonly class RedisSlidingWindow
{
    public function __construct(
        private \Redis $redis,
    ) {}

    public function attempt(string $key, int $limit, int $windowSeconds): RateLimitResult
    {
        $now = microtime(true);
        $windowStart = $now - $windowSeconds;

        $pipe = $this->redis->multi(\Redis::PIPELINE);
        $pipe->zRemRangeByScore($key, '-inf', (string) $windowStart);
        $pipe->zAdd($key, $now, (string) $now . ':' . random_int(0, PHP_INT_MAX));
        $pipe->zCard($key);
        $pipe->expire($key, $windowSeconds);
        $results = $pipe->exec();

        $count = (int) $results[2];
        $allowed = $count <= $limit;

        if (!$allowed) {
            $this->redis->zRemRangeByRank($key, -1, -1);
        }

        return new RateLimitResult(
            allowed: $allowed,
            remainingTokens: max(0, $limit - $count),
            retryAfterSeconds: $allowed ? 0 : $windowSeconds,
        );
    }
}
```

### Rate Limit Headers

| Header | Value | Example |
|--------|-------|---------|
| `X-RateLimit-Limit` | Max requests per window | `100` |
| `X-RateLimit-Remaining` | Remaining requests | `87` |
| `X-RateLimit-Reset` | Window reset timestamp | `1640000000` |
| `Retry-After` | Seconds to wait (on 429) | `30` |

## gRPC Integration for PHP

### PHP gRPC Client Setup

```php
<?php

declare(strict_types=1);

namespace Grpc;

final readonly class GrpcServiceClient
{
    private \Grpc\ChannelCredentials $credentials;

    public function __construct(
        private string $host,
        private int $port,
        private int $timeoutMs = 5000,
    ) {
        $this->credentials = \Grpc\ChannelCredentials::createInsecure();
    }

    public function call(string $method, mixed $request): mixed
    {
        $client = new \Grpc\BaseStub(
            sprintf('%s:%d', $this->host, $this->port),
            ['credentials' => $this->credentials],
        );

        [$response, $status] = $client->_simpleRequest(
            $method,
            $request,
            [],
            ['timeout' => $this->timeoutMs * 1000],
        )->wait();

        if ($status->code !== \Grpc\STATUS_OK) {
            throw new GrpcException($status->details, $status->code);
        }

        return $response;
    }
}
```

### REST vs gRPC Decision Matrix for PHP

| Factor | Choose REST | Choose gRPC |
|--------|-------------|-------------|
| Client type | Browser, mobile, third-party | Internal services |
| Payload size | Small-medium JSON | Large binary data |
| Streaming | Not needed | Real-time updates |
| Schema enforcement | Flexible | Strict contracts |
| PHP ecosystem | Mature (Symfony, Laravel) | Limited (ext-grpc) |
| Debugging | Easy (curl, Postman) | Requires special tools |

## GraphQL N+1 Considerations

### The Problem

```graphql
query {
    orders(first: 10) {    # 1 query for orders
        customer {          # N queries for customers (one per order)
            name
        }
        items {             # N queries for items
            product { name }# N*M queries for products
        }
    }
}
```

### PHP DataLoader Solution

```php
<?php

declare(strict_types=1);

namespace GraphQL;

final class DataLoader
{
    /** @var array<string, list<string>> */
    private array $pending = [];

    /** @var array<string, mixed> */
    private array $cache = [];

    public function __construct(
        private readonly \Closure $batchLoader,
    ) {}

    public function load(string $key): mixed
    {
        if (isset($this->cache[$key])) {
            return $this->cache[$key];
        }

        $this->pending[] = $key;
        return null;
    }

    public function dispatch(): void
    {
        if (empty($this->pending)) {
            return;
        }

        $keys = array_unique($this->pending);
        $this->pending = [];

        $results = ($this->batchLoader)($keys);

        foreach ($results as $key => $value) {
            $this->cache[$key] = $value;
        }
    }
}
```

### GraphQL PHP Best Practices

| Practice | Description |
|----------|-------------|
| Use DataLoader | Batch and cache DB queries per request |
| Limit query depth | Prevent deeply nested queries (max 5-7 levels) |
| Limit query complexity | Assign cost per field, reject expensive queries |
| Persist queries | Store allowed queries, reject unknown |
| Paginate connections | Always use cursor-based pagination |
