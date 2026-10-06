Use the documentation-writer agent to write technical documentation for the specified system or feature.

Target: $ARGUMENTS

**HARD GATE** — Before invoking the agent, check that `ai-specs/<feature-name>/plan-*.md`
exists. If no plan file is found, stop and say:
"No plan found for this feature. Run `/plan <name>` first, then re-run `/feature-docs`."

Steps:
1. Read all files relevant to the target system — services, components, stores, models
2. Trace the full call chain end-to-end
3. Read any existing PRD or plan files for context
4. Produce comprehensive documentation covering: overview, architecture, data models,
   end-to-end flow, configuration, edge cases, and key files reference
5. Save as docs-{topic}.md in the relevant ai-specs/<feature-name>/ folder
