#!/usr/bin/env python3
"""Digest Claude Code + Codex session history into a compact, analyzable form.

Raw session logs are huge (Codex sessions can be gigabytes). Never read them raw.
This script extracts ONLY user prompts + session metadata and emits, in --out:

  prompts.jsonl   one line per user prompt: {source, project, session, ts, text}
  sessions.jsonl  one line per session: {source, project, session, started, n_prompts, n_lines}
  summary.md      repeated-prompt clusters, schedule-language hits, babysat sessions,
                  busiest projects -- the starting point for loop-opportunity analysis

Stdlib only. Defensive parsing: transcript formats evolve; skip what we can't parse.
"""

import argparse
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

MAX_TEXT = 400  # truncate stored prompt text

# Prompts injected by harnesses rather than typed by the user.
SKIP_PREFIXES = (
    "<system", "<command", "<local-command", "<task-notification",
    "Caveat:", "[Request interrupted", "# In app browser",
)

SCHEDULE_PATTERNS = re.compile(
    r"every (day|morning|week|night|monday|friday|time)|daily|weekly|each time|whenever|"
    r"as usual|again today|remind me|tomorrow|routine|"
    r"每天|每日|每周|每次|定时|定期|照旧|像往常|老规矩|提醒我|明天",
    re.IGNORECASE,
)

CONTINUATION = re.compile(
    r"^(continue|go on|keep going|try again|next|proceed|ok(ay)?|y(es)?|do it|"
    r"继续|接着|下一个|再试|好的?|可以|嗯)\s*[.!。！]?$",
    re.IGNORECASE,
)


def clean_text(text):
    if not isinstance(text, str):
        return None
    t = text.strip()
    if not t or t.startswith(SKIP_PREFIXES):
        return None
    return t[:MAX_TEXT]


def parse_ts(value):
    """Return epoch seconds from ISO string or number; None if unparseable."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
        except ValueError:
            return None
    return None


def iter_jsonl(path):
    try:
        with open(path, "r", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue
    except OSError:
        return


# ---------------- Claude Code ----------------

def scan_claude(cutoff, prompts, sessions, claude_root):
    root = claude_root / "projects"
    if not root.is_dir():
        return
    for proj_dir in sorted(root.iterdir()):
        if not proj_dir.is_dir():
            continue
        for f in sorted(proj_dir.glob("*.jsonl")):
            try:
                if f.stat().st_mtime < cutoff:
                    continue
            except OSError:
                continue
            cwd, started, n_prompts, n_lines = None, None, 0, 0
            for d in iter_jsonl(f):
                n_lines += 1
                if cwd is None and isinstance(d.get("cwd"), str):
                    cwd = d["cwd"]
                ts = parse_ts(d.get("timestamp"))
                if started is None and ts:
                    started = ts
                text = None
                if d.get("type") == "user" and not d.get("isMeta"):
                    msg = d.get("message")
                    if isinstance(msg, dict):
                        content = msg.get("content")
                        if isinstance(content, str):
                            text = content
                        elif isinstance(content, list):
                            if any(isinstance(b, dict) and b.get("type") == "tool_result"
                                   for b in content):
                                text = None
                            else:
                                text = "\n".join(
                                    b.get("text", "") for b in content
                                    if isinstance(b, dict) and b.get("type") == "text")
                elif d.get("type") == "queue-operation" and d.get("operation") == "enqueue":
                    text = d.get("content")
                text = clean_text(text)
                if text:
                    n_prompts += 1
                    prompts.append({
                        "source": "claude", "project": cwd or proj_dir.name,
                        "session": f.stem, "ts": ts, "text": text,
                    })
            if n_lines:
                sessions.append({
                    "source": "claude", "project": cwd or proj_dir.name,
                    "session": f.stem, "started": started,
                    "n_prompts": n_prompts, "n_lines": n_lines,
                })


# ---------------- Codex ----------------

def scan_codex(cutoff, prompts, sessions, codex_root):
    root = codex_root / "sessions"
    if not root.is_dir():
        return
    cutoff_date = datetime.fromtimestamp(cutoff, tz=timezone.utc).date()
    date_re = re.compile(r"rollout-(\d{4})-(\d{2})-(\d{2})T")
    for f in sorted(root.rglob("rollout-*.jsonl")):
        m = date_re.search(f.name)
        if m:
            try:
                fdate = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)),
                                 tzinfo=timezone.utc).date()
                if fdate < cutoff_date:
                    continue
            except ValueError:
                pass
        cwd, started, n_prompts, n_lines = None, None, 0, 0
        sid = f.stem
        try:
            with open(f, "r", errors="replace") as fh:
                for line in fh:
                    n_lines += 1
                    # cheap pre-filter before JSON-parsing 100k-line files
                    if '"session_meta"' not in line and '"user_message"' not in line:
                        continue
                    try:
                        d = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    payload = d.get("payload") or {}
                    if d.get("type") == "session_meta":
                        cwd = payload.get("cwd") or cwd
                        started = started or parse_ts(payload.get("timestamp")) \
                            or parse_ts(d.get("timestamp"))
                        sid = payload.get("id") or sid
                    elif (d.get("type") == "event_msg"
                          and payload.get("type") == "user_message"):
                        text = clean_text(payload.get("message")
                                          or payload.get("text")
                                          or payload.get("content"))
                        if text:
                            n_prompts += 1
                            prompts.append({
                                "source": "codex", "project": cwd or "?",
                                "session": sid, "ts": parse_ts(d.get("timestamp")),
                                "text": text,
                            })
        except OSError:
            continue
        if n_lines:
            sessions.append({
                "source": "codex", "project": cwd or "?", "session": sid,
                "started": started, "n_prompts": n_prompts, "n_lines": n_lines,
            })


def scan_codex_history(cutoff, prompts, known_sessions, codex_root):
    """history.jsonl is a cheap global prompt log, but it is sometimes stale
    (rotation/disabled). Use it only for sessions we didn't already cover."""
    path = codex_root / "history.jsonl"
    if not path.is_file():
        return
    covered = {s["session"] for s in known_sessions if s["source"] == "codex"}
    for d in iter_jsonl(path):
        ts = parse_ts(d.get("ts"))
        if not ts or ts < cutoff:
            continue
        sid = d.get("session_id", "?")
        if sid in covered:
            continue
        text = clean_text(d.get("text"))
        if text:
            prompts.append({"source": "codex", "project": "?", "session": sid,
                            "ts": ts, "text": text})


# ---------------- Summary ----------------

def cluster_key(text):
    """Cheap normalization so near-identical prompts group together."""
    t = re.sub(r"[\d/:\\.\-_]+", " ", text.lower())
    t = re.sub(r"\s+", " ", t).strip()
    return t[:60]


def short_project(p):
    return p if len(p) <= 45 else "…" + p[-44:]


def fmt_day(ts):
    if not ts:
        return "?"
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")


def write_summary(out_dir, prompts, sessions, days):
    lines = []
    n_claude = sum(1 for s in sessions if s["source"] == "claude")
    n_codex = sum(1 for s in sessions if s["source"] == "codex")
    lines.append("# Session digest summary")
    lines.append(f"Window: last {days} days · Claude sessions: {n_claude} · "
                 f"Codex sessions: {n_codex} · user prompts: {len(prompts)}")
    lines.append("")

    # Repeated prompt clusters
    clusters = defaultdict(list)
    for p in prompts:
        if len(p["text"]) >= 8 and not CONTINUATION.match(p["text"]):
            clusters[cluster_key(p["text"])].append(p)
    # Rank by distinct days, then sessions: "asked 5 different days" is loop signal,
    # "asked 13 times in one afternoon" usually is not.
    def spread(v):
        return (len({fmt_day(p["ts"]) for p in v}), len({p["session"] for p in v}))
    repeated = sorted(((k, v) for k, v in clusters.items() if spread(v)[1] >= 2),
                      key=lambda kv: -spread(kv[1])[0] * 1000 - len(kv[1]))
    lines.append("## Repeated prompt clusters (normalized; ranked by day-spread)")
    if not repeated:
        lines.append("(none found — check prompts.jsonl manually for semantic repeats)")
    for k, v in repeated[:25]:
        days, sess = spread(v)
        dates = sorted(fmt_day(p["ts"]) for p in v)
        projs = sorted({short_project(p["project"]) for p in v})
        lines.append(f"- **{len(v)}× / {sess} sessions / {days} days** `{v[0]['text'][:90]}`")
        lines.append(f"  - {dates[0]} → {dates[-1]}; projects: {', '.join(projs[:3])}")
    lines.append("")

    # Schedule-flavored language
    sched = [p for p in prompts if SCHEDULE_PATTERNS.search(p["text"])]
    lines.append(f"## Schedule-flavored prompts ({len(sched)} hits, showing up to 40)")
    for p in sched[:40]:
        lines.append(f"- [{p['source']} {fmt_day(p['ts'])}] {p['text'][:120]}")
    lines.append("")

    # Babysat sessions: many continuation nudges
    nudges = Counter()
    for p in prompts:
        if CONTINUATION.match(p["text"]):
            nudges[(p["source"], p["session"], p["project"])] += 1
    babysat = [(k, c) for k, c in nudges.items() if c >= 4]
    babysat.sort(key=lambda kc: -kc[1])
    lines.append("## Babysat sessions (>=4 continuation nudges — candidates for /goal + verification)")
    if not babysat:
        lines.append("(none)")
    for (src, sess, proj), c in babysat[:15]:
        lines.append(f"- {c} nudges · {src} · {short_project(proj)} · session {sess[:18]}")
    lines.append("")

    # Busiest projects
    per_proj = Counter(short_project(s["project"]) for s in sessions)
    lines.append("## Sessions per project")
    for proj, c in per_proj.most_common(15):
        lines.append(f"- {c} · {proj}")
    lines.append("")

    # Longest sessions (proxy for grind/fix-loops)
    longest = sorted(sessions, key=lambda s: -s["n_lines"])[:10]
    lines.append("## Longest sessions (grind candidates)")
    for s in longest:
        lines.append(f"- {s['n_lines']} events · {s['n_prompts']} prompts · {s['source']} · "
                     f"{short_project(s['project'])} · {fmt_day(s['started'])}")
    lines.append("")
    lines.append("Next: grep prompts.jsonl to verify/enrich each candidate "
                 "(e.g. `grep -i 'email' prompts.jsonl | head`).")

    (out_dir / "summary.md").write_text("\n".join(lines))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=90)
    ap.add_argument("--out", default=".loops/reports/.digest")
    ap.add_argument("--claude-dir", default=None,
                    help="override ~/.claude (for tests or alternate machines)")
    ap.add_argument("--codex-dir", default=None,
                    help="override ~/.codex (for tests or alternate machines)")
    args = ap.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    cutoff = time.time() - args.days * 86400

    claude_root = Path(args.claude_dir) if args.claude_dir else Path.home() / ".claude"
    codex_root = Path(args.codex_dir) if args.codex_dir else Path.home() / ".codex"
    prompts, sessions = [], []
    scan_claude(cutoff, prompts, sessions, claude_root)
    scan_codex(cutoff, prompts, sessions, codex_root)
    scan_codex_history(cutoff, prompts, sessions, codex_root)
    prompts.sort(key=lambda p: p["ts"] or 0)

    # Resumed/forked Codex sessions replay prior messages into new rollout files;
    # drop exact (source, text, ts) duplicates so one utterance counts once.
    seen, deduped = set(), []
    for p in prompts:
        key = (p["source"], p["text"], round(p["ts"] or 0))
        if key not in seen:
            seen.add(key)
            deduped.append(p)
    prompts = deduped

    with open(out_dir / "prompts.jsonl", "w") as fh:
        for p in prompts:
            fh.write(json.dumps(p, ensure_ascii=False) + "\n")
    with open(out_dir / "sessions.jsonl", "w") as fh:
        for s in sessions:
            fh.write(json.dumps(s, ensure_ascii=False) + "\n")
    write_summary(out_dir, prompts, sessions, args.days)

    print(f"Digest written to {out_dir}/ — {len(sessions)} sessions, "
          f"{len(prompts)} user prompts. Read summary.md first.")


if __name__ == "__main__":
    main()
