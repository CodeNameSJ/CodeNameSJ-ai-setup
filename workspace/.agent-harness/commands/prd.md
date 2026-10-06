Use the prd-writer agent to write a PRD for the current feature.

Steps:
1. Find the relevant feature folder under ai-specs/ — look for the most recently
   modified folder, or use $ARGUMENTS as the feature name if provided
2. Read requirements.md from that folder as the primary input
3. Explore the codebase to understand current behavior
4. Write the PRD as prd-{topic}.md in the same folder
5. Surface all open questions before finishing
6. Confirm it's ready for /plan
