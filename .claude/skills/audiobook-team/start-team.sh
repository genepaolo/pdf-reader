#!/usr/bin/env bash
# Start the audiobook agent team in Herdr: one tab per agent (roster: team.tsv). Skips agents already running.
# From ab-chief's pane in Git Bash:  bash .claude/skills/audiobook-team/start-team.sh [--brief]
set -euo pipefail
export MSYS_NO_PATHCONV=1
[ "${HERDR_ENV:-}" = 1 ] || { echo "not inside a Herdr pane"; exit 1; }
ROOT="C:\\Users\\paolo\\Work\\Projects\\LOTM\\pdf-reader"
DIR="$(cd "$(dirname "$0")" && pwd)"
WS="${HERDR_WORKSPACE_ID:?}"
herdr agent rename "${HERDR_PANE_ID:?}" ab-chief >/dev/null 2>&1 || true

running=$(herdr agent list | py -3.12 -c "import json,sys;print(' '.join(a.get('name') or '' for a in json.load(sys.stdin)['result']['agents']))")
while IFS=$'\t' read -r name kind label args; do
  [ -z "$name" ] || [ "${name:0:1}" = "#" ] && continue
  if [[ " $running " == *" $name "* ]]; then echo "$name: already running"; continue; fi
  pane=$(herdr tab create --workspace "$WS" --cwd "$ROOT" --label "$label" --no-focus \
    | py -3.12 -c "import json,sys;print(json.load(sys.stdin)['result']['root_pane']['pane_id'])")
  eval "extra=($args)"
  out=$(herdr agent start "$name" --kind "$kind" --pane "$pane" --timeout 90000 ${extra[@]+-- "${extra[@]}"} 2>&1 || true)
  echo "$name ($kind) -> $pane $(echo "$out" | grep -oE '"agent_status":"[a-z]+"|"code":"[a-z_]+"' | head -1)"
  if [ "${1:-}" = "--brief" ]; then
    herdr agent prompt "$name" "You are $name. Read .claude/skills/audiobook-team/SKILL.md (Codex: also ../AGENTS.md), then wait for a task. Reply with one line: HANDOFF -> ab-chief | DONE | -" >/dev/null 2>&1 \
      && echo "  $name: briefed" || echo "  $name: brief not sent (check 'herdr agent get $name')"
  fi
done < <(tr -d '\r' < "$DIR/team.tsv")
herdr agent list | py -3.12 -c "import json,sys;[print(' ',a.get('name'),a['agent'],a['pane_id'],a['agent_status']) for a in json.load(sys.stdin)['result']['agents'] if (a.get('name') or '').startswith('ab-')]"
