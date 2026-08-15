---
type: regex
pattern: "^\\s*(checkMissingIterableValueType|checkGenericClassInNonGenericObjectType|checkExplicitMixed|checkImplicitMixed)\\s*:"
match: not_contains
target: last_message
---

These parameters were removed in PHPStan 2.0. A generated config containing any of them aborts
immediately with `Unexpected item 'parameters › <name>'`, so the very first run fails.
