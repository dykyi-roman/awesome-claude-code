# PHP-FIG Process

## What is PHP-FIG?

The **PHP Framework Interoperability Group (PHP-FIG)** is a group of PHP project representatives who develop and publish PHP Standards Recommendations (PSRs).

**Website:** https://www.php-fig.org/

## PSR Workflow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    Draft    │ ──► │   Review    │ ──► │   Accepted  │ ──► │ Deprecated  │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
      │                   │                                        │
      │                   │                                        │
      ▼                   ▼                                        ▼
 ┌─────────────┐    ┌─────────────┐                          ┌─────────────┐
 │  Abandoned  │    │   Abandoned │                          │   Replaced  │
 └─────────────┘    └─────────────┘                          └─────────────┘
```

## PSR Statuses

| Status | Description |
|--------|-------------|
| **Draft** | Under active development |
| **Review** | Ready for review by voting members |
| **Accepted** | Approved and final |
| **Deprecated** | No longer recommended |
| **Abandoned** | Discontinued |

## Current PSR Status

### Accepted PSRs

| PSR | Name | Status |
|-----|------|--------|
| PSR-1 | Basic Coding Standard | Accepted |
| PSR-3 | Logger Interface | Accepted |
| PSR-4 | Autoloader | Accepted |
| PSR-6 | Caching Interface | Accepted |
| PSR-7 | HTTP Message Interface | Accepted |
| PSR-11 | Container Interface | Accepted |
| PSR-12 | Extended Coding Style Guide | Accepted |
| PSR-13 | Hypermedia Links | Accepted |
| PSR-14 | Event Dispatcher | Accepted |
| PSR-15 | HTTP Handlers | Accepted |
| PSR-16 | Simple Cache | Accepted |
| PSR-17 | HTTP Factories | Accepted |
| PSR-18 | HTTP Client | Accepted |
| PSR-20 | Clock | Accepted |

### Deprecated PSRs

| PSR | Name | Replaced By |
|-----|------|-------------|
| PSR-0 | Autoloading Standard | PSR-4 |
| PSR-2 | Coding Style Guide | PSR-12 |

### Draft PSRs

| PSR | Name | Status |
|-----|------|--------|
| PSR-5 | PHPDoc Standard | Draft |
| PSR-19 | PHPDoc Tags | Draft |
| PSR-21 | Internationalization | Draft |
| PSR-22 | Application Tracing | Draft |

### Abandoned PSRs

| PSR | Name | Reason |
|-----|------|--------|
| PSR-8 | Huggable Interface | April Fools |
| PSR-9 | Security Advisories | Superseded |
| PSR-10 | Security Reporting | Superseded |

## How PSRs Are Created

### 1. Proposal (Pre-Draft)

- Anyone can propose a PSR
- Proposal must have:
  - Editor (main author)
  - Sponsor (voting member)
  - Clear problem statement
  - Proposed solution

### 2. Draft Phase

- Working group forms
- Specification is written
- Reference implementation created
- Community feedback gathered

### 3. Review Phase

- Specification finalized
- 2-week minimum review period
- Voting members can comment
- Changes require returning to Draft

### 4. Vote

- Requires 2/3 majority
- Minimum 10 votes
- 2-week voting period
- Accepted or returned to Draft

### 5. Acceptance

- Specification is final
- Implementation packages released
- Cannot be modified (only deprecated)

## Member Projects

Current voting members include:

- Symfony
- Laravel
- Laminas (formerly Zend)
- Drupal
- Joomla
- WordPress
- CakePHP
- Yii
- Slim
- PEAR
- phpDocumentor
- Composer
- PHPUnit
- And more...

## Contributing to PSRs

### As a Community Member

1. Read existing PSRs at https://www.php-fig.org/psr/
2. Join discussions on GitHub
3. Provide feedback during Review phase
4. Create implementations
5. Report issues with specifications

### As a Project Representative

1. Your project must be accepted as a member
2. Attend meetings
3. Vote on PSRs
4. Sponsor new PSRs

## Resources

### Official

- **Website:** https://www.php-fig.org/
- **GitHub:** https://github.com/php-fig
- **PSR List:** https://www.php-fig.org/psr/

### Packages

- **Interface Packages:** https://packagist.org/packages/psr/

### Documentation

- **Bylaws:** https://www.php-fig.org/bylaws/
- **Workflow:** https://www.php-fig.org/bylaws/psr-workflow/

## Timeline of Major PSRs

| Year | PSRs |
|------|------|
| 2012 | PSR-0 (Autoloading), PSR-1 (Basic), PSR-2 (Style) |
| 2013 | PSR-3 (Logger), PSR-4 (Autoloader) |
| 2015 | PSR-7 (HTTP Message) |
| 2016 | PSR-6 (Cache), PSR-11 (Container), PSR-13 (Link) |
| 2017 | PSR-15 (HTTP Handlers), PSR-16 (Simple Cache) |
| 2018 | PSR-14 (Events), PSR-17 (HTTP Factory), PSR-18 (HTTP Client) |
| 2019 | PSR-12 (Extended Style) |
| 2023 | PSR-20 (Clock) |

## Best Practices for Implementation

### Implementing PSR Interfaces

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Logger;

use Psr\Log\LoggerInterface;
use Psr\Log\LogLevel;
use Stringable;

// Implement the PSR interface
final readonly class FileLogger implements LoggerInterface
{
    public function __construct(
        private string $logFile,
    ) {
    }

    public function emergency(string|Stringable $message, array $context = []): void
    {
        $this->log(LogLevel::EMERGENCY, $message, $context);
    }

    // ... implement other methods

    public function log(mixed $level, string|Stringable $message, array $context = []): void
    {
        $formatted = $this->interpolate((string) $message, $context);
        file_put_contents($this->logFile, "[{$level}] {$formatted}\n", FILE_APPEND);
    }

    private function interpolate(string $message, array $context): string
    {
        $replace = [];
        foreach ($context as $key => $val) {
            $replace['{' . $key . '}'] = $val;
        }
        return strtr($message, $replace);
    }
}
```

### Type Declarations

Always use strict types and follow PSR-12:

```php
<?php

declare(strict_types=1);

// Required for PHP 8.0+ PSR packages
```

### Versioning

Follow semantic versioning for implementations:

```json
{
    "name": "vendor/psr-implementation",
    "require": {
        "psr/log": "^3.0"
    },
    "provide": {
        "psr/log-implementation": "3.0.0"
    }
}
```
