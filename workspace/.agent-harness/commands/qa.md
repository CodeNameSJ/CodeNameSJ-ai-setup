Use the qa-bug-hunter agent to stress-test recent changes.

Steps:
1. Run `git diff main` (or `git diff HEAD~1` if on main) to understand what changed
2. Read every changed file and their dependencies
3. Stress-test across all five angles: happy path variations, failure paths, edge cases,
   race conditions, and security/multi-tenant isolation
4. Produce a prioritised P0/P1/P2 issue report with a suggested fix for each issue
5. Save as qa-{topic}.md in the relevant ai-specs/<feature-name>/ folder
   if $ARGUMENTS provides a feature name, otherwise output inline
6. Give a clear ship verdict: SHIP / SHIP WITH MITIGATIONS / DO NOT SHIP
