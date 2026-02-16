# README Patterns

## Standard Structure

```markdown
# Project Name

[![Build](badge-url)](ci-url)
[![Coverage](badge-url)](coverage-url)
[![Version](badge-url)](releases-url)
[![License](badge-url)](license-url)

One-line description of what the project does.

## Features

- ✅ Feature 1 with brief benefit
- ✅ Feature 2 with brief benefit
- ✅ Feature 3 with brief benefit

## Requirements

- PHP 8.4+
- Composer 2.0+
- ext-json

## Installation

```bash
composer require vendor/package
```

## Quick Start

```php
<?php

use Vendor\Package\MainClass;

$instance = new MainClass();
$result = $instance->doSomething('input');

echo $result; // Expected output
```

## Documentation

- [Getting Started](docs/getting-started.md)
- [Configuration](docs/configuration.md)
- [API Reference](docs/api/README.md)
- [Examples](docs/examples/)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

## License

MIT License - see [LICENSE](LICENSE) for details.
```

## Badge Examples

### Shields.io Badges

```markdown
# Build Status
[![CI](https://github.com/owner/repo/actions/workflows/ci.yml/badge.svg)](https://github.com/owner/repo/actions)

# Coverage
[![Coverage](https://codecov.io/gh/owner/repo/branch/main/graph/badge.svg)](https://codecov.io/gh/owner/repo)

# Version
[![Packagist](https://img.shields.io/packagist/v/vendor/package.svg)](https://packagist.org/packages/vendor/package)

# PHP Version
[![PHP](https://img.shields.io/packagist/php-v/vendor/package.svg)](https://packagist.org/packages/vendor/package)

# License
[![License](https://img.shields.io/github/license/owner/repo.svg)](LICENSE)

# Downloads
[![Downloads](https://img.shields.io/packagist/dt/vendor/package.svg)](https://packagist.org/packages/vendor/package)
```

## Feature Section Patterns

### Checklist Style

```markdown
## Features

- ✅ Type-safe configuration
- ✅ PSR-7 compatible
- ✅ Zero dependencies
- ✅ PHP 8.4+ support
- 🚧 Feature in progress
```

### Comparison Table

```markdown
## Why This Library?

| Feature | This | Alternative A | Alternative B |
|---------|------|---------------|---------------|
| PHP 8.4 | ✅ | ❌ | ✅ |
| Type Safety | ✅ | ⚠️ | ❌ |
| Zero Deps | ✅ | ❌ | ❌ |
| Performance | Fast | Slow | Medium |
```

## Installation Patterns

### Composer Only

```markdown
## Installation

```bash
composer require vendor/package
```
```

### With Configuration

```markdown
## Installation

1. Install via Composer:

```bash
composer require vendor/package
```

2. Copy configuration (optional):

```bash
cp vendor/vendor/package/config/config.php config/package.php
```

3. Register service provider (if using framework):

```php
// config/app.php
'providers' => [
    Vendor\Package\ServiceProvider::class,
],
```
```

## Usage Examples

### Minimal Example

```markdown
## Quick Start

```php
<?php

use Vendor\Package\Client;

$client = new Client();
$result = $client->process('data');
```
```

### Complete Example

```markdown
## Usage

### Basic Usage

```php
<?php

declare(strict_types=1);

use Vendor\Package\Client;
use Vendor\Package\Config;

$config = new Config(
    apiKey: 'your-api-key',
    timeout: 30
);

$client = new Client($config);
$result = $client->process('data');

echo $result->status; // "success"
```

### Advanced Usage

```php
// With custom options
$result = $client->process(
    data: 'input',
    options: ['retry' => 3]
);
```
```

## Section Order Recommendation

1. Title + Badges
2. Description
3. Features
4. Requirements
5. Installation
6. Quick Start
7. Documentation links
8. Contributing
9. Changelog
10. License
