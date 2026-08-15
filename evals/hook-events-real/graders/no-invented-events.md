---
type: regex
pattern: "ToolError|PreUserInput|PostUserInput"
match: not_contains
target: last_message
---

None of these hook events exist. `claude plugin validate` rejects them with
`hooks.<Name>: Invalid key in record`, and at runtime a hook registered under an invented
name silently never fires — the worst possible failure mode, because there is no error to debug.

Note: the response may legitimately mention them if it is explicitly warning that they do not
exist. If that turns out to cause false failures, narrow this pattern rather than deleting it.
