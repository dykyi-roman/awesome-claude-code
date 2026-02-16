# Chain of Responsibility Pattern Templates

## Handler Interface

**File:** `src/Domain/{BoundedContext}/Handler/{Name}HandlerInterface.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext}\Handler;

interface {Name}HandlerInterface
{
    public function setNext(self $handler): self;

    public function handle({RequestType} $request): {ResultType};
}
```

---

## Abstract Handler

**File:** `src/Domain/{BoundedContext}/Handler/Abstract{Name}Handler.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext}\Handler;

abstract class Abstract{Name}Handler implements {Name}HandlerInterface
{
    private ?{Name}HandlerInterface $next = null;

    public function setNext({Name}HandlerInterface $handler): {Name}HandlerInterface
    {
        $this->next = $handler;
        return $handler;
    }

    public function handle({RequestType} $request): {ResultType}
    {
        if ($this->next !== null) {
            return $this->next->handle($request);
        }

        return $this->getDefaultResult();
    }

    abstract protected function getDefaultResult(): {ResultType};
}
```

---

## Concrete Handler

**File:** `src/Domain/{BoundedContext}/Handler/{Name}Handler.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext}\Handler;

final class {Name}Handler extends Abstract{Name}Handler
{
    public function handle({RequestType} $request): {ResultType}
    {
        if ($this->canHandle($request)) {
            return $this->process($request);
        }

        return parent::handle($request);
    }

    private function canHandle({RequestType} $request): bool
    {
        return {condition};
    }

    private function process({RequestType} $request): {ResultType}
    {
        {processing}
    }

    protected function getDefaultResult(): {ResultType}
    {
        return {defaultResult};
    }
}
```

---

## Handler Chain Builder

**File:** `src/Domain/{BoundedContext}/Handler/{Name}ChainBuilder.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext}\Handler;

final class {Name}ChainBuilder
{
    /** @var array<{Name}HandlerInterface> */
    private array $handlers = [];

    public function add({Name}HandlerInterface $handler): self
    {
        $this->handlers[] = $handler;
        return $this;
    }

    public function build(): {Name}HandlerInterface
    {
        if ($this->handlers === []) {
            throw new \LogicException('Chain must have at least one handler');
        }

        $first = $this->handlers[0];
        $current = $first;

        for ($i = 1; $i < count($this->handlers); $i++) {
            $current = $current->setNext($this->handlers[$i]);
        }

        return $first;
    }
}
```

---

## Validation Handler Interface

**File:** `src/Domain/Validation/Handler/ValidationHandlerInterface.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Validation\Handler;

use Domain\Validation\ValueObject\ValidationRequest;
use Domain\Validation\ValueObject\ValidationResult;

interface ValidationHandlerInterface
{
    public function setNext(self $handler): self;

    public function validate(ValidationRequest $request): ValidationResult;
}
```

---

## Abstract Validation Handler

**File:** `src/Domain/Validation/Handler/AbstractValidationHandler.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Validation\Handler;

use Domain\Validation\ValueObject\ValidationRequest;
use Domain\Validation\ValueObject\ValidationResult;

abstract class AbstractValidationHandler implements ValidationHandlerInterface
{
    private ?ValidationHandlerInterface $next = null;

    public function setNext(ValidationHandlerInterface $handler): ValidationHandlerInterface
    {
        $this->next = $handler;
        return $handler;
    }

    public function validate(ValidationRequest $request): ValidationResult
    {
        $result = $this->doValidate($request);

        if ($result->hasErrors()) {
            return $result;
        }

        if ($this->next !== null) {
            return $this->next->validate($request);
        }

        return ValidationResult::valid();
    }

    abstract protected function doValidate(ValidationRequest $request): ValidationResult;
}
```

---

## Middleware-Style Pipeline

**File:** `src/Application/Pipeline/PipelineInterface.php`

```php
<?php

declare(strict_types=1);

namespace Application\Pipeline;

interface PipelineInterface
{
    public function pipe(callable $middleware): self;

    public function process(mixed $payload): mixed;
}
```

**File:** `src/Application/Pipeline/Pipeline.php`

```php
<?php

declare(strict_types=1);

namespace Application\Pipeline;

final class Pipeline implements PipelineInterface
{
    /** @var array<callable> */
    private array $middlewares = [];

    public function pipe(callable $middleware): self
    {
        $this->middlewares[] = $middleware;
        return $this;
    }

    public function process(mixed $payload): mixed
    {
        $middlewares = array_reverse($this->middlewares);

        $next = fn(mixed $p) => $p;

        foreach ($middlewares as $middleware) {
            $next = fn(mixed $p) => $middleware($p, $next);
        }

        return $next($payload);
    }
}
```

**File:** `src/Application/Pipeline/LoggingMiddleware.php`

```php
<?php

declare(strict_types=1);

namespace Application\Pipeline;

use Psr\Log\LoggerInterface;

final readonly class LoggingMiddleware
{
    public function __construct(
        private LoggerInterface $logger
    ) {}

    public function __invoke(mixed $payload, callable $next): mixed
    {
        $this->logger->info('Processing started', ['payload' => $payload]);

        $result = $next($payload);

        $this->logger->info('Processing completed', ['result' => $result]);

        return $result;
    }
}
```
