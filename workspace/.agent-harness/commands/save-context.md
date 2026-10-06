Save the current session state so the next session starts warm.

Optional note: $ARGUMENTS

---

Write a compact summary to `.claude/session-context.md` with exactly these sections:

```markdown
# Session Context — [date]

## Active feature
[feature name and one-sentence description]

## Pipeline position
[what just completed and what the next step is]
e.g. "Plan written (ai-specs/foo/plan-foo.md). Next: /code foo"

## Files changed this session
[bullet list — one file per line]

## Open decisions
[unresolved questions, blockers, or choices pending for next session]

## Immediate next step
[single actionable instruction]
e.g. "/code foo — implement tasks 3-5 from plan-foo.md"
```

Keep under 40 lines. Overwrite completely if file already exists.
Confirm: "Context saved to .claude/session-context.md — next session starts warm."
