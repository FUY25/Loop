# Loops — skill family for loop engineering

> "You shouldn't be prompting coding agents anymore. You should be designing loops that prompt your agents."

This repo is the **development home** for a family of Claude Code skills that help you move from
prompting agents turn-by-turn to designing self-running loops. A loop = **trigger + work +
verification + memory**, assembled from five building blocks (automations, worktrees, skills,
connectors, sub-agents) plus a state file on disk.

## The skills

| Skill | Lifecycle stage | What it does |
|---|---|---|
| `loop-scan` | Discover | Mines Claude Code + Codex session history for repeated work, babysat sessions, and re-explained context → ranked Loop Opportunities Report |
| `loop-generate` | Design | Interviews you (or takes a scan finding) and scaffolds a complete loop: spec with verifiable stop condition, budget, escalation rules, state file, and the exact start command |
| `loop-status` | Operate / maintain | Reads `.loops/` registries, flags stale/failing/over-budget loops, surfaces unreviewed findings, recommends retire/tune |
| `loop-verify` | Verification layer | Encodes your *manual* verification steps (browser clicks, endpoint checks) into a project verification skill that loops and `/goal` conditions can call |

## Lifecycle: a pipeline where every stage stands alone

```
loop-scan ──> loop-generate ──> loop-verify ──> loop-status
(discover)    (design)          (mechanize       (maintain)
                                 the "done"
                                 standard)
```

Each skill consumes the previous one's output when present, but none requires it: generate a
loop from scratch without a scan; run loop-verify just to harden one hook's check; run
loop-status on any project with a `.loops/` folder. Scan findings are classified **loop / hook
/ skill** — loops (recurring, stateful, verification-bearing work) are the first-class output;
hooks and skills are reported as supporting finds, not dressed up as loops.

## Example loops worth building

The most common loop is not a magical fully-autonomous engineer. It is the boring, high-leverage
path from **issue or ticket → draft PR → human review → follow-up**. The loop gathers context,
does bounded work in a branch or worktree, verifies its claims, pushes a reviewable artifact, and
records what happened. The human still owns intent, architecture, risk, and ambiguous judgment.

### Software delivery loops

| Loop | Trigger | What it does | Verification / stop condition |
|---|---|---|---|
| Ticket-to-reviewed-PR | GitHub issue, Linear/Jira ticket, support bug, or labeled backlog item | Reads the ticket, extracts acceptance criteria, creates a worktree, implements the smallest useful change, runs checks, pushes a draft PR, and updates the ticket | Draft PR exists with linked issue, passing relevant checks, changed-files summary, known risks, and a human-review checklist |
| PR review follow-up | Requested changes, new human review comment, stale draft PR | Reads review comments, fixes actionable items, replies with what changed, and escalates ambiguous decisions instead of guessing | All actionable comments are addressed or explicitly escalated; tests rerun; PR body/state updated |
| Broken build fixer | CI failure on a PR, release branch, or main | Pulls failing logs, identifies the likely layer, patches in a worktree, reruns the narrow failing check first, and posts a diagnosis if budget expires | The previously failing job passes, or the loop leaves a concise failure diagnosis with reproduction command |
| Bug reproducer | Support report, issue with repro steps, recurring production error | Converts the report into a failing test, script, fixture, or browser repro before attempting the fix | Repro fails before the fix and passes after; ticket gets the minimal repro and evidence |
| Release readiness | Release branch, tag candidate, scheduled ship window | Checks blockers, changelog, migrations, docs, test status, rollout notes, and rollback plan | Release checklist complete; blockers and risks are surfaced for a human ship/no-ship decision |
| Dependency upgrade | Dependabot PR, security advisory, weekly upgrade window | Applies the upgrade in isolation, fixes compatibility breaks, summarizes changelog risk, and prepares the PR | Tests pass, lockfile diff is expected, advisory is resolved, rollback path is documented |

### Verification loops

| Loop | Trigger | What it does | Verification / stop condition |
|---|---|---|---|
| Manual QA encoder | A human says "I always check this manually" | Interviews for exact commands, URLs, clicks, expected states, and failure signs; turns them into a project verification skill | A reusable verification command/skill exists with evidence capture and pass/fail criteria |
| UI done checker | Agent says a frontend task is complete | Opens the app, drives target flows, checks desktop/mobile layouts, console errors, network failures, and screenshots | Browser check passes; required UI states are visible; screenshots and logs are attached |
| Security diff reviewer | PR touches auth, permissions, secrets, payments, file IO, or network boundaries | Scans the diff, asks targeted security questions, suggests missing guards/tests, and blocks auto-approval on high-risk findings | No high-confidence findings remain, or the PR is marked for human security review |
| Regression sentinel | Nightly, pre-merge, after dependency changes | Runs tests, benchmarks, browser checks, or API probes and compares against known-good state | Drift stays under threshold, or an issue/PR is opened with repro, evidence, and suspected cause |

### Knowledge-work loops

| Loop | Trigger | What it does | Verification / stop condition |
|---|---|---|---|
| Morning brief | Weekday morning | Reads calendar, open PRs, tickets, docs, messages, and previous state; writes a prioritized brief | Brief includes source links, stale items, uncertain items, risks, and asks |
| Status rundown | Before standup, weekly review, manager sync | Synthesizes tickets, PRs, commits, docs, and previous status into done/doing/blocked/risks/asks | Status file is source-linked and separates facts from interpretation |
| Meeting follow-up | Transcript appears or calendar event ends | Extracts decisions, owners, deadlines, action items, and unresolved questions; drafts the follow-up | Draft is source-backed, owners are explicit, ambiguous items are marked for review |
| Research monitor | Daily/weekly watchlist over Reddit, X/Twitter, docs, competitors, papers, GitHub issues, or forums | Finds novel/relevant changes, clusters them, and recommends what deserves attention | Digest contains links, novelty notes, confidence, and suggested next action |
| Inbox triage | Scheduled sweep or new-message threshold | Clusters messages by urgency/topic, drafts replies, flags decisions, and updates state | No-send drafts are prepared; urgent items are surfaced; uncertain classifications are marked |
| Decision log keeper | New planning doc, PR, meeting notes, or design thread | Captures decisions, alternatives rejected, owners, evidence, and revisit dates | Decision record exists with links and explicit non-goals |

Good loops do not remove human judgment. They move it to the right place: the loop handles
repeatable discovery, implementation, verification, and bookkeeping; the human reviews intent,
risk, architecture, ownership, and ambiguous decisions.

## The `.loops/` convention (per project)

Every skill in the family reads/writes the same per-project structure:

```
<project>/.loops/
├── LOOPS.md            # registry: one row per loop (status, mechanism, cadence, last run)
├── reports/            # loop-scan reports + .digest/ cache
└── <loop-name>/
    ├── loop.md         # the spec: purpose, trigger, stop condition, verification, budget, escalation
    ├── state.md        # cross-run memory: done / next / findings (the loop's spine)
    └── runs.log        # append-only, one line per run
```

## Install (Claude Code first; Codex port later)

```bash
./scripts/install.sh        # copies skills/* to ~/.claude/skills/
```

The SKILL.md format is shared with Codex; porting later = copying to `~/.codex/skills/` and
swapping the mechanism wiring (Claude: /goal, /loop, cron/schedule, hooks, GH Actions ↔
Codex: /goal, Automations tab).

## Dev workflow

- Source of truth: `skills/` here. Edit here, re-run `scripts/install.sh`.
- Evals live in `evals/`.
- Run artifacts live locally in `loops-workspace/iteration-N/` and are intentionally ignored:
  reports and digests may contain private prompts, tickets, credentials, or customer data.
