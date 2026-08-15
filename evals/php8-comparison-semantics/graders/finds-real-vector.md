---
type: llm
criteria: "Does the response identify a bypass that is actually real on PHP 8 — a boolean true (e.g. from a JSON body) matching any non-empty string, or numeric-string coercion — and recommend strict comparison (=== or hash_equals)?"
focus: "Reject the answer if its only reasoning is the pre-PHP-8 'integer zero matches a string' behaviour, or if it reports no issue at all. The loose == is still a genuine defect on PHP 8; the answer must explain the right reason for it."
---

The skill should still flag `==` here — just for a reason that is true on PHP 8.
