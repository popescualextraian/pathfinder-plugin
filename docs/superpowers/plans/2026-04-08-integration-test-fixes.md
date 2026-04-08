# Integration Test Fixes Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix all 11 issues found during the first integration test of the pathfinder CLI and skills.

**Architecture:** CLI code fixes (issues 2,3,4,5,6,7) are independent of each other and can be parallelized. Skill documentation rewrites (issues 1,8,9,10,11) form one large task that depends on knowing the final CLI syntax but can be written in parallel with CLI fixes since the target syntax is known.

**Tech Stack:** Python 3.12+, Click CLI, YAML, Markdown skills

---

### Task 1: Add resolve_component_id helper (Issue #2)

**Files:**
- Modify: `pathfinder/core/storage.py` - add `resolve_component_id()` 
- Modify: `pathfinder/cli/set_cmd.py` - use resolver
- Modify: `pathfinder/cli/show_cmd.py` - use resolver
- Modify: `pathfinder/cli/map_cmd.py` - use resolver
- Modify: all other CLI commands taking ID_ - use resolver
- Test: `tests/cli/test_set.py` - add slash-notation test

The resolver tries: ID as-is, then replaces `/` with `.`. Applied to `load_component` calls in CLI layer.

### Task 2: Add --spec to add command (Issue #3)

**Files:**
- Modify: `pathfinder/cli/add_cmd.py` - add `--spec` option
- Test: `tests/cli/test_add.py` - add test

### Task 3: Replace Unicode arrows with ASCII (Issue #5)

**Files:**
- Modify: `pathfinder/cli/set_cmd.py` - `\u2192` -> `->`
- Modify: `pathfinder/cli/map_cmd.py` - `\u2192` -> `->`
- Modify: `pathfinder/cli/flows_cmd.py` - `\u2192` -> `->`
- Modify: `pathfinder/cli/show_cmd.py` - `\u2192` -> `->`

### Task 4: Show without args + flows error (Issues #6, #7)

**Files:**
- Modify: `pathfinder/cli/show_cmd.py` - make id_ optional, show tree when missing
- Modify: `pathfinder/cli/flows_cmd.py` - check component exists before filtering
- Test: `tests/cli/test_show.py` - add no-args test
- Test: `tests/cli/test_flows.py` - add unknown-id test

### Task 5: Rewrite all skills and agent docs (Issues #1, #8, #9, #10, #11)

**Files:**
- Modify: `pathfinder/skills/pathfinder-discover/SKILL.md`
- Modify: `pathfinder/skills/pathfinder-define/SKILL.md`
- Modify: `pathfinder/skills/pathfinder-navigate/SKILL.md`
- Modify: `pathfinder/skills/pathfinder-implement/SKILL.md`
- Modify: `pathfinder/skills/pathfinder-check/SKILL.md`
- Modify: `pathfinder/agents/system-architect.md`

All CLI examples must use correct syntax. Add external component workflow. Add "when in doubt, ask" rules.

### Task 6: Run full test suite

```bash
pytest tests/ -v --tb=short
```

Fix any failures.
