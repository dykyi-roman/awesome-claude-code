---
name: "Type-juggling advice must match PHP 8 semantics"
tags: ["regression", "security", "php8"]
runs: 3
max_turns: 6
timeout_seconds: 240
allowed_tools: ["Read", "Skill", "Grep", "Glob"]
---

I have this PHP 8.4 controller:

```php
public function updateRole(Request $request): Response
{
    $role = $request->get('role');

    if ($role == 'admin') {
        $this->promote();
    }

    return new Response();
}
```

Audit this for type juggling vulnerabilities. For every issue you report, state precisely
what value of `$role` triggers the bypass and why the comparison evaluates to true.
