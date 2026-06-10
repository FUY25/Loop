# Loop: <name>

> One-line purpose. Created <date> · Status: draft | active | paused | retired

## Purpose / north star
Why this loop exists, in payoff terms (time saved, errors prevented, revenue protected).

## Trigger & mechanism
- Mechanism: /goal | /loop <interval> | schedule/cron <expr> | hook <event> | GitHub Action
- Runner-up considered: <mechanism> — <why not chosen>

## Start command / runner config
<exact command or config fragment that starts this loop, e.g. /goal "...", /loop 30m "...",
cron line, schedule prompt, hook fragment, GitHub Actions workflow sketch, or Codex Automation
prompt. `loop-run` prefers this section when present.>

## Workflow
1. Read `.loops/<name>/state.md` (cross-run memory) — always first.
2. <step>
3. <step>
4. Update `state.md` (done / next / findings) and append one line to `runs.log` — always last.

## Stop / success condition (machine-verifiable)
<exact condition a checker can evaluate — commands, file existence, test names, status codes>

## Verification
<exact commands/checks that prove "done" — reproducible by anyone, including a second agent>

## Budget (hard limits)
- Max iterations per run: <n>
- Max wall time per run: <minutes>
- Token ceiling: ~<k> per run / ~<k> per week
- On budget hit: stop, write state, escalate — never push past silently.

## Failure & escalation
- Failure looks like: <signals>
- Retry policy: <n retries / backoff / give up>
- Escalate to human when: <conditions>. Escalation = write to state.md `## Findings` + <channel>.
- Never without a human gate: merge, send, delete, publish, pay. <adjust per user grant>

## Idempotency
- Safe to re-run? <yes/no>
- Must-not-happen-twice actions and their guards: <list>

## Memory contract
After every run `state.md` must contain: last run date+result, work completed, next work,
open findings awaiting human review.

## Maker/checker
<where a second agent or /goal's independent checker verifies the work>

## Assumptions made at creation
<flag anything not confirmed by the user>
