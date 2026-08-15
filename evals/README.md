# Evals

Behavioural regression tests for the plugin, run with `claude plugin eval`.

Every case here exists because a real defect shipped. Static checks
(`make validate-claude`, `make test-regressions`) verify that the *source* no longer contains a
bad pattern; these evals verify the *behaviour* — that the model, having read our skills, does
not produce the bad output. Both are needed: a defect can return through phrasing that no grep
anticipated.

## Running

```bash
claude plugin eval .                                   # everything, 2-3 runs per case
claude plugin eval . --tag smoke --runs 1              # fast subset for PR CI
claude plugin eval . --case 'readonly-*'               # one case
claude plugin eval . --json results.json --report report.html
claude plugin eval acc --ablation with-without         # score delta vs no plugin at all
```

Exit code is 0 when every case meets `--threshold` (default 1.0).

> **Availability:** `claude plugin eval` is in early access. On an account without it enabled the
> command prints `` `plugin eval` is currently in early access `` and exits 1. These cases were
> authored against the documented case format and have **not yet been executed** — treat the first
> real run as part of enabling the feature, and expect to tune grader patterns then.

## Layout

```
evals/<case-name>/
├── prompt.md          # frontmatter (name, tags, runs, max_turns, allowed_tools) + the prompt
└── graders/*.md       # one grader per file: type regex | llm | tool_used
```

## Cases

| Case | Guards against | Tags |
|------|----------------|------|
| `php8-comparison-semantics` | Reporting the pre-PHP-8 `0 == 'admin'` bypass, which is false since 8.0 | regression, security |
| `readonly-inheritance` | Emitting `final readonly class … extends` a non-readonly base (fatal error), and over-applying readonly so stateful decorators become ungeneratable | regression, generator |
| `phpstan-config-valid` | Generating parameters removed in PHPStan 2.0 | regression, ci |
| `hook-events-real` | Inventing `ToolError` / `PreUserInput` / `PostUserInput` instead of the real events | regression, meta, smoke |
| `no-false-critical` | Manufacturing Critical findings on correct code (`.=` in a loop, strict `in_array`) | regression, precision |
| `delegation-fires` | A command inlining analysis instead of delegating to its agent | smoke, wiring |

## Not yet covered

- **Audit level** (`quick` vs `deep`): no case yet, because no agent currently honours the level —
  the test would encode today's broken behaviour. Add it together with the stage-5 fix, asserting
  a lower `Task` call count for `quick` via a `tool_used` grader with `max`.

## Adding a case

Anchor each new case to a defect that actually shipped, and say which one in the grader body.
Prefer a `regex` grader when the failure is a literal string (a removed config key, an invented
identifier) and an `llm` grader when it is a judgement (severity inflation, "does this compile").
Keep `runs` at 2-3: a single run makes a flaky grader indistinguishable from a real regression.
