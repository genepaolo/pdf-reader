# Plan — Replace Azure TTS with a local engine (VoiceStudio)

> Canonical in-repo copy of the plan. Original drafted on the Mac
> (`~/.claude/plans/sharded-whistling-raven.md`, 2026-10-02) and committed
> here so the Windows session picks it up on the next `git pull`.

## Context

The current pipeline pays Azure Neural TTS to synthesize **every chapter** of
`lom_book2_coi` (~1180 chapters total; 603 audio done, 128 uploaded chapters
remaining in the current batch, hundreds more to come). The active voice is
`en-US-SteffanNeural` (male, en-US, rate +0%, pitch +0Hz, output
`audio-24khz-160kbitrate-mono-mp3`, max 20 000 chars/chapter) — see
`tts_pipeline/config/projects/lom_book2_coi/azure_config.json`.

Goal: replace Azure with a **locally-hosted** engine driven by
[VoiceStudio](https://github.com/debpalash/VoiceStudio) (51.9k★, AGPL-3.0, an
open-source ElevenLabs alternative with a local HTTP API + voice cloning in
646 languages). This is a personal project, so AGPL is fine as long as we
**consume VoiceStudio over its local API** rather than vendoring its code.

The outcome we're after:

1. A **voice** rendered by VoiceStudio that is close enough to Steffan that
   switching mid-series does not jar listeners.
2. A **`LocalTTSClient`** that `process_project.py` can select instead of
   `AzureTTSClient`, with the same input (text file in `formatted_text/`),
   the same output (`D:/PDFReader/<project>_output/Volume_N_Name/*.mp3`), and
   the same **deterministic sentence-end silences** that
   `character_scene_video/align_chapter.py` depends on.

### Two hard constraints discovered during research

- **Alignment is Azure-coupled.** `character_scene_video/align_chapter.py`
  explicitly assumes "the synthesiser emits a clear pause at every sentence
  end, so the sentence sequence in the text and the silence sequence in the
  audio are the same sequence" (`detect_silences()` via ffmpeg
  `silencedetect`). A local engine that varies pause length between runs or
  swallows sentence breaks will break alignment for any audio it renders.
  *(Checked 2026-10-02: all Book-1 audio — Vol 1–8, incl. Vol 3's 250 MP3s —
  already exists from Azure, so the current per-scene work is safe. The risk
  is any FUTURE re-render of Book-1 chapters, or per-scene videos for COI.)*
  This still has to be validated BEFORE we commit a voice.
- **AMD GPU on Windows.** The target host is the main PC with an RX 9070 XT.
  Most Python TTS stacks (incl. OmniVoice, VoiceStudio's default engine) are
  PyTorch; PyTorch on AMD Windows means ROCm (unofficial) or DirectML
  (slower) or CPU. CPU on hundreds of chapters is a non-starter. **A
  single-chapter benchmark on the real GPU is step 1** — if it is e.g. 20×
  realtime slower than Azure, the plan changes.

### Where it lives

**Inside `pdf-reader/`**, two new areas:

```
pdf-reader/
├── local_tts/                        <-- NEW: experimentation + adapter
│   ├── README.md
│   ├── audition/
│   │   ├── samples/                  short reference-text .txt files
│   │   ├── reference_audio/          Azure-rendered gold-standard mp3s
│   │   ├── voice_candidates/         one subdir per candidate voice
│   │   ├── render.py                 call VoiceStudio API, write mp3
│   │   ├── compare.py                silence-detect + A/B spectrogram vs gold
│   │   └── benchmark.py              throughput + VRAM + realtime factor
│   ├── voicestudio_client.py         thin HTTP wrapper around VoiceStudio's local API
│   └── config.example.json           host/port/voice settings template
├── tts_pipeline/
│   ├── api/
│   │   ├── tts_engine.py             NEW: abstract interface
│   │   ├── azure_tts_client.py       (unchanged, implements TTSEngine)
│   │   ├── azure_tts_factory.py      renamed → tts_factory.py; switches on config
│   │   └── local_tts_client.py       NEW: wraps local_tts.voicestudio_client
│   └── config/projects/<proj>/
│       ├── processing_config.json    add `"tts_engine": "azure"` default
│       └── local_tts_config.json     NEW (sibling to azure_config.json)
```

**VoiceStudio itself is installed OUTSIDE the repo**, via its one-line
installer, probably at `C:\Program Files\VoiceStudio\` or `D:\VoiceStudio\`.
We never fork or vendor its source. We talk to it over `http://localhost:<port>`
(the exact API shape is read from VoiceStudio's `docs/speech-platform.md` in
Phase 1a).

## Phase 0 — do this before you plan voices (on the Windows PC)

> This is a go/no-go gate. ~1 hour of work.

1. Open a fresh Claude Code session in the repo on Windows and `@`-reference
   this file (`@VOICESTUDIO_TTS_SWAP_PLAN.md`) in the first message.
2. Install VoiceStudio with its official installer. Confirm it launches, the
   local API responds (`curl http://localhost:<port>/health` or the equivalent
   from its docs), and that OmniVoice downloads on first run.
3. Confirm GPU acceleration. Open Task Manager → Performance → GPU and
   render ONE 500-word sample while watching GPU utilization. If the GPU is
   idle and the CPU is pegged → investigate DirectML / ROCm / fallback. Record
   seconds-per-1000-chars.
4. **Decision**: if realtime factor is worse than ~3× (i.e. 10 min of audio
   takes >30 min to render), stop and reconsider — options include a lighter
   engine (Piper, Kokoro), a cloud GPU rental, or sticking with Azure for the
   current series and using local only for shorts. If RTF ≤ 1×, continue.

## Phase 1 — voice audition (standalone, no pipeline changes)

Run from `pdf-reader/local_tts/audition/`.

1. Pick 5 reference passages from `formatted_text/lom_book2_coi/` that are
   known-hard: dialogue, long inner monologue, names like "Hanass Vincent",
   and one page from the Antigonus diary. ~500 words each.
2. Render each with the current Azure Steffan voice (the real MP3s already
   exist on `D:/PDFReader/lom_book2_coi_output/`) → copy into
   `reference_audio/` as the gold standard.
3. **Start with voice cloning — primary candidate** (user call 2026-10-02).
   We have hundreds of hours of clean Steffan audio sitting on `D:/PDFReader/`
   from both lotm_book1 and lom_book2_coi. Feeding that to VoiceStudio's
   clone feature is the whole reason to pick VoiceStudio over a preset-only
   engine like Piper or Kokoro, and a successful clone makes the mid-series
   voice swap invisible to listeners — the one thing a preset voice can't do
   at ch604. Try this before any preset.

   - **Reference clip extraction** (do on the Windows PC, no re-encode):
     ```
     ffmpeg -ss 00:00:30 -t 00:00:30 \
       -i D:/PDFReader/lom_book2_coi_output/Volume_1_Nightmare/Chapter_1_*.mp3 \
       -ar 24000 -ac 1 reference_audio/steffan_30s.wav
     ```
     Pick **pure narration** passages — no quoted dialogue. Azure's prosody
     shifts around quote marks, and we want the narrator voice, not a blend.
     Try 2-3 reference clips of different length (e.g. 20 s, 45 s) sourced
     from different chapters — clone quality is sensitive to seed content.
   - **Known risk — "clone of a synthetic voice":** cloners are normally
     trained on human speech. Cloning TTS output may compound subtle
     artifacts (metallic sheen, flattened prosody). If the clone sounds
     worse than a preset voice, abandon the clone and ship a preset
     Steffan-adjacent voice — a one-time mid-series voice change beats
     hundreds of hours of subtly-degraded audio.
   - **Alignment is NOT solved by cloning.** A clone inherits OmniVoice's
     silence behavior, not Azure's. The silence-detect hard gate in step 5
     still applies — a clone that sounds perfect but swallows sentence
     pauses is still rejected.
   - **Legal note:** Azure's ToS language about "no training competing
     commercial models" is aimed at distributing a model, not at publishing
     the audio you render with it. Keep the clone + reference WAV on your
     local machine; publish only the rendered MP3s (which is what we do
     anyway). The weights never leave the Windows PC.
   - **Optional post-clone modification** (user call 2026-10-02) — once you
     have a clone you like, consider a mild pitch shift (e.g. -1 semitone)
     or formant tweak in VoiceStudio. The reason is **identifiability**,
     not ToS cover. A 1:1 Steffan clone is recognizable to any listener who
     has heard Azure's Steffan on another audiobook channel; a modified
     version becomes "your custom narrator, Steffan-adjacent" and is a
     nicer long-term artistic position. Modification does NOT launder
     training provenance — but we don't need that laundering, we need
     distinctiveness.
   - **Fallbacks** if the clone fails the alignment gate or sounds off:
     1-2 preset male en-US voices VoiceStudio ships with (OmniVoice has its
     own catalog), plus 1 other male narrator-character voice.
4. For each candidate: run `render.py` to produce mp3s into
   `voice_candidates/<voice_id>/`.
5. Run `compare.py`:
   - **Silence-detect check (hard gate):** run
     `character_scene_video/align_chapter.py` logic on each candidate's mp3
     against the same source text, verify every sentence boundary resolves.
     Fail = this voice cannot be used, no matter how good it sounds.
   - Loudness match (ffmpeg `loudnorm`), realtime factor, size on disk.
6. Blind A/B listening — write 2-sentence notes per voice in
   `audition/NOTES.md`.
7. Pick ONE voice. Record its VoiceStudio ID, any clone artifacts, and the
   generation settings in `local_tts_config.json` template.

## Phase 2 — pipeline integration (ships the swap)

Only start this once Phase 1 produces an alignment-safe voice you're happy
with.

### 2a. Introduce an engine interface in `tts_pipeline/`

Minimal interface in `tts_pipeline/api/tts_engine.py`:

```python
class TTSEngine(Protocol):
    def process_chapters_batch(self, chapters: list[dict]) -> dict: ...
```

- Make `AzureTTSClient` (`tts_pipeline/api/azure_tts_client.py:217-636`) a
  concrete `TTSEngine`. No behavior changes.
- Rename `azure_tts_factory.py` → `tts_factory.py`. Add selection:
  ```python
  engine = project.processing_config.get("tts_engine", "azure")
  if engine == "azure":   return AzureTTSClient(project)
  if engine == "local":   return LocalTTSClient(project)
  ```
- `process_project.py` already calls through the factory, so no CLI
  changes are needed. (Optional: add a `--engine azure|local` override.)

### 2b. Implement `LocalTTSClient`

File: `tts_pipeline/api/local_tts_client.py`.

- Imports `local_tts.voicestudio_client` (the HTTP wrapper from Phase 1).
- Mirrors `AzureTTSClient.process_chapters_batch(chapters)` method signature
  and return dict (`total_chapters`, `successful_chapters`,
  `failed_chapters`, `processing_time`, `batches_processed`,
  `average_time_per_chapter`) so downstream code doesn't notice.
- Reads voice settings from `tts_pipeline/config/projects/<p>/local_tts_config.json`
  (NOT from `azure_config.json`).
- Reuses `_load_chapter_text`, `apply_pronunciation_substitutions`, and the
  volume-aware output-path logic from `azure_tts_client.py` — refactor those
  into a `tts_pipeline/api/_common.py` helper so both engines share them. Do
  NOT duplicate code.
- For now, process chapters **sequentially** (one HTTP call to VoiceStudio
  per chapter). Parallelism inside VoiceStudio is its problem; concurrent
  HTTP requests from us would just thrash the GPU.
- Writes directly to `D:/PDFReader/<project>_output/Volume_<name>/*.mp3` —
  same path convention as Azure.

### 2c. Config

`tts_pipeline/config/projects/lom_book2_coi/local_tts_config.json`:

```json
{
  "endpoint": "http://localhost:<port>",
  "voice_id": "<chosen in Phase 1>",
  "clone_reference_wav": "local_tts/audition/reference_audio/steffan_30s.wav",
  "output_format": "mp3",
  "sample_rate": 24000,
  "bitrate_kbps": 160,
  "max_text_length": 20000,
  "timeout_seconds": 1200
}
```

Add `"tts_engine": "local"` to `processing_config.json` **only after** a
successful smoke test — leave `azure` as default until then.

### 2d. Smoke test on real data

1. `py -3.12 tts_pipeline/scripts/process_project.py --project lom_book2_coi --dry-run --max-chapters 1`
2. If dry-run passes, render ONE real chapter (`--chapters 604` since 603 is
   the current highest) with `tts_engine: local`.
3. Compare output file size, duration, loudness to the Azure Steffan
   recording of a known-matching chapter.
4. Run `character_scene_video/verify_alignment.py 604 604` if alignment is
   needed for this project (it's a Book 1 tool; for Book 2 the alignment
   dependency only matters if we start doing per-scene videos there).

## Critical files to touch / create

**New:**
- `local_tts/` whole subtree (see directory layout above)
- `tts_pipeline/api/tts_engine.py`
- `tts_pipeline/api/local_tts_client.py`
- `tts_pipeline/api/_common.py` (shared helpers)
- `tts_pipeline/config/projects/lom_book2_coi/local_tts_config.json`

**Modify (minimally):**
- `tts_pipeline/api/azure_tts_factory.py` → rename `tts_factory.py`, add
  engine selection
- `tts_pipeline/api/azure_tts_client.py` → move `_load_chapter_text` and
  volume-path helpers into `_common.py`; import them back. No behavior
  change for Azure.
- `tts_pipeline/scripts/process_project.py` → one-line change to use
  `TTSFactory` instead of `AzureTTSFactory`; optional `--engine` flag
- `tts_pipeline/config/projects/lom_book2_coi/processing_config.json` → add
  `"tts_engine": "local"` (deferred to the end of Phase 2d)

**Reuse unchanged:**
- `tts_pipeline/utils/project_manager.py` (`ProjectManager`, `Project`)
- `tts_pipeline/utils/file_organizer.py` (`ChapterFileOrganizer`)
- `tts_pipeline/utils/chapter_title.py`
- `tts_pipeline/api/video_processor.py`
- `tts_pipeline/scripts/create_videos.py`
- `upload_queue.py`

## Verification

- **Phase 0**: single sample renders on GPU in ≤3× realtime.
- **Phase 1**: at least one voice passes `align_chapter.py` silence detection
  on all 5 sample passages, and a blind A/B says it's close to Steffan.
- **Phase 2a-c**: `py -3.12 -m pytest tts_pipeline/tests/ -q` still passes
  all 66 tests (the Azure path must be untouched).
- **Phase 2d**: `py -3.12 tts_pipeline/scripts/process_project.py --project
  lom_book2_coi --dry-run --max-chapters 1` succeeds with `tts_engine: local`.
- **Final**: render ch604 locally; `ffprobe` reports 24 kHz mono MP3; file
  lands in `D:/PDFReader/lom_book2_coi_output/Volume_8_<name>/Chapter_604_*.mp3`;
  size/duration within 10% of a comparable Steffan chapter.

## What to do IN THE NEW SESSION on Windows

1. `git pull` on the Windows copy of this repo so this file is present.
2. Open Claude Code in that repo directory and `@`-reference this file
   (`@VOICESTUDIO_TTS_SWAP_PLAN.md`) in the first message.
3. Start at Phase 0, step 1. Do NOT skip the GPU benchmark — it's the
   cheapest way to find out this whole plan is wrong before you've written
   any code.
4. When Phase 1 begins, go to the voice-clone branch FIRST (step 3), not the
   preset survey — presets are the fallback, not the opener.

## Explicit non-goals

- Don't touch `character_scene_video/` code in this effort. If alignment
  breaks on a candidate voice, reject the voice; don't rewrite the aligner.
- Don't retire `AzureTTSClient` yet. Keep both engines so a bad local output
  can fall back to Azure for one chapter without re-plumbing.
- Don't try to speed Azure up or batch-optimize anything on the Azure side —
  this plan is purely additive until Phase 2d flips the default.
- Don't fork VoiceStudio. If a VoiceStudio bug blocks us, file an upstream
  issue; patching their 130 MB Electron+Python monorepo is a bigger project
  than this whole plan.
- Don't commit cloned model weights, voice-clone fingerprints, or the
  Azure-source reference WAV to this repo. The clone lives on the Windows
  PC's local VoiceStudio install; the audio it renders is what ships to
  YouTube. Keeping the weights and reference audio off GitHub keeps the
  "we only publish rendered audio, not the model" line true, which is the
  thing that actually matters for the Azure-ToS corner case. Add the
  relevant `local_tts/audition/reference_audio/` and model-cache paths to
  `.gitignore` as part of Phase 1 when the directory is first created.
