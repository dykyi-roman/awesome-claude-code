# Test Data Builder Templates

## Builder Template

```php
<?php

declare(strict_types=1);

namespace Tests\Builder;

use {FullyQualifiedClassName};

final class {ClassName}Builder
{
    private {IdType} $id;
    private {Property1Type} ${property1};
    private {Property2Type} ${property2};
    // ... other properties

    private function __construct()
    {
        // Sensible defaults
        $this->id = {IdType}::generate();
        $this->{property1} = {default1};
        $this->{property2} = {default2};
    }

    public static function a{ClassName}(): self
    {
        return new self();
    }

    public static function an{ClassName}(): self
    {
        return new self();
    }

    public function withId({IdType} $id): self
    {
        $clone = clone $this;
        $clone->id = $id;
        return $clone;
    }

    public function with{Property1}({Property1Type} ${property1}): self
    {
        $clone = clone $this;
        $clone->{property1} = ${property1};
        return $clone;
    }

    public function with{Property2}({Property2Type} ${property2}): self
    {
        $clone = clone $this;
        $clone->{property2} = ${property2};
        return $clone;
    }

    public function build(): {ClassName}
    {
        return new {ClassName}(
            $this->id,
            $this->{property1},
            $this->{property2}
        );
    }
}
```

## Object Mother Template

```php
<?php

declare(strict_types=1);

namespace Tests\Mother;

use {FullyQualifiedClassName};

final class {ClassName}Mother
{
    public static function default(): {ClassName}
    {
        return {ClassName}Builder::a{ClassName}()->build();
    }

    public static function {scenario1}(): {ClassName}
    {
        return {ClassName}Builder::a{ClassName}()
            ->with{Property}({value})
            ->build();
    }

    public static function {scenario2}(): {ClassName}
    {
        return {ClassName}Builder::a{ClassName}()
            ->with{Property1}({value1})
            ->with{Property2}({value2})
            ->build();
    }
}
```
