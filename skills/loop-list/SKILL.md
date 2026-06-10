---
name: loop-list
description: List loop specs in the current project. Use when the user asks what loops exist, wants available loops printed, says looplist, asks which loop to run, or needs an inventory of .loops entries before operating them.
---

# loop-list — show runnable loops in this project

This is a read-only inventory pass. Do not start loops, modify registry files, or diagnose
health deeply; use `loop-status` for maintenance.

## Workflow

1. Find the project loop registry:
   - Prefer `.loops/LOOPS.md`.
   - Also scan `.loops/*/loop.md` so unregistered loop folders are visible.
   - If `.loops/` is missing, say no loops were found and suggest `loop-generate`.
2. For each loop folder, read only the small files needed for a list:
   - `loop.md`: title, purpose/north star, trigger/mechanism, status line.
   - `state.md`: last run and findings awaiting human review.
   - `.loops/LOOPS.md`: status, mechanism, cadence, last run, notes.
3. Print a compact table:
   - Loop
   - Status
   - Purpose
   - Mechanism
   - Cadence
   - Last run
   - Waiting on human
   - Path
4. After the table, list likely next commands:
   - `/loop-run <name>` for a selected loop.
   - `/loop-status` for health and maintenance.
   - `/loop-generate` if the user expected a loop that is missing.

## Parsing Guidance

- Treat folder names under `.loops/` as the canonical loop ids.
- If registry and folder disagree, show both and mark `registry drift` in the table.
- Extract the first sentence from `## Purpose / north star` when possible.
- Extract the `Mechanism:` and cadence from `## Trigger & mechanism` or the registry row.
- Count non-placeholder bullets under `## Findings awaiting human review`; placeholders like
  `- —` mean zero waiting items.

## Output Rules

- Keep output short enough to scan.
- Do not hide draft, paused, or broken loops; users list loops specifically to find what exists.
- Do not quote sensitive prompt history from reports or digests.
- Do not read `.loops/reports/.digest/` for listing; it can contain private transcript data.
