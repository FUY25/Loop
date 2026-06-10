---
name: loop-generate
description: Design and scaffold a complete autonomous loop for a recurring task — spec with a machine-verifiable stop condition, token/iteration budget, escalation rules, state file, and the exact start command (/goal, /loop, cron/schedule, hooks, or GitHub Actions). Use whenever the user wants to "create a loop", "automate this workflow", "set up a routine/automation", "run this every day/morning", "turn this into a loop", "帮我自动化", "设个定时任务", or picks an item from a loop-scan opportunities report.
---

# loop-generate — scaffold a loop you can actually walk away from

A loop is a recursive goal: you define the purpose and the system iterates until done — without
you as the prompt daemon. The difference between a loop that compounds and a loop that produces
slop is the spec. Your job here is to force precision in the four places vague loops fail:
**stop condition, verification, budget, escalation**.

## Step 1 — Source the loop idea

This skill works standalone — a scan report is a convenient input, never a prerequisite.

- If `.loops/reports/` has a recent loop-opportunities report, offer its top items as starting
  points (evidence and proposed shape are pre-filled).
- Otherwise work from what the user just described, from scratch.
- Bootstrap `.loops/` + `.loops/LOOPS.md` (from `assets/LOOPS-template.md`) if missing.
- **Sanity-check the shape first.** If the request is really a stateless event-triggered check
  (a hook) or context to encode once (a skill), say so and scaffold that lighter thing instead —
  a hook fragment or a plain skill — rather than wrapping a non-loop in loop ceremony. Loops
  earn their ceremony through recurring state, budgets, and verification; hooks and skills don't
  need it.

## Step 2 — Interview for the spec (the hard parts)

Ask only what's missing; if the user is unavailable, make conservative choices and flag every
assumption in the spec. The quality bar, and why each matters:

1. **Purpose / north star** — why does this loop exist in business terms? A loop that can't
   state its payoff gets retired in a month.
2. **Stop / success condition — must be machine-verifiable.** "Looks good" or "feels clean" is
   not a stop condition; it puts the human right back in the loop. Push until you get something
   a checker agent can evaluate: "all tests in `test/auth` pass and lint is clean", "report file
   exists with ≥1 ranked item", "endpoint returns 200 with schema-valid body". If the user
   describes manual verification steps, that's a sign to encode them first (see `loop-verify`).
3. **Trigger shape** — until-done, recurring, event-driven, or external? (mechanism table below)
4. **Budget — hard constraints, not vibes.** Max iterations per run, max wall time, rough token
   ceiling per run and per week. Unattended means mistakes are unattended too; the budget is the
   blast radius.
5. **Failure paths & idempotency** — what does a failed run look like? Is re-running safe?
   Anything that must never happen twice (sending an email, pushing a tag) needs an idempotency
   guard written into the workflow.
6. **Escalation** — what lands in the human's inbox vs. what the loop handles alone. Default:
   the loop never merges, sends, deletes, or publishes without a human gate, unless the user
   explicitly grants it.
7. **Maker/checker split** — for anything beyond trivial, the agent that does the work should
   not be the one grading it. Note in the spec where a second agent (or `/goal`'s independent
   condition checker) verifies.

## Step 3 — Pick the mechanism

| Loop shape | Claude Code | Codex (port later) |
|---|---|---|
| Iterate until condition true, this session | `/goal "<verifiable condition>"` | `/goal` |
| Recurring while session is open | `/loop <interval> <prompt or /skill>` | — |
| Background on a schedule | `/schedule` (cloud agent) or cron | Automations tab |
| Event-triggered (post-edit, pre-commit…) | hooks in settings.json | — |
| Must survive laptop close / team-visible | GitHub Actions | cloud Automations |

Prefer the lightest mechanism that fits. A recurring `/loop` you watch beats a cron job you
forget. Recommend one; mention the runner-up in the spec's "Mechanism" section.

## Step 4 — Scaffold

Create `.loops/<loop-name>/` from the templates (`assets/loop-template.md`,
`assets/state-template.md`):

- `loop.md` — the spec. Fill every section; write "n/a + why" rather than deleting sections.
  Include an exact `## Start command / runner config` section so `loop-run` can start it later.
- `state.md` — the loop's memory. The model forgets everything between runs; this file is the
  spine. The loop prompt you generate MUST instruct: read `state.md` first, append to `runs.log`
  and update `state.md` last.
- Add a row to `.loops/LOOPS.md`.

If the workflow depends on project knowledge an agent would otherwise re-derive every run
(conventions, build steps, gotchas), also scaffold a companion skill in `.claude/skills/<name>/`
and have the loop prompt invoke it.

## Step 5 — Wire and hand over

Produce the exact start command, ready to run:

- `/goal` → the full goal text including the stop condition verbatim.
- `/loop` → the full command line, e.g. `/loop 30m "Read .loops/ci-watch/state.md, then …"`.
- Scheduled → offer to create it now (via the schedule tooling) or print the cron line.
- Hooks → the settings.json fragment.

Then show the user: spec file path, start command, and the one-paragraph "how to stop it /
how to check on it" (point at `loop-status`). Don't start background mechanisms without the
user's go-ahead — what runs unattended is their call.

## Sanity checklist before handing over

- Stop condition machine-verifiable? Budget has numbers in it? Escalation says what reaches the
  human? state.md read-first/write-last wired into the prompt? Idempotency hazards listed?
- If any answer is no, the loop isn't done — fix the spec, not the prose.
