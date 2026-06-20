#!/usr/bin/env bash
# record_cli_demo.sh — Record FinRoot CLI demo (asciinema preferred, txt fallback)
# Writes: docs/demo/cli_demo.cast|.svg|.gif or docs/demo/cli_demo.txt
# Depends on: wave-7 (CLI)

set -euo pipefail

# Configuration
OUT_DIR="docs/demo"
CAST_FILE="${OUT_DIR}/cli_demo.cast"
SVG_FILE="${OUT_DIR}/cli_demo.svg"
GIF_FILE="${OUT_DIR}/cli_demo.gif"
TXT_FILE="${OUT_DIR}/cli_demo.txt"

# Demo queries (matching the task spec)
QUERIES=(
    "Review my portfolio and flag risks"
    "Calculate tax on ₹2,00,000 LTCG from equity"
    "Should I put my entire emergency fund into a hot small-cap stock?"
)

# Environment for mock mode
export PYTHONPATH=src
export FINROOT_LLM_PROVIDER=mock

# Ensure output directory exists
mkdir -p "${OUT_DIR}"

# Check for asciinema
if command -v asciinema >/dev/null 2>&1; then
    echo "asciinema found — recording cast..."
    
    # Record with asciinema
    asciinema rec "${CAST_FILE}" --overwrite --command="
        for q in '${QUERIES[0]}' '${QUERIES[1]}' '${QUERIES[2]}'; do
            echo \"\$ python -m interface.cli --mock \\\"\\\$q\\\"\"
            python3 -m interface.cli --mock \"\$q\"
            echo
            sleep 1
        done
    "
    
    # Try to render SVG/GIF if tools available
    if command -v agg >/dev/null 2>&1; then
        echo "agg found — rendering SVG..."
        agg "${CAST_FILE}" "${SVG_FILE}"
    elif command -v svg-term >/dev/null 2>&1; then
        echo "svg-term found — rendering SVG..."
        cat "${CAST_FILE}" | svg-term --out "${SVG_FILE}" --window
    fi
    
    if command -v agg >/dev/null 2>&1 && command -v convert >/dev/null 2>&1; then
        echo "agg + ImageMagick found — rendering GIF..."
        agg "${CAST_FILE}" "${GIF_FILE}" --format gif
    fi
    
    echo "Recording complete. Output: ${CAST_FILE}"
    if [[ -f "${SVG_FILE}" ]]; then echo "SVG: ${SVG_FILE}"; fi
    if [[ -f "${GIF_FILE}" ]]; then echo "GIF: ${GIF_FILE}"; fi
    
else
    echo "asciinema NOT found — falling back to plain text transcript."
    echo "Install asciinema for animated casts: pip install asciinema"
    echo
    
    # Capture plain text transcript
    {
        echo "=== FinRoot CLI Demo Transcript (Mock Mode) ==="
        echo "Generated: $(date)"
        echo "Environment: PYTHONPATH=src FINROOT_LLM_PROVIDER=mock"
        echo
        
        for q in "${QUERIES[@]}"; do
            echo "======================================================================"
            echo "COMMAND: python -m interface.cli --mock \"${q}\""
            echo "======================================================================"
            echo
            python3 -m interface.cli --mock "${q}" 2>&1 | grep -v "^/" | grep -v "LangChain" | grep -v "Pydantic" | grep -v "LangGraph" || true
            echo
            echo
        done
    } > "${TXT_FILE}"
    
    echo "Transcript written to: ${TXT_FILE}"
fi