Use the implementation-planner agent to write a detailed technical plan for the current feature.

Steps:
1. Find the relevant feature folder under ai-specs/ — use $ARGUMENTS as feature name
   if provided, otherwise use the most recently modified folder
2. Read prd-{topic}.md from that folder as the primary input
3. Explore every file that will be affected — read them before writing the plan
4. Write the plan as plan-{topic}.md in the same folder
5. Surface all open questions and flag risks before finishing
6. Confirm it's ready for /code
