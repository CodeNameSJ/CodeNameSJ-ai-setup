Run the full feature development workflow from raw requirements through to QA.

Raw requirements or feature name: $ARGUMENTS

---

## Workflow

Execute each step in order. After each step, print a status line:
`✓ Step N complete — [what was produced]`
Then pause if there are open questions that need a decision before continuing.

---

### Step 1 — Requirements

Use the requirement-writer agent.

- If $ARGUMENTS is a feature name (short, like "consent-overhaul"), check if
  ai-specs/<feature-name>/requirements.md already exists — if yes, skip to Step 2.
- If $ARGUMENTS is raw requirement text (a sentence or more), process it into requirements.md.
- Save to ai-specs/<feature-name>/requirements.md.

**HARD GATE** — Stop and do not proceed to Step 2 if:
- Feature name is ambiguous or conflicts with an existing folder
- Input is too vague to structure without inventing scope

Reply with clarification to continue. Type SKIP only if you accept the risk.

---

### Step 2 — PRD

Use the prd-writer agent.

- Read requirements.md from the feature folder.
- Explore the codebase to understand current behavior.
- Write prd-{topic}.md in the same folder.

**HARD GATE** — Stop and do not proceed to Step 3 if the PRD surfaces:
- Unresolved ownership questions (who owns this data — frontend or backend?)
- Security or compliance implications not addressed in the requirements
- Scope ambiguity where multiple interpretations are equally valid

List the open questions explicitly. User must answer before implementation planning begins.
Type SKIP only if you accept the risk.

If prd-{topic}.md already exists and requirements.md hasn't changed, ask user whether to regenerate or skip to Step 3.

---

### Step 2.5 — Design (conditional)

Use the brainstorm agent if the feature involves any of:
- New data model shapes or document structures
- Multi-repo coordination (backend + frontend)
- New async flows (queues, PubSub, Cloud Tasks)
- Security, compliance, or IAM implications
- More than 5 files across 2+ apps

**HARD GATE** — If invoked, do NOT proceed to Step 3 without explicit design approval.
The brainstorm agent will propose 2–3 approaches and require you to choose before planning.

If the PRD is straightforward (UI-only change, single-app config tweak, single-file edit),
skip this step and state your reasoning explicitly.

---

### Step 3 — Implementation Plan

Use the implementation-planner agent.

- Read prd-{topic}.md from the feature folder.
- Read every file that will be affected before writing the plan.
- Write plan-{topic}.md in the same folder.

**HARD GATE** — Stop and do not proceed to Step 4 if the plan surfaces:
- Security or data ownership questions (frontend-supplied vs backend-generated data)
- Ambiguous scope or conflicting requirements
- Missing files or function signatures that can't be confirmed from the codebase

The following open questions must be answered before implementation begins:
[implementation-planner will list them here]

Reply with answers to continue. Type SKIP only if you accept the risk.

If plan-{topic}.md already exists, ask user whether to regenerate or skip to Step 4.

---

### Step 4 — Implementation

Use the code-writer agent.

- Read plan-{topic}.md.
- Implement each task in order.
- Do not proceed to Step 5 until all tasks are complete.

**HARD GATE** — Stop immediately if:
- An unresolved open question from the plan is encountered
- A type conflict, missing import, or changed function signature is found
- Actual code shape differs from what the plan assumed

Do not guess or work around it. Surface the exact blocker and wait for direction.

---

### Step 5 — Test Coverage

Add and run automated coverage for the behavior implemented in Step 4. QA in
Step 7 is complementary and does not replace this step.

- Map every changed behavior to the appropriate unit, integration, API E2E, or
  UI E2E layer.
- Use the code-writer agent to add or update the tests required by that map.
- For Voice AI UI changes, use the review-coverage agent to identify manifest
  gaps, then follow the automate-ui skill for any missing Playwright coverage.
- Run the narrowest relevant tests first, then the repository's required
  aggregate check when its local contract requires one.
- Save the behavior-to-test map, commands, and results to test-{topic}.md in the
  feature folder.

**HARD GATE** — Stop and do not proceed to Step 6 if:
- Changed behavior has no automated coverage and no explicit user-approved
  non-automatable reason
- A required test is skipped, conditionally green, or replaced by a mock of the
  successful behavior it claims to prove
- The targeted test fails or cannot execute because the implementation and test
  environment contract disagree

Surface the exact gap or blocker. Do not treat later QA exploration as a
substitute for deterministic regression coverage.

---

### Step 6 — Code Review

Use the code-reviewer agent.

- Run `git diff main` to get all changes made in Step 4.
- Review every changed file.
- Save review-{topic}.md in the feature folder.

**Pause after this step.** Show the review verdict and wait for user acknowledgement
before starting QA. If verdict is "Request changes", stop the workflow and wait for
the user to decide whether to fix before QA or proceed anyway.

---

### Step 7 — QA

Use the qa-bug-hunter agent.

- Read the same git diff used in Step 5.
- Read all changed files and their dependencies.
- Produce a P0/P1/P2 issue report.
- Save qa-{topic}.md in the feature folder.

**Workflow complete.** Print a summary:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Feature workflow complete: [feature name]

  requirements.md    ✓
  prd-{topic}.md     ✓
  plan-{topic}.md    ✓
  Code changes       ✓
  test-{topic}.md    ✓  [tests run]
  review-{topic}.md  ✓  [verdict]
  qa-{topic}.md      ✓  [ship verdict] — N issues (X P0, Y P1, Z P2)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
