#!/usr/bin/env bash
# dispatch_worker.sh — hand ONE task file to ONE CLI agent (headless) and capture its run log.
# The orchestrator (Claude) calls this; the agent (OpenCode/Grok) does the implementation.
#
# Usage:
#   dispatch_worker.sh <engine> <model> <wave> <task-file>
#     engine     : opencode | grok
#     model      : provider/model (opencode)  OR  grok-build|grok-composer-2.5-fast (grok)
#     wave       : e.g. wave-1
#     task-file  : path under work/<wave>/  e.g. work/wave-1/02-pydantic-schemas-state.md
#
# Writes a run log to work/reports/<wave>/<NN>-<slug>.run.log and (the agent) the report .md.
set -uo pipefail
cd "$(dirname "$0")/../.."
ROOT="$(pwd)"
export PATH="$PATH:/Users/srujansai/.grok/bin"

ENGINE="${1:?engine}"; MODEL="${2:?model}"; WAVE="${3:?wave}"; TASKFILE="${4:?task-file}"
[ -f "$TASKFILE" ] || { echo "task file not found: $TASKFILE" >&2; exit 1; }
BASE="$(basename "$TASKFILE" .md)"
LOG="work/reports/${WAVE}/${BASE}.run.log"
mkdir -p "work/reports/${WAVE}"

read -r -d '' DIRECTIVE <<EOF
You are a FinRoot Tier-2 worker agent. Working dir: ${ROOT}.

1. Read work/WORKER_PROMPT.md (your rules) and ${TASKFILE} (your task) and any contract it references
   under .specify/specs/${WAVE}/contracts/.
2. Implement ONLY the files in the task's "Writes" set. Touch nothing else (FM-13).
3. Numbers from tools+cited, fail loud, no fabricated data, type everything (Pydantic v2), ruff-clean, add tests.
4. Run the task's Acceptance commands and capture their REAL output.
5. Write your report to work/reports/${WAVE}/${BASE}.report.md using work/REPORT_TEMPLATE.md, including
   the acceptance command output. If you hit a surprise, append it to docs/waves/${WAVE}-gotchas.md.
Finish when acceptance passes and the report is written. Do not ask questions; make the smallest correct choice.
EOF

echo "=== dispatch ${ENGINE} ${MODEL} -> ${TASKFILE} @ $(date) ===" | tee "$LOG"

case "$ENGINE" in
  opencode)
    # NB: opencode's -f is array-typed and greedily eats the trailing positional message;
    # so we pass the directive as the sole positional and let the agent read files via --dir.
    opencode run -m "$MODEL" --dir "$ROOT" "$DIRECTIVE" >>"$LOG" 2>&1
    ;;
  grok)
    grok -p "$DIRECTIVE" --cwd "$ROOT" -m "$MODEL" --always-approve \
      --output-format plain --no-alt-screen --max-turns 80 >>"$LOG" 2>&1
    ;;
  *) echo "unknown engine: $ENGINE" >&2; exit 1 ;;
esac
RC=$?
echo "=== ${ENGINE} exited rc=$RC @ $(date) ===" | tee -a "$LOG"
exit $RC
