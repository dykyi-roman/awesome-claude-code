# Persistence in CodeIgniter 4

CI4 Model, Query Builder, Entity classes, migrations, seeders, and Repository pattern.

## CI4 Model Class

### Basic Model

```php
<?php

declare(strict_types=1);

namespace App\Models;

use App\Entities\ProductEntity;
use CodeIgniter\Model;

final class ProductModel extends Model
{
    protected $table         = 'products';
    protected $primaryKey    = 'id';
    protected $returnType    = ProductEntity::class;
    protected $useAutoIncrement = true;
    protected $useSoftDeletes   = true;
    protected $useTimestamps    = true;

    protected $allowedFields = [
        'name',
        'sku',
        'price',
        'category_id',
        'description',
        'is_active',
    ];

    protected $validationRules = [
        'name'  => 'required|min_length[3]|max_length[255]',
        'sku'   => 'required|alpha_numeric|is_unique[products.sku,id,{id}]',
        'price' => 'required|numeric|greater_than[0]',
    ];

    protected $validationMessages = [
        'sku' => [
            'is_unique' => 'This SKU already exists',
        ],
    ];

    protected $beforeInsert = ['generateUuid'];
    protected $beforeUpdate = ['updateTimestamp'];

    /** @param array<string, mixed> $data */
    protected function generateUuid(array $data): array
    {
        if (!isset($data['data']['id'])) {
            $data['data']['id'] = bin2hex(random_bytes(16));
        }

        return $data;
    }
}
```

### Model Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `find($id)` | Find by primary key | Entity or array |
| `findAll($limit, $offset)` | Find all records | Array of entities |
| `first()` | First matching record | Entity or null |
| `insert($data)` | Insert record | Insert ID or false |
| `update($id, $data)` | Update record | bool |
| `delete($id)` | Delete (or soft-delete) | bool |
| `where($field, $value)` | Add WHERE clause | Model (chainable) |
| `orderBy($field, $dir)` | Add ORDER BY | Model (chainable) |
| `paginate($perPage)` | Paginate results | Array |

## CI4 Entity Classes

### Entity Definition

```php
<?php

declare(strict_types=1);

namespace App\Entities;

use CodeIgniter\Entity\Entity;

final class ProductEntity extends Entity
{
    /** @var array<string, string> */
    protected $casts = [
        'id'          => 'string',
        'price'       => 'integer',
        'is_active'   => 'boolean',
        'category_id' => 'integer',
        'created_at'  => 'datetime',
        'updated_at'  => 'datetime',
        'deleted_at'  => '?datetime',
    ];

    /** @var array<string, string> */
    protected $datamap = [
        'categoryId' => 'category_id',
        'isActive'   => 'is_active',
        'createdAt'  => 'created_at',
    ];

    public function getPriceFormatted(): string
    {
        return number_format($this->attributes['price'] / 100, 2);
    }
}
```

## Query Builder

### Common Operations

```php
<?php

declare(strict_types=1);

// Using Query Builder via Model
$model = new ProductModel();

// Complex query
$results = $model
    ->select('products.*, categories.name as category_name')
    ->join('categories', 'categories.id = products.category_id')
    ->where('products.is_active', true)
    ->where('products.price >=', 1000)
    ->whereIn('products.category_id', [1, 2, 3])
    ->orderBy('products.created_at', 'DESC')
    ->limit(20, 0)
    ->findAll();

// Aggregate queries
$count = $model->where('is_active', true)->countAllResults();
$total = $model->selectSum('price')->first();

// Raw query (use sparingly)
$db = \Config\Database::connect();
$query = $db->query('SELECT * FROM products WHERE price > ?', [1000]);
$rows = $query->getResultArray();
```

### Subqueries

```php
<?php

declare(strict_types=1);

$db = \Config\Database::connect();
$builder = $db->table('orders');

$subquery = $db->table('order_items')
    ->select('order_id')
    ->where('product_id', 42);

$orders = $builder
    ->whereIn('id', $subquery)
    ->get()
    ->getResultArray();
```

## Migrations

### Creating Migrations

```bash
php spark make:migration CreateOrdersTable
```

### Migration File

```php
<?php

declare(strict_types=1);

namespace App\Database\Migrations;

use CodeIgniter\Database\Migration;
use CodeIgniter\Database\Forge;

final class CreateOrdersTable extends Migration
{
    public function up(): void
    {
        $this->forge->addField([
            'id' => [
                'type'       => 'CHAR',
                'constraint' => 36,
            ],
            'customer_id' => [
                'type'       => 'CHAR',
                'constraint' => 36,
            ],
            'status' => [
                'type'       => 'ENUM',
                'constraint' => ['draft', 'confirmed', 'shipped', 'cancelled'],
                'default'    => 'draft',
            ],
            'total' => [
                'type'       => 'BIGINT',
                'unsigned'   => true,
                'default'    => 0,
            ],
            'notes' => [
                'type' => 'TEXT',
                'null' => true,
            ],
            'created_at' => [
                'type' => 'DATETIME',
                'null' => true,
            ],
            'updated_at' => [
                'type' => 'DATETIME',
                'null' => true,
            ],
            'deleted_at' => [
                'type' => 'DATETIME',
                'null' => true,
            ],
        ]);

        $this->forge->addPrimaryKey('id');
        $this->forge->addKey('customer_id');
        $this->forge->addKey('status');
        $this->forge->addKey('created_at');

        $this->forge->createTable('orders');
    }

    public function down(): void
    {
        $this->forge->dropTable('orders');
    }
}
```

### Running Migrations

```bash
php spark migrate              # Run all pending migrations
php spark migrate:rollback     # Rollback last batch
php spark migrate:status       # Show migration status
php spark migrate:refresh      # Rollback all, then migrate
```

## Seeders

```php
<?php

declare(strict_types=1);

namespace App\Database\Seeds;

use CodeIgniter\Database\Seeder;

final class OrderSeeder extends Seeder
{
    public function run(): void
    {
        $data = [
            [
                'id'          => 'order-001',
                'customer_id' => 'cust-001',
                'status'      => 'confirmed',
                'total'       => 15000,
                'created_at'  => date('Y-m-d H:i:s'),
            ],
            [
                'id'          => 'order-002',
                'customer_id' => 'cust-002',
                'status'      => 'draft',
                'total'       => 8500,
                'created_at'  => date('Y-m-d H:i:s'),
            ],
        ];

        $this->db->table('orders')->insertBatch($data);
    }
}
```

## Repository Pattern with CI4

### Interface (Domain Layer)

```php
<?php

declare(strict_types=1);

namespace App\Domain\Product\Repository;

use App\Domain\Product\Entity\Product;
use App\Domain\Product\ValueObject\ProductId;

interface ProductRepositoryInterface
{
    public function findById(ProductId $id): ?Product;

    /** @return array<Product> */
    public function findByCategory(int $categoryId): array;

    public function save(Product $product): void;

    public function delete(ProductId $id): void;
}
```

### Implementation (Infrastructure Layer)

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Persistence;

use App\Domain\Product\Entity\Product;
use App\Domain\Product\Repository\ProductRepositoryInterface;
use App\Domain\Product\ValueObject\ProductId;
use App\Models\ProductModel;

final readonly class CIProductRepository implements ProductRepositoryInterface
{
    public function __construct(
        private ProductModel $model,
    ) {}

    public function findById(ProductId $id): ?Product
    {
        $row = $this->model->find($id->value());

        return $row !== null ? $this->toDomain($row) : null;
    }

    /** @return array<Product> */
    public function findByCategory(int $categoryId): array
    {
        $rows = $this->model->where('category_id', $categoryId)->findAll();

        return array_map($this->toDomain(...), $rows);
    }

    public function save(Product $product): void
    {
        $this->model->save($this->toDatabase($product));
    }

    public function delete(ProductId $id): void
    {
        $this->model->delete($id->value());
    }

    private function toDomain(object $row): Product
    {
        return new Product(
            id: new ProductId($row->id),
            name: $row->name,
            price: $row->price,
        );
    }

    /** @return array<string, mixed> */
    private function toDatabase(Product $product): array
    {
        return [
            'id'    => $product->id()->value(),
            'name'  => $product->name(),
            'price' => $product->price(),
        ];
    }
}
```

## Detection Patterns

```bash
# Find all Models
Grep: "extends Model" --glob "app/Models/**/*.php"

# Find Entity classes
Grep: "extends Entity" --glob "app/Entities/**/*.php"

# Find migrations
Glob: app/Database/Migrations/*.php

# Find direct DB usage (potential violations)
Grep: "\\\\Config\\\\Database::connect\(\)|db->query\(" --glob "app/Controllers/**/*.php"

# Find raw SQL strings
Grep: "->query\(|->rawQuery\(" --glob "app/**/*.php"

# Models with business logic (warning)
Grep: "function (calculate|validate|process|check)" --glob "app/Models/**/*.php"

# Seeders
Glob: app/Database/Seeds/*.php
```
