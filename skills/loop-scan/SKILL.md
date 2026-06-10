---
name: loop-scan
description: Scan Claude Code and Codex session history to find automation opportunities, classified as loops (recurring/long-process work with verification needs — the priority), hooks (event-triggered checks), or skills (context to encode once). Produces a ranked Loop Opportunities Report in .loops/reports/. Use whenever the user asks "what can I automate", "find loop opportunities", "scan my sessions", "what do I keep doing manually", "我经常重复做什么", or wonders aloud that they keep doing the same tasks in their AI coding sessions.
---

# loop-scan — find the loops hiding in your session history

Your past sessions are evidence. Anything the user asked an agent to do three times by hand is a
candidate for automation. This skill turns raw transcripts into a ranked report — loops first
(that's where the leverage is), hooks and skills as supporting finds — each with evidence, a
proposed shape, and a cost caution.

**Never read raw session logs directly.** Codex history alone can be gigabytes. Always digest
first, analyze second.

## Step 0 — Bootstrap

If `./.loops/` doesn't exist in the current project, create `.loops/reports/` and a minimal
`.loops/LOOPS.md` (see the registry stub at the bottom of this file). The report belongs to the
project you're standing in, even though the scan covers all projects.

## Step 1 — Digest (script does the heavy lifting)

Run the bundled digester:

```bash
python3 {skill_dir}/scripts/digest.py --days 90 --out .loops/reports/.digest
```

(`--claude-dir` / `--codex-dir` override the default `~/.claude` / `~/.codex` when the user
points you at history stored elsewhere.)

It extracts only user prompts + session metadata from:
- `~/.claude/projects/*/*.jsonl` (Claude Code transcripts)
- `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl` (Codex; date-filtered by filename before opening)
- `~/.codex/history.jsonl` (if fresh — it is sometimes stale, the script checks)

Outputs in the digest dir:
- `summary.md` — read this FIRST: top repeated prompt clusters, schedule-language hits,
  babysat sessions, busiest projects
- `prompts.jsonl` — every user prompt `{source, project, session, ts, text}`; grep it
  selectively, don't read it whole
- `sessions.jsonl` — per-session metadata (prompt count, line count ≈ session length)

If the script fails on an unexpected transcript format, fix the script (it's defensive but
formats evolve), don't fall back to reading raw logs.

## Step 2 — Analyze for the five signals

Read `summary.md`, then grep `prompts.jsonl` to verify and enrich each candidate. You're looking
for these patterns — the *why* behind each tells you what kind of loop fixes it:

1. **Repeated asks** — near-identical prompts across sessions/days ("summarize my email",
   "grade the next batch", "check CI"). The user is the cron daemon. → scheduled loop
   (cron / `/schedule` / Codex Automation).
2. **Babysat sessions** — long sessions dense with "continue", "继续", "keep going", "try again",
   short corrective nudges. The user is the stop-condition evaluator. → `/goal` with a
   machine-verifiable condition, plus encoded verification.
3. **Re-explained context** — the same project background, conventions, or constraints pasted
   into multiple sessions. The user is paying intent debt every session. → a project skill
   (not a loop per se; still report it — skills are what loops call).
4. **Schedule-flavored language** — "every morning", "again", "as usual", "tomorrow",
   "每天", "定期", "像往常一样", "提醒我". The user already thinks of it as recurring. → highest-
   confidence scheduled-loop candidates; the summary pre-greps these.
5. **Follow-up obligations** — sessions ending with deferred work ("check this tomorrow",
   "after CI passes, merge"). → one-shot scheduled task or event hook.

Cluster semantically, not just lexically — "grade assignment 4" and "mark the next homework
batch" are the same loop. Use the cluster counts in summary.md as a starting point, not the
final answer.

## Step 2.5 — Classify before you rank

Not every repetition is a loop. Sort each candidate into the shape that fits — the user's
leverage comes mostly from loops, so never inflate a hook or skill into one:

- **Loop** — recurring or runs-until-done work with its own goal, state that matters across
  runs, and a verification need (today usually vague human judgment). These get ranked.
- **Hook** — deterministic, stateless, event-triggered check or action at a lifecycle moment
  (pre-commit review, post-edit format). Cheap to wire, real value — but a different section.
- **Skill** — knowledge the user re-explains every session that should be encoded once.
  Skills are what loops call; report them as enablers.

For each loop, also mark **verification readiness**: `ready` (a machine-checkable done-condition
already exists) or `needs-encoding` (the standard lives in the user's head — route through
loop-verify before automating, or the loop will ship slop unattended).

## Step 3 — Write the report

Write `.loops/reports/loop-opportunities-<YYYY-MM-DD>.md` with exactly this structure:

```markdown
# Loop Opportunities — <date>
Scanned: <N> Claude sessions, <M> Codex sessions, <window> days

## Ranked loop opportunities
### 1. <short name>
- **Signal**: <which of the five signals>
- **Evidence**: <frequency, projects, date range, 2-3 short quoted prompts with dates>
- **Proposed loop**: <mechanism + cadence + one-line workflow>
- **Stop/verification**: <how the loop proves it's done or healthy> (readiness: ready | needs-encoding)
- **Payoff**: <time saved per week, sessions eliminated>
- **Cost caution**: <est. runs/week × rough tokens per run; flag anything heavy>
- **Confidence**: high / medium / low
...
## Hook opportunities (event-triggered, deterministic)
## Skill opportunities (context to encode once)
## Not worth automating (and why)
## Next step
Run loop-generate on loop #1: <one-line suggested invocation>
```

Rank loops by `(frequency × pain) / token cost`. A daily 2-minute manual task beats a monthly
1-hour one. Include the "not worth automating" section — restraint is what keeps the user
trusting the reports; a one-off task or one needing fresh human judgment every run is not a loop.

If the history is mostly spontaneous one-off work (common for exploratory developers), say so
plainly: a thin loops section with strong hook/skill sections is an honest, useful result.
Knowledge-worker patterns (inbox triage, recurring reports, batch grading) are where loops
cluster — developer histories often yield more hooks and skills than loops.

## Step 4 — Present

Give the user the top 3–5 in chat (name, evidence one-liner, proposed shape), link the report
file, and suggest running `loop-generate` on the top pick. Don't auto-generate loops — choosing
what runs unattended is the user's call.

Privacy note: the digest contains the user's prompt history. It stays inside `.loops/reports/.digest/`
on their machine; never send it anywhere or quote sensitive content (credentials, names in
grading data) into the report.

## Registry stub (for Step 0)

```markdown
# Loops registry
| Loop | Status | Mechanism | Cadence | Last run | Notes |
|---|---|---|---|---|---|
```
