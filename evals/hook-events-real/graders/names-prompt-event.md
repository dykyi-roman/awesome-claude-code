---
type: regex
pattern: "UserPromptSubmit"
match: contains
target: last_message
---

`UserPromptSubmit` is the real "before the prompt is processed" event. It appeared zero times
anywhere in this plugin before the v3.3.0 fixes, which is why it gets its own grader.
