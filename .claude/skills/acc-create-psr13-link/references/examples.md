# PSR-13 Link Examples

## REST API Controller

```php
<?php

declare(strict_types=1);

namespace App\Presentation\Api\Controller;

use App\Presentation\Api\Resource\UserCollectionResource;
use App\Presentation\Api\Resource\UserResource;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;

final readonly class UserController
{
    public function index(ServerRequestInterface $request): ResponseInterface
    {
        $page = (int) ($request->getQueryParams()['page'] ?? 1);
        $limit = (int) ($request->getQueryParams()['limit'] ?? 10);

        $users = $this->userRepository->findAll($page, $limit);
        $total = $this->userRepository->count();

        $resources = array_map(
            fn($user) => UserResource::fromEntity($user),
            $users,
        );

        $collection = new UserCollectionResource($resources, $page, $limit, $total);

        return $this->json($collection);
    }

    public function show(ServerRequestInterface $request): ResponseInterface
    {
        $id = $request->getAttribute('id');
        $user = $this->userRepository->findById($id);

        if ($user === null) {
            return $this->notFound();
        }

        $resource = UserResource::fromEntity($user);

        return $this->json($resource);
    }
}
```

## Link Header Response

```php
<?php

use App\Infrastructure\Http\Link\Link;
use App\Infrastructure\Http\Link\LinkProvider;
use App\Infrastructure\Http\Link\LinkSerializer;

$provider = (new LinkProvider())
    ->withLink((new Link('/api/users?page=2'))->withRel('next'))
    ->withLink((new Link('/api/users?page=10'))->withRel('last'));

$serializer = new LinkSerializer();
$headerValue = $serializer->serializeToHeader($provider);

$response = $response->withHeader('Link', $headerValue);
// Link: </api/users?page=2>; rel="next", </api/users?page=10>; rel="last"
```

## JSON API Response

```json
{
    "id": "123",
    "email": "john@example.com",
    "name": "John Doe",
    "_links": {
        "self": {
            "href": "/api/users/123"
        },
        "posts": {
            "href": "/api/users/123/posts"
        },
        "collection": {
            "href": "/api/users"
        }
    }
}
```
