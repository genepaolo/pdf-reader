#!/usr/bin/env python3
"""
Build the SAMPLE Scene Timeline (content pass) for the character-scene video test.

Scene boundaries + FULL present-cast come from Claude reading the chapters (DESIGN.md §10).
Each scene records every named character present; images are resolved from _manifest.json;
characters with no portrait become the per-batch "needs an image" list. Durations are ESTIMATES
(char-share x chapter audio duration) until forced alignment (M3). Fallback when no
portrait-bearing character is present = HOLD PREVIOUS FRAME.

Outputs: timelines/block_01_ch001-050_SAMPLE.md (+ .json), timelines/ch215_sherlock_SAMPLE.md
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FT = ROOT / "formatted_text" / "lotm_book1"
MANIFEST = ROOT / "tts_pipeline" / "assets" / "characters" / "lotm" / "_manifest.json"
OUT = Path(__file__).resolve().parent / "timelines"
OUT.mkdir(exist_ok=True)

DUR = {1: 620.952, 2: 808.104, 3: 799.008, 4: 945.528, 5: 890.232,
       6: 805.320, 7: 778.032, 215: 856.704}

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

# protagonist persona -> (display label, image file)
PERSONA = {
    "Zhou Mingrui": ("Klein (as Zhou Mingrui)", "Zhou Mingrui.jpg"),
    "Klein (Beginning)": ("Klein (Beginning)", "Klein Moretti (Beginning of the Series).jpg"),
    "Klein Moretti": ("Klein Moretti", "Klein Moretti.jpg"),
    "The Fool": ("Klein (as The Fool)", "The Fool.jpg"),
    "Sherlock Moriarty": ("Klein (as Sherlock Moriarty)", "Sherlock Moriarty.jpg"),
    "Gehrman Sparrow": ("Klein (as Gehrman Sparrow)", "Gehrman Sparrow.jpg"),
    "Dwayne Dantès": ("Klein (as Dwayne Dantès)", "Dwayne Dantès.jpg"),
    "Merlin Hermes": ("Klein (as Merlin Hermes)", "Merlin Hermes.jpg"),
}
PERSONA_IMAGE_NAMES = {"Zhou Mingrui", "Klein Moretti", "Klein Moretti (Beginning of the Series)",
                       "The Fool", "Sherlock Moriarty", "Gehrman Sparrow", "Dwayne Dantès", "Merlin Hermes"}

# (line_start, line_end, protagonist_present, persona|None, other_characters[], text_anchor)
SCENES = {
    1: [
        (3, 92, True, "Zhou Mingrui", [], "Painful! How painful! My head hurts so badly!"),
        (93, 145, True, "Klein (Beginning)", [], "Klein Moretti, a citizen of the Northern Continent's Loen Kingdom..."),
    ],
    2: [
        (3, 153, True, "Klein (Beginning)", [], "Tap! Tap! Tap! Zhou Mingrui reeled back in fear"),
    ],
    3: [
        (3, 21, True, "Klein (Beginning)", [], "After confirming his plan, Zhou Mingrui immediately felt"),
        (23, 139, True, "Klein (Beginning)", ["Melissa Moretti"], "Melissa is awake... She's really as punctual"),
    ],
    4: [
        (3, 63, True, "Klein (Beginning)", [], "Returning to his chair again, he heard the faraway"),
        (65, 99, True, "Klein (Beginning)", [], "The corridor during the day remained dim"),
        (101, 153, True, "Klein (Beginning)", ["Wendy Smyrin"], "Smyrin Bakery, buying rye bread"),
        (155, 161, True, "Klein (Beginning)", [], "There was a municipal square at the intersection"),
        (163, 204, True, "Klein (Beginning)", ["[fortune-teller]"], "the tarot fortune-teller offers a reading"),
    ],
    5: [
        (3, 91, True, "Klein (Beginning)", ["[circus fortune-teller]", "[real fortune-teller]"], "Free? Free things cost the most!"),
        (93, 99, True, "Klein (Beginning)", [], "Zhou Mingrui very quickly put this matter behind him."),
        (101, 167, True, "Klein (Beginning)", [], "the luck-enhancement ritual; pulled into the gray fog"),
        (169, 185, False, None, ["Audrey Hall"], "In the Loen Kingdom's capital, Backlund. Inside a luxurious"),
        (187, 197, False, None, ["Alger Wilson"], "In the Sonia Sea, a three-masted sailboat"),
        (199, 212, True, "The Fool", ["Audrey Hall", "Alger Wilson"], "In the fog of gray mist, Audrey Hall regained"),
    ],
    6: [
        (3, 9999, True, "Klein (Beginning)", ["[ch6 not tagged in sample]"], "(chapter 6 omitted; placeholder so offsets stay honest)"),
    ],
    7: [
        (3, 133, True, "The Fool", ["[Justice (unidentified)]", "[The Hanged Man (unidentified)]"], "You can address me as The Fool"),
        (135, 168, True, "Klein (Beginning)", [], "As for Zhou Mingrui, he felt himself turning heavy"),
    ],
    215: [
        (3, 21, True, "Sherlock Moriarty", ["[highlander pursuers]", "[train conductor]"], "Did you see a teenage boy?"),
        (23, 35, True, "Sherlock Moriarty", ["[teenage boy fugitive]"], "the red-eyed teenage boy"),
        (37, 45, True, "Sherlock Moriarty", [], "The rest of the journey happened stably"),
        (47, 63, True, "Sherlock Moriarty", ["Julianne", "Stelyn Sammer"], "the maidservant ushers Klein in"),
        (65, 139, True, "Sherlock Moriarty", ["Stelyn Sammer", "Julianne"], "The mistress was in her thirties."),
        (141, 147, True, "Sherlock Moriarty", ["Stelyn Sammer", "Luke Sammer", "[male servant]"], "the door suddenly opened"),
        (149, 153, True, "Sherlock Moriarty", ["Julianne"], "After exchanging some pleasantries, Klein was led"),
        (155, 173, True, "Sherlock Moriarty", [], "Empty Unit 15; Klein alone deliberates"),
    ],
}


def load_images() -> dict:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    avail = {}
    for m in manifest:
        if m["kind"] != "character" or m["name"] in PERSONA_IMAGE_NAMES or not m["row_viable"]:
            continue
        ext = "png" if m["mime"] == "image/png" else "jpg"
        avail[m["name"]] = f"{m['name']}.{ext}"
    return avail


def body_chars(ch: int, ls: int, le: int) -> int:
    lines = FILES[ch].read_text(encoding="utf-8").splitlines()
    return sum(len(lines[i - 1].strip()) for i in range(ls, min(le, len(lines)) + 1) if 1 <= i <= len(lines))


def hms(sec: float) -> str:
    sec = int(round(sec))
    return f"{sec // 3600:d}:{(sec % 3600) // 60:02d}:{sec % 60:02d}"


AVAIL = load_images()
# 384 Book 1 characters with their own wiki article — the "important" bar.
REGISTRY = set(json.loads(
    (Path(__file__).resolve().parent / "character_registry.json").read_text(encoding="utf-8")
)["characters"])


def resolve(present, persona, others):
    """Return (present_cast labels, image files, missing names, layout)."""
    cast, images, missing = [], [], []
    if present and persona:
        label, img = PERSONA[persona]
        cast.append(label)
        images.append(img)
    for name in others:
        cast.append(name)
        if name in AVAIL:
            images.append(AVAIL[name])
        else:
            missing.append(name)
    if not images:                       # nobody with a portrait -> hold previous frame
        return cast, ["(hold previous frame)"], missing, "hold-previous"
    n = len(images)
    layout = "single" if n == 1 else (f"row({n})" if n <= 4 else f"grid({n})")
    return cast, images, missing, layout


def build(chapters, offset0=0.0):
    rows, offset, index = [], offset0, {}
    for ch in chapters:
        specs = SCENES[ch]
        counts = [max(1, body_chars(ch, s[0], s[1])) for s in specs]
        total = sum(counts)
        for (ls, le, present, persona, others, anchor), cc in zip(specs, counts):
            cast, images, missing, layout = resolve(present, persona, others)
            dur = DUR[ch] * cc / total
            rows.append({"chapter": ch, "start": hms(offset), "duration": hms(dur),
                         "present_cast": cast, "images": images, "missing_images": missing,
                         "layout": layout, "text_anchor": anchor})
            for label in cast:
                if label.startswith("Klein"):
                    key, status = "Klein Moretti (protagonist)", "have"
                elif label in AVAIL:
                    key, status = label, "have"
                elif label.startswith("["):
                    key, status = label, "background"      # unnamed extra
                elif label in REGISTRY:
                    key, status = label, "need"            # important: has a wiki page, no portrait
                else:
                    key, status = label, "minor"           # named but no wiki page
                e = index.setdefault(key, {"status": status, "scenes": 0})
                e["scenes"] += 1
            offset += dur
    return rows, offset, index


def write_md(path, title, note, rows, total, index):
    L = [f"# {title}", "", note, "",
         f"**Total covered:** {hms(total)}  ·  **scenes:** {len(rows)}", "",
         "| Start | Dur | Ch | Present cast | Image(s) | Missing image |",
         "|---|---|---|---|---|---|"]
    for r in rows:
        miss = ", ".join(r["missing_images"]) or "—"
        L.append(f"| {r['start']} | {r['duration']} | {r['chapter']} | "
                 f"{', '.join(r['present_cast'])} | {', '.join(r['images'])} | {miss} |")
    STATUS = {"have": "✅ have", "need": "❌ get image (wiki char)",
              "minor": "➖ minor (no wiki page)", "background": "· unnamed extra"}
    L += ["", "## Character index (this batch)", "",
          "| Character | Status | Scenes |", "|---|---|---|"]
    for name in sorted(index, key=lambda n: (-index[n]["scenes"], n)):
        L.append(f"| {name} | {STATUS[index[name]['status']]} | {index[name]['scenes']} |")
    need = sorted(n for n in index if index[n]["status"] == "need")
    minor = sorted(n for n in index if index[n]["status"] == "minor")
    bg = sum(1 for n in index if index[n]["status"] == "background")
    L += ["",
          f"**🎯 Get an image — important characters with a wiki page ({len(need)}):** "
          + (", ".join(need) or "none"),
          f"**Minor named (no wiki page, optional) ({len(minor)}):** " + (", ".join(minor) or "none"),
          f"**Unnamed background figures:** {bg} (not expected to have portraits)"]
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


rows1, end1, idx1 = build([1, 2, 3, 4, 5, 6, 7])
write_md(OUT / "block_01_ch001-050_SAMPLE.md",
         "Scene Timeline — SAMPLE (Block 1, chapters 1-7 of 1-50)",
         "_Content pass, full-cast tracking. Durations are char-share ESTIMATES (placeholder until forced "
         "alignment). ch6 is an untagged placeholder; ch8-50 omitted._",
         rows1, end1, idx1)
(OUT / "block_01_ch001-050_SAMPLE.json").write_text(
    json.dumps({"batch": 1, "chapters_sampled": "1-7", "scenes": rows1,
                "characters_index": idx1}, indent=2, ensure_ascii=False), encoding="utf-8")

rows2, end2, idx2 = build([215])
write_md(OUT / "ch215_sherlock_SAMPLE.md",
         "Scene Timeline — SAMPLE (chapter 215, 'Mrs. Sammer' — Sherlock persona)",
         "_Standalone illustration. Offsets are chapter-relative._", rows2, end2, idx2)

print(f"Block 1 sample: {len(rows1)} scenes, {hms(end1)}; "
      f"{sum(1 for e in idx1.values() if e['status']=='need')} wiki chars need images")
print(f"Ch215 sample: {len(rows2)} scenes, {hms(end2)}; "
      f"{sum(1 for e in idx2.values() if e['status']=='need')} wiki chars need images")
