Evaluate a candidate skill against the installed skill set and repo context before installing.

Skill name, package reference, or description: $ARGUMENTS

---

Use the skill-evaluator agent.

Pass whatever you have — a skill name, a GitHub reference (e.g. `vercel-labs/agent-skills@react`),
or a plain description of what you want the skill to do.

The agent runs a structured 6-step evaluation:
1. Inventory all installed skills and agent capabilities
2. Inspect the current repo context and active workstream
3. Understand what the candidate skill claims to do
4. Check for overlap with the installed capability set
5. Evaluate fit for this stack and workstream
6. Return a structured verdict

Verdicts:
- `already covered` — an installed skill or agent handles this; do not install
- `recommend install` — clear net positive; install
- `not worth it` — adds cost, overlap, or noise; do not install
- `need more context` — evaluation requires more information

Use before:
- Installing any skill from skills.sh, npx skills add, or any other source
- Comparing two candidate skills (e.g. frontend-design vs Ui-UX-pro-max)
- Auditing whether an already-installed skill is still earning its place
- Responding to a recommendation from the find-skills skill
