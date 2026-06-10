---
name: loop-verify
description: Turn the user's MANUAL verification steps (open the app and click around, curl an endpoint, run and eyeball a script) into an encoded verification skill that agents run automatically after changes and that loop stop-conditions can call. Use whenever the user describes how they manually test/check their work, asks to "encode my verification", "make Claude test this like I do", "automate my QA steps", "把我的测试步骤变成自动的", or a loop being designed has a human-judgment stop condition that should be mechanized.
---

# loop-verify — encode the checks only you know

Type checkers, tests, and runtime errors are signals agents already use. What they can't infer
are the steps you take to *manually* verify a change — those live in your head, not the repo.
Every step you encode moves the agent's first response closer to what you had in mind, and makes
loop stop-conditions checkable without you. This skill interviews the user and writes that
knowledge down as a verification skill.

It works standalone — no `.loops/` or existing loop required. Use it equally to harden the
check behind a single hook, to mechanize any vague "done" standard before a loop is built
(loop-scan marks these `needs-encoding`), or purely to upgrade everyday manual QA.

## Step 1 — Capture the current manual workflow

Ask the user to walk through what they actually do after a change, as a "best-practices version
of what you already do". Get concrete: commands, URLs, what they look at, what "wrong" looks
like. If they struggle to articulate it, propose a domain-default end-to-end pass (Step 2) and
let them correct it — editing is easier than authoring.

## Step 2 — Upgrade with domain defaults

Map each manual step to something an agent can drive, and add the checks the user does
implicitly. Read `references/domain-playbooks.md` for the playbook matching the project domain
(web UI, API/backend, CLI, docs/content, data pipeline) — it lists the standard pass, the tools
that drive it, and the evidence to capture.

Two rules that make verification trustworthy:
- **Evidence, not vibes** — every check captures something reviewable: screenshot, response
  body, exit code, log excerpt. "It works" without evidence is a claim, not a proof.
- **Regression scope** — verify the change AND the 2–3 adjacent things most likely to break.
  The famous catch is the layout shift found while adding a like button: it gets caught because
  the pass always checks core vitals, not because someone asked.

## Step 3 — Write the verification skill

Scaffold `.claude/skills/verify-<project-name>/SKILL.md`:

- **description**: written to trigger *proactively* — "Use after ANY code change to <project>,
  before reporting work as done, even when the user didn't ask for verification."
- **Body**: setup (dev server/env), the ordered checks with exact commands/tool calls, evidence
  to capture and where to save it, pass/fail criteria per check, and what to do on failure
  (fix and re-verify; report honestly if still failing — a failed verification reported
  faithfully is worth more than a green lie).
- Keep checks fast enough to run every time. A pass nobody runs because it takes 20 minutes
  verifies nothing; if needed, split a quick per-change pass from a deep pre-ship pass.

## Step 4 — Wire into loops

- If `.loops/` exists, note in the relevant `loop.md → Verification` sections that the loop
  calls this skill, and that `/goal` stop conditions may reference it ("verify-<project> pass
  is green").
- Tell the user the skill triggers automatically on future changes, and offer a dry run now on
  the current working tree to validate the checks actually work end-to-end. Fix any check that
  doesn't run cleanly — a verification skill that errors gets ignored forever.
