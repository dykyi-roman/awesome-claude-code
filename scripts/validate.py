#!/usr/bin/env python3
"""
Structural and regression validator for the acc plugin.

`claude plugin validate --strict` covers manifest syntax, unknown plugin.json fields and
unknown hook-event names. It was measured NOT to catch any of the following, which is why
this script exists:

    - model: <nonsense>            passes
    - empty description            passes
    - skills: <missing-skill>      passes
    - name != filename             passes
    - permissionMode: <nonsense>   passes

Run both:  make validate-claude

Exit code 0 = clean, 1 = at least one error. Warnings alone do not fail unless --strict.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

VALID_MODELS = {"haiku", "sonnet", "opus", "inherit"}
MAX_SKILL_LINES = 500
MAX_SKILLS_PER_AGENT = 15
MAX_DESCRIPTION_CHARS = 1024

# Hook events verified against Claude Code 2.1.233 by feeding each name to
# `claude plugin validate`, which rejects an unknown one as "Invalid key in record".
VALID_HOOK_EVENTS = {
    "PreToolUse", "PostToolUse", "PostToolUseFailure", "PostToolBatch",
    "PermissionRequest", "PermissionDenied",
    "UserPromptSubmit", "UserPromptExpansion", "Stop", "StopFailure",
    "SubagentStart", "SubagentStop", "TeammateIdle", "TaskCreated", "TaskCompleted",
    "SessionStart", "SessionEnd", "Setup",
    "PreCompact", "PostCompact", "Notification", "MessageDisplay",
    "FileChanged", "CwdChanged", "DirectoryAdded", "ConfigChange", "InstructionsLoaded",
    "WorktreeCreate", "WorktreeRemove",
    "Elicitation", "ElicitationResult",
}

# Each entry: (regex, human explanation). These are defects that actually shipped.
BANNED_PATTERNS = [
    (r"O\(n²\):\s*String concatenation",
     "`.=` in a loop is amortised O(1) in PHP, not quadratic"),
    (r"checkMissingIterableValueType|checkGenericClassInNonGenericObjectType",
     "removed in PHPStan 2.0 — the generated config aborts on first run"),
    (r"implements\s+\\?Cloneable",
     "there is no Cloneable interface in PHP; cloning uses __clone()"),
    (r"clear_env\s*=\s*yes",
     "in a container this wipes the inherited environment, so -e / compose env vars never reach the workers"),
    (r"Integer division loses precision",
     "PHP's / returns float; intdiv() is the truncating one"),
    (r"'[A-Za-z][^']*'\s*==\s*0 is true|0\s*==\s*'[A-Za-z][^']*' is true",
     "PHP 8 compares an int with a non-numeric string AS A STRING — this is false since 8.0"),
    (r"(public|private|protected)\s+\??callable\s+\$",
     "PHP forbids `callable` as a property type; use ?\\Closure"),
    (r"\breadonly class\s+[\w{}]+\s+extends\b",
     "checked separately for a non-readonly parent — see check_readonly_inheritance"),
]

# Invented hook events that must never be recommended.
INVENTED_HOOK_EVENTS = {
    "ToolError": "PostToolUseFailure",
    "PreUserInput": "UserPromptSubmit",
    "PostUserInput": "Stop",
}


class Report:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def error(self, where, msg):
        self.errors.append((where, msg))

    def warn(self, where, msg):
        self.warnings.append((where, msg))

    def render(self, strict):
        for where, msg in self.errors:
            print(f"  \033[0;31m✘\033[0m {where}\n      {msg}")
        for where, msg in self.warnings:
            print(f"  \033[0;33m⚠\033[0m {where}\n      {msg}")
        if not self.errors and not self.warnings:
            print("  \033[0;32m✓\033[0m no issues")
        return 1 if (self.errors or (strict and self.warnings)) else 0


def parse_frontmatter(path):
    """Return (dict, body, error_or_None). Only the flat `key: value` shape used here."""
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---"):
        return None, text, "file does not start with '---' (no frontmatter)"
    end = text.find("\n---", 3)
    if end == -1:
        return None, text, "frontmatter is not terminated by a closing '---'"
    raw = text[3:end]
    body = text[end + 4:]
    fm = {}
    for line in raw.splitlines():
        line = line.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = re.match(r"^([A-Za-z][\w-]*)\s*:\s*(.*)$", line)
        if m:
            fm[m.group(1)] = m.group(2).strip()
    return fm, body, None


def iter_components():
    for p in sorted((ROOT / "agents").glob("*.md")):
        yield "agent", p
    for p in sorted((ROOT / "commands").glob("*.md")):
        yield "command", p
    for p in sorted((ROOT / "skills").glob("*/SKILL.md")):
        yield "skill", p


def rel(p):
    return str(Path(p).relative_to(ROOT))


# ---------------------------------------------------------------- structural

def check_frontmatter(rep):
    skill_dirs = {d.name for d in (ROOT / "skills").iterdir() if d.is_dir()}

    for kind, path in iter_components():
        fm, _, err = parse_frontmatter(path)
        if err:
            rep.error(rel(path), err)
            continue

        desc = fm.get("description", "")
        if not desc:
            rep.error(rel(path), "description is missing or empty")
        elif len(desc) > MAX_DESCRIPTION_CHARS:
            rep.error(rel(path),
                      f"description is {len(desc)} chars, limit is {MAX_DESCRIPTION_CHARS}")

        model = fm.get("model", "")
        if kind in ("agent", "command"):
            if not model:
                rep.error(rel(path), "model is missing")
            elif model not in VALID_MODELS:
                rep.error(rel(path),
                          f"model '{model}' is not one of {sorted(VALID_MODELS)} "
                          f"(claude plugin validate does NOT catch this)")

        if kind == "agent":
            expected = path.stem
            if fm.get("name") != expected:
                rep.error(rel(path), f"name '{fm.get('name')}' != filename '{expected}'")
            skills = [s.strip() for s in fm.get("skills", "").split(",") if s.strip()]
            if len(skills) > MAX_SKILLS_PER_AGENT:
                rep.error(rel(path),
                          f"{len(skills)} skills, limit is {MAX_SKILLS_PER_AGENT} "
                          f"(CONTRIBUTING.md: over 15 = God-Agent, must split)")
            for s in skills:
                if s not in skill_dirs:
                    rep.error(rel(path), f"skills: '{s}' does not resolve to skills/{s}/SKILL.md")

        if kind == "skill":
            expected = path.parent.name
            if fm.get("name") != expected:
                rep.error(rel(path), f"name '{fm.get('name')}' != folder '{expected}'")
            n = len(path.read_text(encoding="utf-8", errors="replace").splitlines())
            if n > MAX_SKILL_LINES:
                rep.error(rel(path),
                          f"{n} lines, limit is {MAX_SKILL_LINES} — move detail into references/")


def check_skill_reachability(rep):
    referenced = set()
    for path in sorted((ROOT / "agents").glob("*.md")):
        fm, _, err = parse_frontmatter(path)
        if err:
            continue
        referenced |= {s.strip() for s in fm.get("skills", "").split(",") if s.strip()}
    on_disk = {d.name for d in (ROOT / "skills").iterdir() if d.is_dir()}
    for orphan in sorted(on_disk - referenced):
        rep.error(f"skills/{orphan}",
                  "orphaned — no agent lists it in `skills:` (CLAUDE.md requires at least one)")


def check_agent_references(rep):
    agents = {p.stem for p in (ROOT / "agents").glob("*.md")}
    pat = re.compile(r'subagent_type\s*[=:]\s*["\']?acc:([a-z0-9-]+)')
    for kind, path in iter_components():
        for m in pat.finditer(path.read_text(encoding="utf-8", errors="replace")):
            if m.group(1) not in agents:
                rep.error(rel(path), f'subagent_type "acc:{m.group(1)}" has no agents/{m.group(1)}.md')


def check_task_tool_granted(rep):
    """A file that instructs Task delegation must have Task in tools/allowed-tools."""
    instructs = re.compile(r'subagent_type\s*[=:]|use the \*\*Task tool\*\*|Task tool with subagent_type')
    for kind, path in iter_components():
        if kind == "skill":
            continue
        fm, body, err = parse_frontmatter(path)
        if err:
            continue
        if not instructs.search(body):
            continue
        tools = fm.get("tools") or fm.get("allowed-tools") or ""
        if not re.search(r"\bTask\b", tools):
            rep.error(rel(path),
                      "instructs Task delegation but 'Task' is absent from tools/allowed-tools — "
                      "the delegation is dead code")


def check_counts_in_sync(rep):
    """
    Only inventory lines are checked — those naming two or more component types at once
    ("26 commands, 68 agents, 283 skills"). A local count such as "with 11 skills" describing
    one agent is legitimate and must not be rewritten to the global total.
    """
    actual = {
        "commands": len(list((ROOT / "commands").glob("*.md"))),
        "agents": len(list((ROOT / "agents").glob("*.md"))),
        "skills": len([d for d in (ROOT / "skills").iterdir() if d.is_dir()]),
    }
    targets = ["README.md", "llms.txt", "CLAUDE.md",
               "docs/quick-reference.md", ".claude-plugin/marketplace.json"]
    for t in targets:
        p = ROOT / t
        if not p.exists():
            continue
        for i, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            found = {noun: int(m.group(1))
                     for noun in actual
                     for m in [re.search(rf"(\d+)\s+(?:slash\s+)?{noun}\b", line)] if m}
            if len(found) < 2:
                continue
            for noun, said in found.items():
                if said != actual[noun]:
                    rep.error(f"{t}:{i}",
                              f"inventory line says {said} {noun}, actual is {actual[noun]}"
                              f"\n      → {line.strip()[:110]}")


# ---------------------------------------------------------------- lexical

def markdown_files():
    for sub in ("skills", "agents", "commands", "docs"):
        d = ROOT / sub
        if d.exists():
            yield from sorted(d.rglob("*.md"))


def check_banned_patterns(rep):
    exempt = re.compile(
        r"must never be generated|do not exist|does not exist|there is no|Use instead|"
        r"Never generate|Do NOT report|NOT quadratic|Invalid key in record|no Cloneable interface|"
        r"Must be `no` in containers|removed in PHPStan|is FALSE since PHP 8|checked separately"
    )
    for path in markdown_files():
        for i, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if exempt.search(line):
                continue
            for pat, why in BANNED_PATTERNS:
                if pat.startswith(r"\breadonly class"):
                    continue  # handled by check_readonly_inheritance
                if re.search(pat, line):
                    rep.error(f"{rel(path)}:{i}", f"{why}\n      → {line.strip()[:110]}")


def check_invented_hook_events(rep):
    """
    Naming an invented event is a defect; documenting that it is invented is not.
    A line is exempt when it also names the correct replacement, or carries an explicit
    "does not exist" style warning — that covers the "invented → real" mapping tables.
    """
    # Case-insensitive, and tolerant of markdown emphasis inside the phrase
    # ("do **not** exist"), which is how these warnings are actually written.
    exempt = re.compile(
        r"do(es)? \*{0,2}not\*{0,2} exist|use instead|never offer|never generate|"
        r"there is no|is the real one|invalid key",
        re.IGNORECASE,
    )
    for path in markdown_files():
        for i, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if exempt.search(line):
                continue
            for bad, good in INVENTED_HOOK_EVENTS.items():
                if not re.search(rf"\b{bad}\b", line):
                    continue
                if re.search(rf"\b{good}\b", line):
                    continue  # a mapping row: "| ToolError | PostToolUseFailure |"
                rep.error(f"{rel(path)}:{i}",
                          f"hook event '{bad}' does not exist — use '{good}'"
                          f"\n      → {line.strip()[:110]}")


def check_grep_patterns_executable(rep):
    """
    Detection greps must be runnable by the Grep tool, whose Rust regex has no lookaround
    and no backreferences, and which treats '\\|' as a literal pipe rather than alternation.

    Reported as WARNINGS, not errors: 124 pre-existing occurrences across 56 files are scheduled
    for the stage-5 grep audit. Flip these to rep.error() once that stage lands, so the gate
    stops new ones from appearing.
    """
    grep_line = re.compile(r"^\s*Grep:\s*(.+)$")
    for path in markdown_files():
        for i, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            m = grep_line.match(line)
            if not m:
                continue
            expr = m.group(1)
            if re.search(r"\(\?[=!<]", expr):
                rep.warn(f"{rel(path)}:{i}",
                         "Grep uses lookahead/lookbehind — ripgrep rejects it with a hard parse "
                         "error. Replace with a two-pass 'widen, then Read to confirm' recipe.")
            if re.search(r"\\[1-9]\b", expr):
                rep.warn(f"{rel(path)}:{i}",
                         "Grep uses a backreference — unsupported by ripgrep.")
            if re.search(r"\\\|", expr):
                rep.warn(f"{rel(path)}:{i}",
                         r"Grep uses BRE alternation '\|' — ripgrep needs a plain '|'.")


def check_readonly_inheritance(rep):
    """A readonly class may not extend a non-readonly one (PHP 8.2+ fatal error)."""
    decl = re.compile(r"^\s*(?:(final|abstract)\s+)?(readonly\s+)?(?:(final|abstract)\s+)?"
                      r"(?:(readonly)\s+)?class\s+([\w{}]+)(?:\s+extends\s+([\w{}]+))?", re.M)
    for path in markdown_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        bases, children = {}, []
        for m in decl.finditer(text):
            is_ro = bool(m.group(2) or m.group(4))
            bases[m.group(5)] = is_ro
            if m.group(6):
                line = text[:m.start()].count("\n") + 1
                children.append((m.group(5), m.group(6), is_ro, line))
        for child, parent, child_ro, line in children:
            if child_ro and parent in bases and not bases[parent]:
                rep.error(f"{rel(path)}:{line}",
                          f"'{child}' is readonly but extends non-readonly '{parent}' — "
                          f"Fatal error on PHP 8.2+")


def check_reference_links(rep):
    """
    Every references/<file> named in a SKILL.md must exist. Two forms occur:
      references/foo.md                 → relative to this skill
      other-skill/references/foo.md     → relative to skills/other-skill/
    """
    link = re.compile(r"(?:([\w-]+)/)?references/([\w.-]+\.md)")
    for path in sorted((ROOT / "skills").glob("*/SKILL.md")):
        for i, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            for m in link.finditer(line):
                owner, fname = m.group(1), m.group(2)
                base = (ROOT / "skills" / owner) if owner else path.parent
                if not (base / "references" / fname).exists():
                    shown = f"{owner}/references/{fname}" if owner else f"references/{fname}"
                    rep.error(f"{rel(path)}:{i}", f"{shown} does not exist on disk")


def check_hooks_json(rep):
    p = ROOT / "hooks" / "hooks.json"
    if not p.exists():
        return
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        rep.error("hooks/hooks.json", f"invalid JSON: {e}")
        return
    for event in data.get("hooks", {}):
        if event not in VALID_HOOK_EVENTS:
            rep.error("hooks/hooks.json",
                      f"'{event}' is not a real hook event — claude plugin validate rejects it")


CHECKS = [
    ("frontmatter", check_frontmatter),
    ("skill reachability", check_skill_reachability),
    ("agent references", check_agent_references),
    ("Task tool granted", check_task_tool_granted),
    ("component counts", check_counts_in_sync),
    ("banned patterns", check_banned_patterns),
    ("invented hook events", check_invented_hook_events),
    ("executable grep patterns", check_grep_patterns_executable),
    ("readonly inheritance", check_readonly_inheritance),
    ("references/ links", check_reference_links),
    ("hooks.json", check_hooks_json),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    ap.add_argument("--only", help="run a single check by name")
    args = ap.parse_args()

    total = 0
    for name, fn in CHECKS:
        if args.only and args.only not in name:
            continue
        print(f"\n\033[0;36m{name}\033[0m")
        rep = Report()
        fn(rep)
        total += rep.render(args.strict)

    print()
    if total:
        print(f"\033[0;31m✘ {total} check(s) failed\033[0m\n")
        return 1
    print("\033[0;32m✓ all checks passed\033[0m\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
