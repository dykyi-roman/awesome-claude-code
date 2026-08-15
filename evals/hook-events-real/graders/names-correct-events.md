---
type: regex
pattern: "PostToolUseFailure"
match: contains
target: last_message
---

The real event for "a tool call failed" is `PostToolUseFailure`. The companion grader checks the
prompt half is answered with `UserPromptSubmit`.
