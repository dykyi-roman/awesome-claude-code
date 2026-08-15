---
type: regex
pattern: "O\\(n²\\)|O\\(n\\^2\\)|quadratic"
match: not_contains
target: last_message
---

`$out .= …` in a loop is amortised O(1) in PHP — the string is reallocated in place while its
refcount is 1. Calling this quadratic is the false positive this eval guards against.
