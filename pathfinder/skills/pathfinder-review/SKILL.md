# pathfinder-review

> Interactive architecture review: walk through each C4 level with the user, visualize with Structurizr, and iterate until the model is validated.

## When to use

- After the Init Agent builds the initial C4 model from a codebase
- After the Architect Agent modifies the workspace (new containers, components, flows)
- Before starting implementation to confirm the architecture is correct
- When onboarding a stakeholder who needs to validate the model

## Inputs

| Input | Required | Description |
|---|---|---|
| Workspace | Yes | A Structurizr DSL workspace (already created by Init Agent or Architect Agent) |
| Review scope | No | Limit to a specific C4 level or container; defaults to full top-down review |

## Prerequisites

- MCP server is available with these tools: "Read workspace", "Update workspace", "Validate DSL", "Inspect DSL", "Export to Mermaid", "Parse DSL"
- Docker is installed and running (for Structurizr Server visualization; see fallback below)

---

## Procedure

### Phase 1: Start infrastructure

**Step 1 -- Start the Structurizr Server**

```bash
pathfinder start
```

If the command fails (Docker unavailable, port conflict), fall back to Mermaid mode (see Phase 5).

**Step 2 -- Direct the user to the visualization**

Tell the user:

> Open http://localhost:8080 in your browser. This is the Structurizr Server showing your architecture diagrams and documentation. Keep it open -- it will update live as we make changes.

Wait for the user to confirm they can see the visualization before proceeding.

---

### Phase 2: Review System Context level

**Step 3 -- Read the current workspace**

Use MCP "Read workspace" to load the full DSL. Use MCP "Inspect DSL" to extract the system context elements: the software system(s) and all external actors, systems, and dependencies.

**Step 4 -- Present the System Context for validation**

Present the system context to the user:

> Here is the big picture -- your system and its external dependencies.
>
> **Your system:** [name and description]
>
> **External actors/systems:**
> - [actor/system] -- [relationship description]
> - [actor/system] -- [relationship description]
>
> Does this accurately represent how your system fits into the broader landscape? Is anything missing or incorrect?

**Step 5 -- Collect corrections**

If the user identifies corrections:

1. Use MCP "Update workspace" to apply each change to the DSL.
2. Use MCP "Validate DSL" to confirm the workspace is still valid.
3. Tell the user to refresh http://localhost:8080 to see the updated diagram.
4. Re-present the updated System Context and ask for confirmation.

Repeat until the user approves the System Context level.

---

### Phase 3: Review Container level

**Step 6 -- Present the Containers for validation**

Use MCP "Inspect DSL" to extract all containers within the software system. Present them:

> These are the deployable units in your system -- the things you build, deploy, and run independently.
>
> **Containers:**
> - [container name] -- [technology] -- [description]
> - [container name] -- [technology] -- [description]
>
> **Relationships between containers:**
> - [source] -> [target]: [description]
>
> Does this match how you actually deploy? Are there containers missing, or any that should be merged or split?

**Step 7 -- Collect corrections**

Same correction loop as Step 5:

1. Use MCP "Update workspace" to apply changes.
2. Use MCP "Validate DSL" to confirm validity.
3. Direct user to refresh the visualization.
4. Re-present and ask for confirmation.

Repeat until the user approves the Container level.

---

### Phase 4: Review Component level (per container)

**Step 8 -- Iterate over each container**

For each container in the workspace, present its internal components:

> These are the logical modules inside **[container name]**.
>
> **Components:**
> - [component name] -- [technology] -- [description]
> - [component name] -- [technology] -- [description]
>
> **Internal relationships:**
> - [source] -> [target]: [description]
>
> **External relationships (to/from other containers):**
> - [component] -> [external container/component]: [description]
>
> Missing anything? Are the responsibilities correctly assigned?

**Step 9 -- Collect corrections per container**

Same correction loop as Step 5. Apply changes, validate, refresh, re-present.

Repeat for each container until the user approves all component diagrams.

---

### Phase 4b: Review Documentation

**Step 10 -- Present documentation for validation**

Use MCP "Read workspace" to extract any documentation sections and ADRs (Architecture Decision Records) defined in the workspace.

> Here is the written documentation included in the workspace:
>
> **Documentation sections:**
> - [section title]: [brief summary]
>
> **ADRs:**
> - [ADR title]: [status] -- [brief summary]
>
> Is this accurate? Any sections missing or needing updates?

**Step 11 -- Collect corrections**

If documentation needs changes, use MCP "Update workspace" to modify the relevant sections, then validate.

---

### Phase 5: Fallback -- Mermaid mode (no Docker)

If Docker is unavailable and `pathfinder start` failed in Step 1, use this fallback for every review step above.

**Instead of directing the user to http://localhost:8080**, generate inline diagrams:

1. Use MCP "Export to Mermaid" to generate a Mermaid diagram for the current C4 level.
2. Present the Mermaid diagram directly in the conversation as a fenced code block:

````
```mermaid
[exported diagram]
```
````

3. Proceed with the same review questions and correction loop.
4. After each correction, re-export to Mermaid and present the updated diagram.

Tell the user at the start:

> Docker is not available, so I cannot start the Structurizr Server. Instead, I will generate Mermaid diagrams inline for each level. If your editor supports Mermaid preview, you can visualize them there.

---

### Phase 6: Final confirmation

**Step 12 -- Summarize all approvals**

Once the user has approved every level, present the summary:

```
== Review Complete ==

System Context:  APPROVED
Containers:      APPROVED
Components:      APPROVED ([N] containers reviewed)
Documentation:   APPROVED

Changes made during review:
  - [brief description of each change applied]

The workspace is validated and ready for use.
```

**Step 13 -- Validate the final workspace**

Run a final validation to confirm everything is consistent:

1. Use MCP "Validate DSL" one last time.
2. If validation passes, confirm to the user that the workspace is clean.
3. If validation fails, fix the issues and re-validate before declaring completion.

---

## Correction loop reference

Every correction follows the same cycle. Do not skip any step:

1. **Understand** -- Confirm what the user wants changed.
2. **Update** -- Use MCP "Update workspace" to apply the change to the DSL.
3. **Validate** -- Use MCP "Validate DSL" to ensure the DSL is still syntactically and structurally valid.
4. **Render** -- Tell the user to refresh the Structurizr Server, or re-export to Mermaid in fallback mode.
5. **Confirm** -- Re-present the updated level and ask if it is now correct.

If validation fails after an update, inspect the error, fix the DSL, and validate again before showing the result to the user.

---

## Decision points

| Situation | Decision |
|---|---|
| User wants to skip a C4 level | Allow it, but note it as unreviewed in the final summary |
| User requests a change that breaks DSL validation | Do not present the broken state; fix the validation error first, then show the corrected result |
| User is unsure about a component's placement | Suggest examining the code that implements it; use MCP "Inspect DSL" to show the current definition |
| User wants to add entirely new containers or systems | Apply the addition, validate, and continue the review at the appropriate level |
| Structurizr Server stops responding mid-review | Fall back to Mermaid mode for the remainder of the review |
| User disputes the documentation but not the diagrams | Update documentation independently; documentation changes do not require re-reviewing diagrams |

## Output

When this skill completes, the project will have:

- A user-validated Structurizr workspace at all C4 levels (System Context, Containers, Components)
- Validated documentation and ADRs
- A clean DSL that passes validation
- A record of all changes made during the review
