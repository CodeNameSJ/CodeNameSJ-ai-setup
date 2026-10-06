Review recent code changes with the code-reviewer agent. This workflow is named
`review-changes` to stay distinct from provider-built-in review commands.

Steps:
1. Run `git diff main` (or `git diff HEAD~1` if on main) to see what changed
2. Read every changed file in full
3. Read neighbouring files to understand codebase patterns
4. Produce a structured review with blocking issues, suggestions, and positive callouts
5. Save as review-{topic}.md in the relevant ai-specs/<feature-name>/ folder
   if $ARGUMENTS provides a feature name, otherwise output inline
6. Give a clear verdict: Approve / Approve with suggestions / Request changes
