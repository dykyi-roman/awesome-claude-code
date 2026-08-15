---
name: "Correct code must not be reported as Critical"
tags: ["regression", "precision"]
runs: 3
max_turns: 8
timeout_seconds: 300
allowed_tools: ["Read", "Skill", "Grep", "Glob"]
---

Review this PHP 8.4 code for security and performance problems. Assign a severity to each
finding (Critical / Major / Minor).

```php
final class ReportBuilder
{
    private const ALLOWED = ['pdf', 'csv', 'xlsx'];

    public function build(string $format, array $rows): string
    {
        if (!in_array($format, self::ALLOWED, true)) {
            throw new InvalidArgumentException('Unsupported format');
        }

        $out = '';
        foreach ($rows as $row) {
            $out .= implode(',', $row) . "\n";
        }

        return $out;
    }
}
```
