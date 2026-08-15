---
type: regex
pattern: "0 ?== ?'admin' (is|evaluates to) true|'admin' ?== ?0 (is|evaluates to) true|integer 0 (would |will )?match(es)? (the string )?'admin'"
match: not_contains
target: last_message
---

PHP 8.0 reversed int-vs-non-numeric-string comparison: `0 == 'admin'` is **false**.
Claiming the pre-8.0 bypass on a PHP 8.4 codebase is a false positive and the exact
defect this eval guards against.
