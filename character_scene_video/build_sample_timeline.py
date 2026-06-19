#!/usr/bin/env python3
"""
Build the SAMPLE Scene Timeline (content pass) for the character-scene video test.

Scene boundaries/casts come from Claude reading the chapters (see DESIGN.md §10).
Durations here are ESTIMATES: each scene's share of its chapter's body characters x the
chapter's known audio duration (placeholder until forced alignment, M3). Batch-relative
start offsets accumulate across chapters in order.

Outputs:
  character_scene_video/timelines/block_01_ch001-050_SAMPLE.md   (+ .json)
  character_scene_video/timelines/ch215_sherlock_SAMPLE.md
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FT = ROOT / "formatted_text" / "lotm_book1"
OUT = Path(__file__).resolve().parent / "timelines"
OUT.mkdir(exist_ok=True)

# Audio durations (seconds) from D:/PDFReader/lotm_book1_output/_durations.csv
DUR = {1: 620.952, 2: 808.104, 3: 799.008, 4: 945.528, 5: 890.232,
       6: 805.320, 7: 778.032, 215: 856.704}

KB = "Klein Moretti (Beginning of the Series).jpg"
FILES = {
    1: FT / "Volume_1_Clown" / "Chapter_1_Crimson.txt",
    2: FT / "Volume_1_Clown" / "Chapter_2_Situation.txt",
    3: FT / "Volume_1_Clown" / "Chapter_3_Melissa.txt",
    4: FT / "Volume_1_Clown" / "Chapter_4_Divination.txt",
    5: FT / "Volume_1_Clown" / "Chapter_5_Ritual.txt",
    6: FT / "Volume_1_Clown" / "Chapter_6_Beyonder.txt",
    7: FT / "Volume_1_Clown" / "Chapter_7_Call_Sign.txt",
    215: FT / "Volume_2_Faceless" / "Chapter_215_Mrs._Sammer.txt",
}

# (line_start, line_end, characters, images, text_anchor, flag)
SCENES = {
    1: [
        (3, 92, ["Klein (as Zhou Mingrui)"], ["Zhou Mingrui.jpg"], "Painful! How painful! My head hurts so badly!", ""),
        (93, 145, ["Klein (Beginning)"], [KB], "Klein Moretti, a citizen of the Northern Continent's Loen Kingdom...", "persona switch mid-chapter"),
    ],
    2: [
        (3, 153, ["Klein (Beginning)"], [KB], "Tap! Tap! Tap! Zhou Mingrui reeled back in fear", ""),
    ],
    3: [
        (3, 21, ["Klein (Beginning)"], [KB], "After confirming his plan, Zhou Mingrui immediately felt", ""),
        (23, 129, ["Klein (Beginning)"], [KB], "Melissa is awake... She's really as punctual", "Melissa present but no portrait"),
        (131, 139, ["Klein (Beginning)"], [KB], "Simultaneously, he repeated the word 'Sunday'", ""),
    ],
    4: [
        (3, 63, ["Klein (Beginning)"], [KB], "Returning to his chair again, he heard the faraway", ""),
        (65, 101, ["Klein (Beginning)"], [KB], "The corridor during the day remained dim", ""),
        (103, 153, ["Klein (Beginning)"], [KB], "The owner of the bakery was a seventy-plus year", ""),
        (155, 204, ["Klein (Beginning)"], [KB], "There was a municipal square at the intersection", ""),
    ],
    5: [
        (3, 91, ["Klein (Beginning)"], [KB], "Free? Free things cost the most!", ""),
        (93, 167, ["Klein (Beginning)"], [KB], "Zhou Mingrui very quickly put this matter", ""),
        (171, 185, ["Klein (Beginning)"], [KB], "In the Loen Kingdom's capital, Backlund.", "AUDREY POV cutaway — Klein absent; shown via fallback (review)"),
        (189, 197, ["Klein (Beginning)"], [KB], "In the Sonia Sea, a three-masted sailboat", "ALGER POV cutaway — Klein absent; shown via fallback (review)"),
        (201, 211, ["Klein (as The Fool)"], ["The Fool.jpg"], "In the fog of gray mist, Audrey Hall", "first gray-fog / Tarot contact"),
    ],
    6: [
        (3, 9999, ["[ch6 not tagged in sample]"], [KB], "(chapter 6 omitted from sample; placeholder so offsets stay honest)", "UNTAGGED"),
    ],
    7: [
        (3, 133, ["Klein (as The Fool)"], ["The Fool.jpg"], "You can address me as The Fool.", "Tarot Club gathering; other members are vague fog-figures (no portrait)"),
        (135, 167, ["Klein (Beginning)"], [KB], "As for Zhou Mingrui, he felt himself turning", ""),
    ],
    215: [
        (3, 35, ["Klein (as Sherlock Moriarty)"], ["Sherlock Moriarty.jpg"], "Did you see a teenage boy?", ""),
        (37, 147, ["Klein (as Sherlock Moriarty)"], ["Sherlock Moriarty.jpg"], "The rest of the journey happened stably and calmly.", "adopts 'Sherlock Moriarty' name here"),
        (149, 173, ["Klein (as Sherlock Moriarty)"], ["Sherlock Moriarty.jpg"], "After exchanging some pleasantries, Klein was led by", ""),
    ],
}


def body_chars(ch: int, ls: int, le: int) -> int:
    lines = FILES[ch].read_text(encoding="utf-8").splitlines()
    total = 0
    for i in range(ls, min(le, len(lines)) + 1):
        if 1 <= i <= len(lines):
            total += len(lines[i - 1].strip())
    return total


def hms(sec: float) -> str:
    sec = int(round(sec))
    return f"{sec // 3600:d}:{(sec % 3600) // 60:02d}:{sec % 60:02d}"


def build(chapters: list[int], offset0: float = 0.0):
    rows, offset = [], offset0
    for ch in chapters:
        specs = SCENES[ch]
        counts = [max(1, body_chars(ch, s[0], s[1])) for s in specs]
        total = sum(counts)
        for (ls, le, chars, imgs, anchor, flag), cc in zip(specs, counts):
            dur = DUR[ch] * cc / total
            rows.append({
                "chapter": ch, "start": hms(offset), "duration": hms(dur),
                "duration_sec": round(dur, 1), "characters": chars, "images": imgs,
                "text_anchor": anchor, "flag": flag,
            })
            offset += dur
    return rows, offset


def write_md(path: Path, title: str, note: str, rows: list[dict], total: float):
    L = [f"# {title}", "", note, "",
         f"**Total covered:** {hms(total)}  ·  **scenes:** {len(rows)}", "",
         "| Start | Dur | Ch | Characters | Image(s) | Anchor / review note |",
         "|---|---|---|---|---|---|"]
    for r in rows:
        imgs = ", ".join(r["images"]) or "—"
        note_cell = r["text_anchor"]
        if r["flag"]:
            note_cell += f"  ⚠️ _{r['flag']}_" if "review" in r["flag"].lower() or "UNTAGGED" in r["flag"] else f"  ({r['flag']})"
        L.append(f"| {r['start']} | {r['duration']} | {r['chapter']} | "
                 f"{', '.join(r['characters'])} | {imgs} | {note_cell} |")
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


# Block 1 sample: ch 1-7 (ch6 untagged placeholder). Honest contiguous offsets from 00:00:00.
rows1, end1 = build([1, 2, 3, 4, 5, 6, 7])
write_md(OUT / "block_01_ch001-050_SAMPLE.md",
         "Scene Timeline — SAMPLE (Block 1, chapters 1-7 of 1-50)",
         "_Content pass. Durations are char-share ESTIMATES (placeholder until forced alignment). "
         "ch6 is an untagged placeholder; ch8-50 omitted from this sample._",
         rows1, end1)
(OUT / "block_01_ch001-050_SAMPLE.json").write_text(
    json.dumps({"batch": 1, "chapters_sampled": "1-7", "scenes": rows1}, indent=2, ensure_ascii=False),
    encoding="utf-8")

# Ch215 standalone (it lives in Block 5, ch201-250; offsets here are chapter-relative).
rows2, end2 = build([215])
write_md(OUT / "ch215_sherlock_SAMPLE.md",
         "Scene Timeline — SAMPLE (chapter 215, 'Mrs. Sammer' — Sherlock persona)",
         "_Standalone illustration of the Sherlock Moriarty persona. Offsets are chapter-relative "
         "(true Block-5 offset needs ch201-214)._",
         rows2, end2)

print(f"Block 1 sample: {len(rows1)} scenes, covers {hms(end1)}")
print(f"Ch215 sample: {len(rows2)} scenes, covers {hms(end2)}")
print(f"Written to {OUT}")
