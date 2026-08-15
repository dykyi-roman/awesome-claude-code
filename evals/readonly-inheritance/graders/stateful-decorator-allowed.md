---
type: llm
criteria: "The prompt asked for a decorator that keeps an in-memory list of sent messages — i.e. mutable state. Does the generated decorator actually hold that state in a mutable property, and is the class NOT declared readonly?"
focus: "Fail if the decorator is declared readonly while also mutating a property (impossible — readonly forbids it), or if the model silently dropped the deduplication requirement to keep the class readonly. Immutability on the injected `$wrapped` dependency is fine and expected; immutability on the whole class is not, for this request."
---

The immutability rule must not be applied so aggressively that stateful decorators
(Retry, CircuitBreaker, dedup caches) become ungeneratable.
