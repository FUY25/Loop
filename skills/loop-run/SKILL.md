---
name: loop-run
description: Select and start an existing project loop. Use when the user asks to run a loop, says looprun, gives a fuzzy loop name, wants to start a generated loop, or asks for the /goal, /loop, schedule, hook, GitHub Actions, or Codex Automation command for a .loops entry.
---

# loop-run — start one existing loop

Run means: select a loop from `.loops/`, read its spec, then produce or invoke the lightest
runner for that loop. Do not invent a new loop; use `loop-generate` when no suitable loop exists.

## Workflow

1. Discover loops:
   - Read `.loops/LOOPS.md` if present.
   - Scan `.loops/*/loop.md`.
   - If none exist, stop and suggest `loop-generate`.
2. Fuzzy-match the user's query against:
   - folder name
   - registry row
   - `# Loop:` title
   - purpose/north star
   - trigger/mechanism text
3. Select safely:
   - If exactly one loop is an obvious match, continue.
   - If multiple loops are plausible, print the top matches and ask the user to choose.
   - If nothing matches, run a `loop-list` style inventory and ask which one to run.
4. Read the selected loop:
   - `.loops/<name>/loop.md`
   - `.loops/<name>/state.md`
   - recent tail of `.loops/<name>/runs.log` if it exists
5. Build the start command or config:
   - Prefer an explicit `## Start command` / `## Runner config` section in `loop.md`.
   - Otherwise synthesize from `## Trigger & mechanism`, `## Workflow`, `## Stop / success
     condition`, `## Verification`, `## Budget`, and `## Failure & escalation`.
6. Hand off clearly:
   - Show matched loop, path, status, mechanism, last run, and waiting findings.
   - Print the exact command/config.
   - If the local environment can directly invoke the runner and the user explicitly asked to
     start now, run it. Otherwise print the command for the user to paste into Claude Code,
     Codex, cron, GitHub Actions, or the automation UI.

## Runner Rules

### `/goal`

Use for one run that should iterate until a verifiable condition is true.

Command shape:

```text
/goal "Read .loops/<name>/state.md first. Run the workflow in .loops/<name>/loop.md. Stop only when <stop condition>. Run <verification>. Respect budget and escalation rules. Update state.md and append runs.log last."
```

### `/loop`

Use for recurring work while the Claude Code session is open.

Command shape:

```text
/loop <interval> "Read .loops/<name>/state.md first. Run the workflow in .loops/<name>/loop.md once. Respect budget and escalation rules. Update state.md and append runs.log last."
```

Do not start a repeating loop silently. If the user did not explicitly ask to start it now,
print the command and explain that it repeats while the session is open.

### Scheduled, Cron, GitHub Actions, Codex Automations

Print the schedule, cron line, workflow sketch, or automation prompt. Do not install or enable
background execution unless the user explicitly asks.

### Hooks

Print the settings fragment or hook instructions. Do not modify hook settings unless the user
explicitly asks.

## Safety Rules

- Always preserve the memory contract: read `state.md` first, update `state.md` and `runs.log`
  last.
- Never auto-merge, send, delete, publish, pay, or create irreversible external effects unless
  the loop spec explicitly grants it and the user confirms for this run.
- Stop and escalate if the loop has unresolved findings awaiting human review that could affect
  this run.
- If the stop condition is vague or missing, refuse to start unattended execution and suggest
  repairing the loop spec with `loop-generate` or `loop-verify`.
