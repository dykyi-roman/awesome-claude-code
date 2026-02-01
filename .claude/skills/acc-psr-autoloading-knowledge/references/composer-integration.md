# Composer PSR-4 Integration

## Basic Configuration

### composer.json Structure

```json
{
    "name": "vendor/package",
    "autoload": {
        "psr-4": {
            "Vendor\\Package\\": "src/"
        }
    },
    "autoload-dev": {
        "psr-4": {
            "Vendor\\Package\\Tests\\": "tests/"
        }
    }
}
```

## Configuration Options

### Single Directory Mapping

```json
{
    "autoload": {
        "psr-4": {
            "App\\": "src/"
        }
    }
}
```

### Multiple Directories

```json
{
    "autoload": {
        "psr-4": {
            "App\\": ["src/", "lib/", "modules/"]
        }
    }
}
```

### Multiple Namespace Prefixes

```json
{
    "autoload": {
        "psr-4": {
            "App\\": "src/",
            "Vendor\\SharedKernel\\": "packages/shared-kernel/src/",
            "Vendor\\Utils\\": "packages/utils/src/"
        }
    }
}
```

### Empty Prefix (Fallback)

```json
{
    "autoload": {
        "psr-4": {
            "": "src/"
        }
    }
}
```

## Project Templates

### Standard PHP Project

```json
{
    "name": "company/project",
    "type": "project",
    "require": {
        "php": "^8.5"
    },
    "autoload": {
        "psr-4": {
            "App\\": "src/"
        }
    },
    "autoload-dev": {
        "psr-4": {
            "App\\Tests\\": "tests/"
        }
    }
}
```

### DDD Project

```json
{
    "name": "company/ddd-project",
    "type": "project",
    "require": {
        "php": "^8.5"
    },
    "autoload": {
        "psr-4": {
            "App\\": "src/",
            "App\\Domain\\": "src/Domain/",
            "App\\Application\\": "src/Application/",
            "App\\Infrastructure\\": "src/Infrastructure/",
            "App\\Presentation\\": "src/Presentation/"
        }
    },
    "autoload-dev": {
        "psr-4": {
            "App\\Tests\\": "tests/",
            "App\\Tests\\Unit\\": "tests/Unit/",
            "App\\Tests\\Integration\\": "tests/Integration/",
            "App\\Tests\\Functional\\": "tests/Functional/"
        }
    }
}
```

### Symfony Application

```json
{
    "name": "company/symfony-app",
    "type": "project",
    "require": {
        "php": "^8.5",
        "symfony/framework-bundle": "^7.0"
    },
    "autoload": {
        "psr-4": {
            "App\\": "src/"
        }
    },
    "autoload-dev": {
        "psr-4": {
            "App\\Tests\\": "tests/"
        }
    },
    "config": {
        "sort-packages": true
    }
}
```

### Laravel Package

```json
{
    "name": "vendor/laravel-package",
    "type": "library",
    "require": {
        "php": "^8.5",
        "illuminate/support": "^11.0"
    },
    "autoload": {
        "psr-4": {
            "Vendor\\Package\\": "src/"
        }
    },
    "autoload-dev": {
        "psr-4": {
            "Vendor\\Package\\Tests\\": "tests/"
        }
    },
    "extra": {
        "laravel": {
            "providers": [
                "Vendor\\Package\\PackageServiceProvider"
            ]
        }
    }
}
```

### Monorepo with Packages

```json
{
    "name": "company/monorepo",
    "type": "project",
    "autoload": {
        "psr-4": {
            "App\\": "app/src/",
            "Company\\Billing\\": "packages/billing/src/",
            "Company\\Shipping\\": "packages/shipping/src/",
            "Company\\SharedKernel\\": "packages/shared-kernel/src/"
        }
    },
    "autoload-dev": {
        "psr-4": {
            "App\\Tests\\": "app/tests/",
            "Company\\Billing\\Tests\\": "packages/billing/tests/",
            "Company\\Shipping\\Tests\\": "packages/shipping/tests/"
        }
    }
}
```

## Composer Commands

### Generate Autoload Files

```bash
# Basic autoload generation
composer dump-autoload

# Optimized autoload (class map)
composer dump-autoload --optimize

# Authoritative class map (fails on missing classes)
composer dump-autoload --classmap-authoritative

# Strict mode (shows warnings)
composer dump-autoload --strict

# Combined for production
composer dump-autoload --optimize --classmap-authoritative
```

### Validate Configuration

```bash
# Validate composer.json
composer validate

# Strict validation
composer validate --strict

# Check dependencies
composer check-platform-reqs
```

### Debug Autoloading

```bash
# Show autoload configuration
composer show -s

# Show installed packages with autoload
composer show -i

# Find where a class is loaded from
composer show -p
```

## Generated Files

After `composer dump-autoload`, Composer generates:

```
vendor/
├── autoload.php                    # Main autoloader entry point
└── composer/
    ├── autoload_classmap.php       # Class map (when optimized)
    ├── autoload_files.php          # Files to include
    ├── autoload_namespaces.php     # PSR-0 namespaces
    ├── autoload_psr4.php           # PSR-4 mappings
    ├── autoload_real.php           # Real autoloader
    ├── autoload_static.php         # Static autoloader (optimized)
    ├── ClassLoader.php             # ClassLoader implementation
    └── installed.json              # Installed packages
```

### autoload_psr4.php Example

```php
<?php

// autoload_psr4.php @generated by Composer

$vendorDir = dirname(__DIR__);
$baseDir = dirname($vendorDir);

return array(
    'App\\Tests\\' => array($baseDir . '/tests'),
    'App\\' => array($baseDir . '/src'),
);
```

## Optimization Strategies

### Development

```json
{
    "config": {
        "optimize-autoloader": false
    }
}
```

### Production

```json
{
    "config": {
        "optimize-autoloader": true,
        "classmap-authoritative": true
    }
}
```

### CI/CD

```bash
# Development
composer install --prefer-dist

# Production
composer install --no-dev --optimize-autoloader --classmap-authoritative
```

## Troubleshooting

### Class Not Found

```bash
# Regenerate autoload
composer dump-autoload

# Check if namespace matches path
grep -r "namespace App" src/

# Verify file exists
ls -la src/Domain/User/Entity/User.php
```

### Performance Issues

```bash
# Generate optimized autoloader
composer dump-autoload --optimize

# Check generated classmap
cat vendor/composer/autoload_classmap.php | head -50
```

### Namespace Conflicts

```bash
# Find duplicate class definitions
grep -rh "^class\|^interface\|^trait\|^enum" src/ | sort | uniq -d
```
