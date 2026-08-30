#!/usr/bin/env python3
"""QC gate for align/ch_*.json -- catches a silently-wrong alignment.

The matcher anchors line starts onto detected silences, so "did it land on a pause" is
circular. This checks something the matcher never optimises for: the implied speaking rate.
Azure TTS reads at a near-constant chars/sec, so if lines were mapped to the wrong audio the
implied rate for those lines goes wildly out of range even though every anchor is a real pause.

    py -3.12 character_scene_video/verify_alignment.py 1 50 [--project NAME]
"""
import json
import re
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from align_chapter import find_files, speakable, scene_span  # noqa: E402
from charvid_project import pop_project_arg                  # noqa: E402

# an outlier line is one whose implied rate is this many times off the chapter median
RATE_TOL = 3.0
# tolerated share of rate outliers before the gate fails (block 1 currently sits at ~0.9%)
OUTLIER_BUDGET = 0.02


def check(ch, P):
    f = P.align_dir / f"ch_{ch}.json"
    if not f.exists():
        return {"chapter": ch, "fatal": ["no alignment file"]}
    a = json.loads(f.read_text(encoding="utf-8"))
    txt, _ = find_files(ch, P)
    lines = txt.read_text(encoding="utf-8").split("\n")
    fatal, warn = [], []

    times = {int(k): v for k, v in a["lines"].items()}
    ordered = sorted(times)

    # 1. structural: monotonic, non-negative, inside the audio
    prev_end = -1.0
    for ln in ordered:
        s, e = times[ln]
        if e < s - 0.001:
            fatal.append(f"L{ln}: end<start")
        if s < prev_end - 0.35:          # small overlap tolerated (anchor is a pause span)
            fatal.append(f"L{ln}: starts {prev_end - s:.2f}s before previous line ended")
        if e > a["duration"] + 0.5:
            fatal.append(f"L{ln}: ends past end of audio")
        prev_end = e

    # 2. coverage: aligned lines must be exactly the non-empty lines of the source
    src = {i + 1 for i, l in enumerate(lines) if l.strip()}
    if src != set(ordered):
        miss, extra = src - set(ordered), set(ordered) - src
        fatal.append(f"line-set mismatch (missing {len(miss)}, extra {len(extra)})")

    # 3. every scene must resolve to a real, forward-going span
    sc = json.loads((P.scenes_dir / f"ch_{ch}.json").read_text(encoding="utf-8"))["scenes"]
    rec = {"lines": times}
    prev = None
    for s in sc:
        span = scene_span(rec, s["line_start"], s["line_end"])
        if span is None:
            fatal.append(f"scene L{s['line_start']}-{s['line_end']} has no timestamp")
            continue
        if span[1] <= span[0]:
            fatal.append(f"scene L{s['line_start']}-{s['line_end']} is zero/negative length")
        if prev is not None and span[0] < prev - 0.35:
            fatal.append(f"scene L{s['line_start']} starts before the previous scene ended")
        prev = span[1]

    # 4. independent signal: implied speaking rate per line
    rates = []
    for ln in ordered:
        s, e = times[ln]
        dur = e - s
        n = speakable(lines[ln - 1])
        if dur > 0.4 and n > 40:          # ignore very short lines (pause noise dominates)
            rates.append((ln, n / dur))
    if not rates:
        return {"chapter": ch, "fatal": fatal, "warn": warn, "median_rate": 0, "outliers": []}
    med = statistics.median(r for _, r in rates)
    out = [(ln, r) for ln, r in rates if r > med * RATE_TOL or r < med / RATE_TOL]
    return {"chapter": ch, "fatal": fatal, "warn": warn, "median_rate": med,
            "n_rated": len(rates), "outliers": out,
            "rate_spread": (min(r for _, r in rates), max(r for _, r in rates))}


def main():
    P, rest = pop_project_arg(sys.argv[1:])
    a = int(rest[0])
    b = int(rest[1]) if len(rest) > 1 else a
    recs = [check(c, P) for c in range(a, b + 1)]
    meds = [r["median_rate"] for r in recs if r.get("median_rate")]
    n_fatal = sum(len(r["fatal"]) for r in recs)
    n_out = sum(len(r.get("outliers", [])) for r in recs)
    n_rated = sum(r.get("n_rated", 0) for r in recs)

    for r in recs:
        if r["fatal"]:
            print(f"ch{r['chapter']} FATAL:")
            for m in r["fatal"][:6]:
                print(f"    {m}")
        if r.get("outliers"):
            print(f"ch{r['chapter']} rate outliers ({len(r['outliers'])}): "
                  + ", ".join(f"L{ln}@{rt:.1f}c/s" for ln, rt in r["outliers"][:6]))

    rate = n_out / n_rated if n_rated else 0.0
    print(f"\nchapters checked      : {len(recs)}")
    print(f"structural errors     : {n_fatal}")
    print(f"lines rate-checked    : {n_rated}")
    print(f"rate outliers (>{RATE_TOL}x): {n_out}  ({rate:.2%})")
    if meds:
        print(f"median chars/sec      : {statistics.median(meds):.2f} "
              f"(per-chapter range {min(meds):.2f}-{max(meds):.2f})")
    # Some outliers are real speech rather than bad alignment: chants and trailing ellipses do
    # read very slowly. Demanding zero would make this gate cry wolf every run, so allow a small
    # tail and fail hard on anything structural, which is never legitimate.
    ok = n_fatal == 0 and rate <= OUTLIER_BUDGET
    print(f"RESULT: {'PASS' if ok else 'REVIEW NEEDED'}   "
          f"(budget: 0 structural, <={OUTLIER_BUDGET:.0%} rate outliers)")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
