---
name: loop-status
description: Health check and maintenance for autonomous loops — reads the project's .loops/ registry and state files, flags stale/failing/over-budget loops, surfaces findings awaiting human review, and recommends retire/tune/fix actions. Use whenever the user asks "how are my loops", "loop status", "check my loops/automations", "anything need attention", "我的循环/自动化任务怎么样了", or returns to a project after time away and has loops registered.
---

# loop-status — stay the engineer

A loop running unattended is also making mistakes unattended, and the comfortable posture —
take whatever it produces — is the risky one. This skill is the maintenance pass: what ran,
what's rotting, what's waiting on the human.

## Step 1 — Gather

- Read `.loops/LOOPS.md`. If missing, say so and point to `loop-scan`/`loop-generate` — done.
- For each registered loop, read `.loops/<name>/loop.md` (cadence, budget, escalation),
  `state.md` (last run, findings), `runs.log` (history; line count and last lines).
- Cross-check schedulers for drift — a loop can be registered but not scheduled, or scheduled
  but deregistered: check the scheduled-task list for cron/schedule mechanisms, `crontab -l`
  if system cron, hooks in `.claude/settings.json` for hook loops. Drift in either direction
  is a finding.

## Step 2 — Score each loop

| Health | Meaning |
|---|---|
| 🟢 healthy | last run within 1.5× cadence, result success, within budget |
| 🟡 attention | stale (1.5–3× cadence), partial results, budget near ceiling, or findings unreviewed |
| 🔴 broken | >3× cadence overdue, last runs failed, budget-hit repeatedly, or registry/scheduler drift |
| ⚪ paused/retired | as recorded — verify the scheduler entry is actually gone |

## Step 3 — Report

Output a status table (loop · mechanism · cadence · last run · health · waiting-on-human), then:

- **Findings inbox** — every item under `state.md → Findings awaiting human review`, across all
  loops, oldest first. This is the section the user must actually read; a loop whose output
  nobody reads is comprehension debt on a timer.
- **Recommended actions**, each with a reason:
  - **Fix** — broken loops: likely cause from runs.log/state.md, one-line repair suggestion.
  - **Tune** — repeated budget hits or noisy findings: adjust cadence, budget, or scope in loop.md.
  - **Retire** — a loop that produced nothing the human used in its last ~3 runs, or whose
    purpose has lapsed. Retiring is success, not failure; loops rot and restraint keeps the
    registry trusted. To retire: set status in LOOPS.md + loop.md, remove the scheduler entry,
    keep the folder for history.

## Step 4 — Apply

Offer to apply the bookkeeping (registry updates, retire status) immediately; for anything
touching live schedulers, confirm with the user first. Update `LOOPS.md` last-run column from
what you observed — the registry should leave this session truthful.
