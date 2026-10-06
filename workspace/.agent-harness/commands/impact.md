Use the api-impact agent to analyse the cross-repo impact of a proposed change.

Proposed change: $ARGUMENTS

Steps:
1. Read the thing being changed — confirm its current shape before analysing impact
2. Search all repos (ai-backend, ai-frontend, ghl-crm-frontend legacy, ghl-revex-frontend)
   for every caller, consumer, or dependent
3. For each affected file: describe what it uses, what breaks, and what needs to change
4. Produce a summary table of all affected files
5. Give a clear verdict: safe to proceed / proceed with the following updates first
6. State the migration order if a coordinated deployment is required
