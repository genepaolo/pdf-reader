---
name: audiobook-team
description: Audiobook (pdf-reader) multi-agent team protocol in Herdr — roster, who owns what, hand-off line, RAM/token rules. Use when acting as ab-chief, when briefing or messaging a team agent, or when any ab-* agent finishes a step.
---

# Audiobook team (Herdr workspace "Audiobook Project - PDF Reader/TTS/Voice Studio")

Repo: `C:\Users\paolo\Work\Projects\LOTM\pdf-reader` (operational truth: `CLAUDE.md`; Codex: `AGENTS.md`).
Names carry an `ab-` prefix because Herdr names are unique server-wide (Core EMR uses `chief`, `builder`, ...).

## Roster (`team.tsv`; models are fixed, roles are not)

| Name | Model | Default role |
|---|---|---|
| `ab-chief` | Claude Opus | dispatch, plans, rulings, commits/pushes, YouTube/growth strategy |
| `ab-builder` | Claude Sonnet | code, tests, doc edits in the repo; one feature branch at a time |
| `ab-verifier` | Codex | reviews plans, diffs, docs; writes only into `.team/` |
| `ab-producer` | Claude Sonnet | (started when needed) pipeline runs, uploads, end screens, thumbnails, metadata |
| `jobs` tab | plain shell | long runs (`upload_queue.py`, renders) in the foreground: no agent, no 30-min kill |

Chief reassigns roles by prompt; a new role is a new line here, not a new agent.

## Rules

- Every artifact has one writer; findings go to the writer through chief. Verifier never edits code or repo docs.
- Never read `.env`, `client_secret.json`, `token.json`, `azure_config.json`, `.yt_studio_profile/`. Ask chief if a value's presence matters.
- No YouTube/Azure action that publishes, deletes or bills without chief's explicit go (chief asks the operator for anything new).
- After any killed upload run: check the channel's newest uploads for an untracked video before restarting.
- Commits: plain human messages, explicit paths (`git commit -- <paths>`), noreply identity. Only chief pushes.
- Facts from this session's command output, never memory. Answer every review point ACCEPT / ACCEPT-IN-PART / REJECT + reason; verifiers are not always right.

## Budget (8 GB target, Max $100 Claude, $20 Codex)

- One task per agent at a time; idle agents cost RAM, not tokens. Never run this team alongside the Core EMR team.
- Read files once, quote paths not contents, grep before reading big files (`CLAUDE.md` sections by heading).
- Substance goes in `.team/<YYYY-MM-DD>-<topic>.md` (gitignored); chat stays short.

## Hand-off (end every finished step with exactly one line)

```
HANDOFF -> ab-chief | <DONE|AGREED|REJECTED|BLOCKED> | <.team/ path or "-">
```

## Chief commands (Git Bash, `HERDR_ENV=1`)

```bash
bash .claude/skills/audiobook-team/start-team.sh [--brief]   # start missing agents from team.tsv
herdr agent prompt ab-builder "You are ab-builder. ..." --wait --timeout 600000
herdr agent read ab-verifier --source recent-unwrapped --lines 40 | grep HANDOFF
```

`blocked` = an approval dialog: read it before answering; Codex asks to append its verdict to `.team/` (approve that
exact append only). Codex update prompt: "Skip". Codex cannot always run the Python toolchain in its sandbox; it judges
from source and the builder's recorded runs.
