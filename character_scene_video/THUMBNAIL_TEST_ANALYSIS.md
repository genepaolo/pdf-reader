# Thumbnail test analysis — Volume 1 tests read on 2026-09-06, applied to Volume 2

Source: YouTube Studio (Reach tab, per-day values read off the chart for Aug 27 – Sep 5) for the
four Volume 1 parts. All four have a Test & Compare running; **none had per-variant data yet**
("Not enough information to display data") — P1 had 6 days left, P2–P4 about 10. What CAN be
read is the aggregate CTR of each part before and after its test started, which is enough to
rank the concepts and to fix Volume 2 before it goes up.

## 1. What is actually running

| Part | Video | Test started | Slot 1 (shown as current) | Slot 2 | Slot 3 |
|---|---|---|---|---|---|
| 1 | `sQ94crQVoAQ` | ~Aug 29 | old series template | varB faces (Audrey + Klein) | varA row (3 cards) |
| 2 | `AfBLteZ9nfU` | ~Sep 2/3 | varA bigface (warm donghua Klein) | varB faces | varC row |
| 3 | `Qi3hZkRr_j0` | ~Sep 2/3 | varA bigface (dark top-hat Klein) | varB faces | varC row |
| 4 | `8lha69vkmCE` | ~Sep 2/3 | varA bigface (dark red Klein) | varB faces | varC row |

(The plan had said hold P2–P4 as controls; the user started them ~Sep 2/3. The 4-day control
window Aug 30 – Sep 2 still exists and is used below.)

## 2. Daily numbers (impressions / CTR / views)

```
PART 1    Aug 27   Aug 28   Aug 29   Aug 30   Aug 31    Sep 1    Sep 2    Sep 3    Sep 4    Sep 5
  impr          0     1298      238      331      376       91      112       97       71       62
  ctr %       0.0      1.5      2.9      2.4      3.5      7.7      4.5      4.1      0.0      1.6
PART 2
  impr          0      775      103      132      104       63       96       83       74       68
  ctr %       0.0      1.3      1.0      0.0      3.9      1.6      1.0      3.6      5.4      7.4
PART 3
  impr          0      179       39       78       65       54       94       67       53       60
  ctr %       0.0      1.1      0.0      0.0      1.5      0.0      0.0      0.0      0.0      0.0
PART 4
  impr          0     1608      109      177      249       28       48       37       30       28
  ctr %       0.0      0.9      0.0      2.3      1.6      3.6      2.1      2.7      3.3      3.6
```

Impression-weighted CTR by window:

| Part | Launch Aug 27–29 | Control Aug 30–Sep 2 | Test Sep 3–5 |
|---|---|---|---|
| 1 (test since Aug 29) | 1.7% (1,536 impr) | **3.6%** (910) | 2.2% (230) |
| 2 (test since Sep 2/3) | 1.3% (878) | 1.5% (395) | **5.3%** (225) |
| 3 (test since Sep 2/3) | 0.9% (218) | 0.3% (291) | **0.0%** (180) |
| 4 (test since Sep 2/3) | 0.8% (1,717) | 2.0% (502) | 3.2% (95) |

## 3. What it says

1. **Ignore launch-day CTR.** Every part's launch spike is 1,000+ impressions at 0.8–1.7% — mass
   Browse exposure to people who were never going to click. Post-launch impressions are fewer and
   better targeted, and CTR settles 2–3× higher. Compare windows, never cumulative totals.

2. **The new concepts beat the series template by roughly 2×.** In the same control window, P1
   (rotating template / faces / row) ran 3.6% while P2/P3/P4 on the untouched template ran
   1.5% / 0.3% / 2.0%. Same line-1 description on all four, so the thumbnail is the variable.

3. **P2's jump is real; brightness is the tell.** P2 went 1.5% → 5.3% the moment its test started
   (6 clicks/395 → 12/225, p ≈ 0.01). P3 went 0.3% → 0.0% (0 clicks on 180 impressions). Both are
   the same "bigface" concept with the same text block. The difference is the art:

   | Bigface thumbnail | Face-panel brightness (0–255) | Post-test CTR |
   |---|---|---|
   | Vol 1 P2 — warm, lit donghua Klein | **121** | **5.3%** |
   | Vol 1 P4 — dark red Klein | 43 | 3.2% (3/95, weak) |
   | Vol 1 P3 — dark top-hat Klein | **49** | **0.0%** |

   A lit, warm face at feed size gets clicks; a dark, low-contrast one gets none. That's the
   standard thumbnail rule showing up in our own data.

4. **P1's Sep 3–5 dip (3.6% → 2.2%) is small-n** (5 clicks/230) and coincides with P2–P4's new
   thumbnails competing in the same Browse shelves. Not evidence against the P1 variants.

5. **The channel is impression-starved (~60–100/day/part), so YouTube's tests will probably end
   "no clear winner".** ⚠ When a Test & Compare ends without a winner, Studio keeps the pre-test
   thumbnail — for P1 that is the OLD template. When each test ends, pick the winner manually
   (P1: whichever of faces/row Studio shows ahead, else varB faces; P2–P4: keep varA bigface).

6. Traffic mix: Browse 50–92%, Playlists 18–30% on P1/P2 (the Vol-1 playlist autoplay chain is
   working — P2's playlist share is P1 viewers continuing), Search 5–33%, Suggested 5–19%.

## 4. Applied to the Volume 2 thumbnails (built 2026-09-02)

Face-panel brightness of each part's varA bigface, same measurement:

| Vol 2 part | Art | Face brightness | Verdict |
|---|---|---|---|
| 1 | S2 concept-poster Sherlock | 165 | ✅ keep as default |
| 2 | Sherlock Moriarty card | 90 | ⚠ mid-dark → **varD built (133)** |
| 3 | S2 poster Sherlock (bright) | 161 | ✅ keep |
| 4 | Hero Bandit (black armour) | **48** | ❌ same range as the 0%-CTR Vol-1 P3 → **varD built (96)** — the art is a silhouette by design, so the lift comes from a hot ember/blue backdrop rather than the figure; if it also tests poorly, swap P4 to the bright S2-poster Sherlock (he is still that part's lead) |
| 5 | Amon card | 64 | ❌ dark → **varD built (101)** |

`varD_bright` = same crop and text as varA, art panel auto-contrasted and lifted, tighter face
crop, stronger warm glow behind the panel. Files sit next to A/B/C in each part's `thumbnails/`
folder (`parts/Part_K_chAAA-BBB/thumbnails/thumb_vol02_pK_varD_bright.jpg`).

**Recommendation for the Vol 2 upload:**
- P1 and P3: upload with varA (already bright); Test & Compare against varB + varC.
- P2, P4, P5: upload with **varD_bright** as the default; Test & Compare against varA + varB
  (so the test directly measures the brightness lift on the same concept).
- Do not touch titles while thumbnail tests run — one variable at a time.

## 5. Title / description / pinned-comment adjustments (Volume 2) — APPLIED 2026-09-06

- **Description line 1** — `make_upload_pack.py` still emitted the original "The hit web novel as a
  continuous audiobook" line; the live Vol-1 parts have used the rewritten line since 08-29
  ("…full audiobook with the cast on screen — character portraits change with every scene. Volume
  N: Name, Part K of N, Ch A–B, H hours[ — the volume finale]."). The generator now writes that
  line, so every Vol-2 pack carries the exact search phrase + USP in the snippet.
- **Bridge line** — the series line ("Volume 1 covers far more than Season 1 adapts") is Vol-1
  specific. Vol 2 now overrides it: *"Season 2 (announced for 2027) adapts THIS volume — Klein's
  Backlund years as the detective Sherlock Moriarty. Hear the whole arc before it airs."*
  (`upload_meta.json` → `volumes.2.bridge_line`; any volume may override.)
- **Pinned comment** — Vol 2's pinned comment now adds, under the part links: *"New here? Start at
  the beginning — Volume 1: The Clown (all 4 parts, autoplays in order): …watch?v=sQ94crQVoAQ&list=PLQD_MWrZYC-I"*
  (`volumes.2.pinned_extra_lines`). The `[link]` placeholders for Parts 2–5 still get filled after
  all five are up, as before.
- **Titles** — unchanged (89/100 chars, search phrase front-loaded). Revisit "Visual Audiobook"
  only after the thumbnail tests conclude.
- **Tags** — unchanged (380/500).
- **Still manual, after Vol 2 is live:** append a "Continue with Volume 2 →" line to the four live
  Vol-1 pinned comments, and give Vol-1 P4 its missing end screen pointing at Vol-2 P1.
