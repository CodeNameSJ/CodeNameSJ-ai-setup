Use the code-writer agent to implement the current feature plan.

Steps:
1. Find the relevant feature folder under ai-specs/ — use $ARGUMENTS as feature name
   if provided, otherwise use the most recently modified folder
2. Look for plan-{topic}.md in that folder

   **HARD GATE** — If no plan file exists, STOP. Tell the user:
   "No plan found. Run `/plan {feature}` first — writing code without a plan
   produces lower-quality output and is harder to review."
   Only proceed if user explicitly types SKIP and accepts the risk.

3. Read plan-{topic}.md fully before touching any file
4. Implement each task in the plan in order
5. After completing all tasks, confirm what was implemented and any deviations
6. Confirm it's ready for /review-changes
