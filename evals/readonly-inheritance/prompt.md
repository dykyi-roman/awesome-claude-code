---
name: "Generated decorator must compile on PHP 8.4"
tags: ["regression", "generator", "php8"]
runs: 3
max_turns: 8
timeout_seconds: 300
allowed_tools: ["Read", "Skill", "Grep", "Glob"]
---

Using the create-decorator skill, show me the complete code for a caching decorator over this
interface, including the abstract base class it extends:

```php
interface NotifierInterface
{
    public function send(string $to, string $message): void;
}
```

The decorator must keep an in-memory list of already-sent messages so it can skip duplicates
within one request.
