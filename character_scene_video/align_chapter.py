#!/usr/bin/env python3
"""Forced alignment (structural) of a chapter's formatted text against its TTS mp3.

Why not aeneas/WhisperX: the audio is Azure TTS read from the exact text we already have, so
we do not need acoustic modelling to find where each line starts. The synthesiser emits a
clear pause at every sentence end, so the sentence sequence in the text and the silence
sequence in the audio are the same sequence. We detect silences with ffmpeg and match the two
monotonically with a DP that tolerates a few extra/missing gaps.

Output: align/ch_<N>.json -- start/end seconds for every non-empty LINE of the source text
(line numbers are 1-based and match the line_start/line_end in timelines/scenes/ch_<N>.json).

    py -3.12 character_scene_video/align_chapter.py 1 50 [--project NAME]
"""
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from charvid_project import pop_project_arg  # noqa: E402

# silencedetect settings. Pauses are bimodal (clause ~0.2-0.5s, sentence ~0.7-1.0s), but
# pre-filtering to the long mode is a mistake: the two modes overlap, and every real boundary
# thrown away before matching is one the DP can only guess at. Offering it every detected
# silence and letting PENALTY_UNUSED_GAP discard the extras cut rate outliers by two thirds
# over ch1-12 (22 -> 7). Detecting finer than ~0.12s starts adding noise back.
NOISE_DB = "-35dB"
DETECT_MIN = 0.12
MIN_GAP = 0.15

# DP penalties (seconds). Leaving a real boundary unplaced distorts timing far more than
# ignoring a spurious pause, so an unmatched boundary is expensive: nearly every text sentence
# really does have a pause in the audio, and extra gaps (ellipses make the voice pause twice)
# are the common artefact. Swept over ch1-50 -- at 80 every scene boundary lands on a detected
# silence; lower values start interpolating scene starts inside multi-second windows.
PENALTY_UNMATCHED_BOUNDARY = 80.0
PENALTY_UNUSED_GAP = 0.5
REFIT_PASSES = 6
# an anchor implying a local rate this many times off the chapter median is not trusted
RATE_TOL = 2.5
# how many times to drop a spurious gap and re-solve
REPAIR_PASSES = 6

SENT_END = re.compile(r'(?<=[.!?\u2026])["\u201d\u2019\')\]]*\s+')


def find_files(ch, P):
    return P.chapter_text(ch), P.chapter_audio(ch)


def split_units(txt_path, title_echo=False):
    """-> (units, lines) where units = [(line_no, text)] in reading order, one per sentence.

    title_echo: book-1's MP3s were synthesised before epub_to_text learned to drop the leading
    body echo of the chapter title, so the audio reads the bare title a second time between the
    "Chapter N: X" header and the body. The text no longer contains it. When set, we insert that
    extra spoken unit (billed to header line 2, which no scene references) so the sentence
    sequence matches what the voice actually said. process() decides per chapter via has_title_echo().
    """
    lines = txt_path.read_text(encoding="utf-8").split("\n")
    units = []
    for i, raw in enumerate(lines):
        s = raw.strip()
        if not s:
            continue
        parts = [p.strip() for p in SENT_END.split(s) if p.strip()] or [s]
        for p in parts:
            units.append((i + 1, p))
        if title_echo and i == 1:
            bare = re.sub(r"^Chapter\s+\d+\s*:\s*", "", s).strip()
            if bare:
                units.append((2, bare))
    return units, lines


def speakable(text):
    """Rough duration proxy: characters the voice actually renders."""
    return max(1, len(re.sub(r"\s+", "", text)))


def detect_silences(mp3):
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(mp3),
         "-af", f"silencedetect=noise={NOISE_DB}:d={DETECT_MIN}", "-f", "null", "-"],
        capture_output=True, text=True)
    err = proc.stderr
    starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", err)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", err)
    if not m:
        raise RuntimeError(f"no duration from ffmpeg for {mp3}")
    total = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    # silence_end is missing when the file ends inside a silence; clamp that pair to EOF.
    if len(ends) < len(starts):
        ends = ends + [total] * (len(starts) - len(ends))
    return [(max(0.0, s), e) for s, e in zip(starts, ends)], total


def speech_clock(silences, total):
    """Map wall time -> speech-only time (wall minus all silence before it).

    This removes the circularity in predicting boundary times: pauses are not speech, so
    char-proportional prediction should run on the speech clock, not the wall clock.
    """
    cuts = []          # (wall_time, cumulative_silence_before_it)
    cum = 0.0
    for s, e in silences:
        cuts.append((s, cum))
        cum += (e - s)
        cuts.append((e, cum))
    total_speech = total - cum

    def to_speech(t):
        prior = 0.0
        for wall, c in cuts:
            if wall <= t:
                prior = c
            else:
                break
        return max(0.0, t - prior)

    return to_speech, total_speech


def _dp_match(pred, gap_speech):
    """Monotone match of boundaries to gaps. -> {boundary_index: gap_index}."""
    nb, ng = len(pred), len(gap_speech)
    INF = float("inf")
    dp = [[INF] * (ng + 1) for _ in range(nb + 1)]
    bt = [[None] * (ng + 1) for _ in range(nb + 1)]
    dp[0][0] = 0.0
    for i in range(nb + 1):
        for j in range(ng + 1):
            cur = dp[i][j]
            if cur == INF:
                continue
            if i < nb and j < ng:
                c = cur + abs(gap_speech[j] - pred[i])
                if c < dp[i + 1][j + 1]:
                    dp[i + 1][j + 1], bt[i + 1][j + 1] = c, ("match", i, j)
            if i < nb:
                c = cur + PENALTY_UNMATCHED_BOUNDARY
                if c < dp[i + 1][j]:
                    dp[i + 1][j], bt[i + 1][j] = c, ("skipb", i, j)
            if j < ng:
                c = cur + PENALTY_UNUSED_GAP
                if c < dp[i][j + 1]:
                    dp[i][j + 1], bt[i][j + 1] = c, ("skipg", i, j)

    # walk back
    i, j = nb, ng
    matched = {}
    while i or j:
        kind, pi, pj = bt[i][j]
        if kind == "match":
            matched[pi] = pj
            i, j = pi, pj
        elif kind == "skipb":
            i = pi
        else:
            j = pj
    return matched, dp[nb][ng]


def _refit(pred, matched, chars, gap_speech, total_speech):
    """Re-predict boundary times from the matched anchors, discarding implausible ones.

    A single global char-rate drifts badly over a 10-minute chapter (dialogue reads faster than
    narration), so predictions must follow the anchors. But pinning every prediction onto whatever
    the DP matched makes the model self-fulfilling: a wrong match becomes a zero-residual anchor
    and the next pass can never undo it. So we first throw out anchors that imply an impossible
    local speaking rate, then interpolate through the survivors. A mis-matched boundary shows up
    as a segment read absurdly fast or slow, gets dropped here, and is free to re-match next pass.
    """
    nb = len(pred)
    cum, run = [], 0
    for c in chars[:-1]:
        run += c
        cum.append(run)
    total_chars = run + chars[-1]

    pts = [(-1, 0.0, 0.0)] + [(k, float(cum[k]), gap_speech[g]) for k, g in sorted(matched.items())] \
          + [(nb, float(total_chars), total_speech)]

    # local rate implied by each consecutive pair of anchors
    rates = []
    for a in range(len(pts) - 1):
        dc = pts[a + 1][1] - pts[a][1]
        dt = pts[a + 1][2] - pts[a][2]
        rates.append(dc / dt if dt > 1e-6 else float("inf"))
    finite = sorted(r for r in rates if r != float("inf"))
    med = finite[len(finite) // 2] if finite else 1.0

    keep = [pts[0]]
    for a in range(1, len(pts) - 1):
        # an anchor is suspect if either segment touching it implies a wild rate
        left, right = rates[a - 1], rates[a]
        if all(med / RATE_TOL <= r <= med * RATE_TOL for r in (left, right)):
            keep.append(pts[a])
    keep.append(pts[-1])

    out = list(pred)
    for a in range(len(keep) - 1):
        k0, c0, t0 = keep[a]
        k1, c1, t1 = keep[a + 1]
        span_c = (c1 - c0) or 1.0
        for k in range(max(k0, 0), min(k1, nb)):
            out[k] = t0 + (t1 - t0) * (cum[k] - c0) / span_c
    return out


def align(units, silences, total):
    """Match unit boundaries to detected gaps, repairing spurious ones.

    Trailing ellipses make the voice emit a brief blip between two pauses, so a real sentence
    boundary can appear as two gaps a few tenths of a second apart. The matcher will happily
    put a whole line in that sliver. We detect the physical impossibility afterwards (a 126-char
    line cannot be read in half a second), drop the offending gap, and re-solve.
    """
    all_gaps = [(s, e) for s, e in silences if (e - s) >= MIN_GAP]
    # a silence starting at ~0 is lead-in, not a boundary between two units
    if all_gaps and all_gaps[0][0] < 0.05:
        all_gaps = all_gaps[1:]

    banned = set()
    for _ in range(REPAIR_PASSES):
        bounds, nmatch, nb, ng, cost, matched, live = _solve(
            units, all_gaps, banned, silences, total)
        squeezed = _find_squeezed(units, bounds, total, silences)
        # map the offending boundaries back to positions in the ORIGINAL gap list
        live_ids = [i for i in range(len(all_gaps)) if i not in banned]
        newly = {live_ids[matched[b]] for b in squeezed if b in matched}
        if not newly - banned:
            break
        banned |= newly
    return bounds, nmatch, nb, ng, cost


def _find_squeezed(units, bounds, total, silences):
    """-> boundary indices whose matched gap produced an impossible unit duration."""
    starts, ends = unit_times(units, bounds, total, silences)
    bad = []
    for k, ((_, text), s, e) in enumerate(zip(units, starts, ends)):
        if k == 0:
            continue
        d, n = e - s, speakable(text)
        # a line needing seconds of speech cannot fit in a sub-0.6s sliver; and NO line fits in
        # ~nothing (e.g. a boundary matched to the file's trailing silence squeezes the final
        # short line to zero -- too short for the rate test above to catch)
        if (d < 0.6 and n / max(d, 0.01) > 45 and n > 30) or d < 0.05:
            bad.append(k - 1)          # the boundary that opened this unit is the bad one
    return bad


def _solve(units, all_gaps, banned, silences, total):
    gaps = [g for i, g in enumerate(all_gaps) if i not in banned]

    to_speech, total_speech = speech_clock(silences, total)

    chars = [speakable(t) for _, t in units]
    total_chars = sum(chars)
    # predicted speech-clock time of boundary k (between unit k-1 and unit k)
    pred, run = [], 0
    for c in chars[:-1]:
        run += c
        pred.append(run / total_chars * total_speech)

    nb, ng = len(pred), len(gaps)
    gap_speech = [to_speech(s) for s, _ in gaps]

    # iterate: match, refit the rate model through the anchors we trust, match again
    matched, cost = {}, float("inf")
    for _ in range(REFIT_PASSES):
        new, cost = _dp_match(pred, gap_speech)
        if new == matched:
            break
        matched = new
        pred = _refit(pred, matched, chars, gap_speech, total_speech)

    # boundary times; unmatched boundaries get interpolated between their matched neighbours
    bounds = [None] * nb
    for k, g in matched.items():
        bounds[k] = gaps[g]
    first_speech = silences[0][1] if silences and silences[0][0] < 0.05 else 0.0
    _interpolate(bounds, chars, first_speech, total)
    return bounds, len(matched), nb, ng, cost, matched, gaps


def _interpolate(bounds, chars, t0, total):
    """Fill None boundaries by char-share between the nearest known anchors."""
    n = len(bounds)
    anchors = [(-1, (t0, t0))] + [(k, b) for k, b in enumerate(bounds) if b] + [(n, (total, total))]
    for a in range(len(anchors) - 1):
        k0, b0 = anchors[a]
        k1, b1 = anchors[a + 1]
        if k1 - k0 <= 1:
            continue
        span_start, span_end = b0[1], b1[0]
        seg = chars[k0 + 1:k1 + 1]
        tot = sum(seg) or 1
        run = 0
        for off, c in enumerate(seg[:-1]):
            run += c
            t = span_start + (span_end - span_start) * run / tot
            bounds[k0 + 1 + off] = (t, t)


def unit_times(units, bounds, total, silences):
    """-> (starts, ends) per unit. Unit k runs from the end of gap k-1 to the start of gap k."""
    first = silences[0][1] if silences and silences[0][0] < 0.05 else 0.0
    starts, ends = [], []
    for k in range(len(units)):
        starts.append(first if k == 0 else bounds[k - 1][1])
        ends.append(total if k == len(units) - 1 else bounds[k][0])
    return starts, ends


def fit_score(units, bounds, total, silences):
    """How plausible are the speaking rates this alignment implies? Lower is better.

    This is the signal the matcher does NOT optimise for, which is exactly why it can arbitrate
    between candidate alignments. _refit pins predictions onto whatever the DP matched, so the
    DP's own cost collapses toward zero for any monotone matching -- including one shifted a unit
    off by a title echo. Implied chars/sec cannot be gamed that way: a shifted alignment forces
    some unit to be read impossibly fast and its neighbour impossibly slowly.
    """
    starts, ends = unit_times(units, bounds, total, silences)
    rates = []
    for (_, text), s, e in zip(units, starts, ends):
        d = e - s
        n = speakable(text)
        if d > 0.25 and n >= 25:      # short units are dominated by pause edges, not speech
            rates.append(n / d)
    if len(rates) < 8:
        return float("inf")
    rates.sort()
    med = rates[len(rates) // 2]
    if med <= 0:
        return float("inf")
    # mean absolute log-deviation: symmetric in "twice too fast" vs "twice too slow"
    import math
    return sum(abs(math.log(r / med)) for r in rates) / len(rates)


def line_times(units, bounds, total, silences):
    """-> {line_no: [start, end]} covering every non-empty line."""
    starts, ends = unit_times(units, bounds, total, silences)
    per = {}
    for (ln, _), s, e in zip(units, starts, ends):
        if ln in per:
            per[ln][1] = e
        else:
            per[ln] = [s, e]
    return per


def has_title_echo(txt_path, silences, total):
    """Does this MP3 read the chapter title twice?

    Book-1's audio predates epub_to_text dropping the leading body echo of the title, so almost
    every chapter has one. Rather than infer it from a whole-chapter fit (a two-unit error at the
    opening is diluted to nothing across ~180 units), test the opening directly: the third spoken
    segment is either the echoed title or the first body sentence, and at the chapter's own
    speaking rate those two have very different expected lengths.
    """
    lines = txt_path.read_text(encoding="utf-8").split("\n")
    title = lines[1].strip() if len(lines) > 1 else ""
    bare = re.sub(r"^Chapter\s+\d+\s*:\s*", "", title).strip()
    body = next((l.strip() for l in lines[2:] if l.strip()), "")
    if not bare or not body:
        return False

    segs = [(silences[i][1], silences[i + 1][0]) for i in range(len(silences) - 1)]
    if len(segs) < 3:
        return False
    seg3 = segs[1][1] - segs[1][0]

    all_chars = sum(speakable(l) for l in lines if l.strip())
    speech = total - sum(e - s for s, e in silences)
    rate = all_chars / speech if speech > 0 else 14.3

    first_sent = next(iter([p for p in SENT_END.split(body) if p.strip()]), body)
    d_echo = abs(seg3 - speakable(bare) / rate)
    d_body = abs(seg3 - speakable(first_sent) / rate)
    # ties go to "echo present": it is the overwhelmingly common case for this corpus
    return d_echo <= d_body


def load(ch, P):
    """Load a chapter's alignment record, or None."""
    f = P.align_dir / f"ch_{ch}.json"
    if not f.exists():
        return None
    rec = json.loads(f.read_text(encoding="utf-8"))
    rec["lines"] = {int(k): v for k, v in rec["lines"].items()}
    return rec


def scene_span(rec, line_start, line_end):
    """Seconds [start, end] for a scene's line range.

    Scene tags sometimes point at a blank separator line (the tagger counted raw lines, and only
    non-empty lines carry audio), so snap the start forward and the end backward to the nearest
    line that was actually spoken.
    """
    have = sorted(rec["lines"])
    lo = next((l for l in have if l >= line_start), None)
    hi = next((l for l in reversed(have) if l <= line_end), None)
    if lo is None or hi is None or lo > hi:
        return None
    return [rec["lines"][lo][0], rec["lines"][hi][1]]


def process(ch, P, verbose=True):
    txt, mp3 = find_files(ch, P)
    if not txt or not mp3:
        return {"chapter": ch, "error": f"missing {'text' if not txt else 'audio'}"}
    silences, total = detect_silences(mp3)

    echo = has_title_echo(txt, silences, total)
    units, _ = split_units(txt, title_echo=echo)
    bounds, nmatch, nb, ng, cost = align(units, silences, total)
    score = fit_score(units, bounds, total, silences)
    per = line_times(units, bounds, total, silences)

    matched_frac = nmatch / nb if nb else 1.0
    rec = {
        "chapter": ch,
        "audio": str(mp3),
        "duration": round(total, 3),
        "title_echo": echo,
        "units": len(units),
        "gaps_detected": ng,
        "boundaries_matched": nmatch,
        "boundaries_total": nb,
        "match_rate": round(matched_frac, 4),
        "dp_cost": round(cost, 2),
        "fit_score": round(score, 4),
        "lines": {str(k): [round(v[0], 3), round(v[1], 3)] for k, v in sorted(per.items())},
    }
    P.align_dir.mkdir(exist_ok=True)
    (P.align_dir / f"ch_{ch}.json").write_text(json.dumps(rec, indent=1), encoding="utf-8")
    if verbose:
        flag = "" if matched_frac >= 0.97 else "   <-- LOW"
        print(f"ch{ch:>4}  {total/60:6.2f}min  units={len(units):<4} gaps={ng:<4} "
              f"matched={nmatch}/{nb} ({matched_frac:.1%})  echo={'Y' if echo else 'n'}{flag}")
    return rec


def main():
    P, rest = pop_project_arg(sys.argv[1:])
    a = int(rest[0])
    b = int(rest[1]) if len(rest) > 1 else a
    recs = [process(c, P) for c in range(a, b + 1)]
    ok = [r for r in recs if "error" not in r]
    bad = [r for r in recs if "error" in r]
    low = [r for r in ok if r["match_rate"] < 0.97]
    print(f"\naligned {len(ok)} chapter(s); errors={len(bad)}; below 97% match={len(low)}")
    if low:
        print("  low: " + ", ".join(f"ch{r['chapter']}({r['match_rate']:.1%})" for r in low))
    for r in bad:
        print(f"  ERROR ch{r['chapter']}: {r['error']}")


if __name__ == "__main__":
    main()
