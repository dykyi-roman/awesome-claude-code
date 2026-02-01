# PSR-13 Link Templates

## HAL Resource

```php
<?php

declare(strict_types=1);

namespace App\Presentation\Api\Resource;

use JsonSerializable;
use Psr\Link\LinkInterface;
use Psr\Link\LinkProviderInterface;

abstract class HalResource implements JsonSerializable, LinkProviderInterface
{
    /** @var LinkInterface[] */
    protected array $links = [];

    /** @var array<string, HalResource|HalResource[]> */
    protected array $embedded = [];

    public function addLink(LinkInterface $link): void
    {
        $this->links[] = $link;
    }

    public function embed(string $rel, HalResource|array $resource): void
    {
        $this->embedded[$rel] = $resource;
    }

    public function getLinks(): iterable
    {
        return $this->links;
    }

    public function getLinksByRel(string $rel): iterable
    {
        foreach ($this->links as $link) {
            if (in_array($rel, $link->getRels(), true)) {
                yield $link;
            }
        }
    }

    abstract protected function getData(): array;

    public function jsonSerialize(): array
    {
        $data = $this->getData();

        // Add _links
        $links = [];
        foreach ($this->links as $link) {
            foreach ($link->getRels() as $rel) {
                $linkData = ['href' => $link->getHref()];

                if ($link->isTemplated()) {
                    $linkData['templated'] = true;
                }

                foreach ($link->getAttributes() as $name => $value) {
                    $linkData[$name] = $value;
                }

                $links[$rel] = $linkData;
            }
        }

        if (!empty($links)) {
            $data['_links'] = $links;
        }

        // Add _embedded
        if (!empty($this->embedded)) {
            $data['_embedded'] = array_map(
                fn($resource) => is_array($resource)
                    ? array_map(fn($r) => $r->jsonSerialize(), $resource)
                    : $resource->jsonSerialize(),
                $this->embedded,
            );
        }

        return $data;
    }
}
```

## Collection Resource

```php
<?php

declare(strict_types=1);

namespace App\Presentation\Api\Resource;

use App\Infrastructure\Http\Link\Link;

final class UserCollectionResource extends HalResource
{
    /** @param UserResource[] $users */
    public function __construct(
        private readonly array $users,
        private readonly int $page,
        private readonly int $limit,
        private readonly int $total,
    ) {
        $this->addLink((new Link('/api/users'))->withRel('self'));

        if ($page > 1) {
            $this->addLink(
                (new Link("/api/users?page=" . ($page - 1) . "&limit={$limit}"))
                    ->withRel('prev'),
            );
        }

        if ($page * $limit < $total) {
            $this->addLink(
                (new Link("/api/users?page=" . ($page + 1) . "&limit={$limit}"))
                    ->withRel('next'),
            );
        }

        $this->embed('users', $users);
    }

    protected function getData(): array
    {
        return [
            'page' => $this->page,
            'limit' => $this->limit,
            'total' => $this->total,
            'pages' => (int) ceil($this->total / $this->limit),
        ];
    }
}
```

## Link Serializer

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Http\Link;

use Psr\Link\LinkInterface;
use Psr\Link\LinkProviderInterface;

final readonly class LinkSerializer
{
    public function serializeProvider(LinkProviderInterface $provider): array
    {
        $links = [];

        foreach ($provider->getLinks() as $link) {
            foreach ($link->getRels() as $rel) {
                $links[$rel] = $this->serializeLink($link);
            }
        }

        return $links;
    }

    public function serializeLink(LinkInterface $link): array
    {
        $data = ['href' => $link->getHref()];

        if ($link->isTemplated()) {
            $data['templated'] = true;
        }

        foreach ($link->getAttributes() as $name => $value) {
            $data[$name] = $value;
        }

        return $data;
    }

    public function serializeToHeader(LinkProviderInterface $provider): string
    {
        $parts = [];

        foreach ($provider->getLinks() as $link) {
            $part = '<' . $link->getHref() . '>';

            foreach ($link->getRels() as $rel) {
                $part .= '; rel="' . $rel . '"';
            }

            foreach ($link->getAttributes() as $name => $value) {
                $part .= '; ' . $name . '="' . $value . '"';
            }

            $parts[] = $part;
        }

        return implode(', ', $parts);
    }
}
```
