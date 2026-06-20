#!/usr/bin/env bash
# record_hero_cast.sh — Record README hero CLI demo (asciinema preferred, txt fallback)
# Writes: docs/demo/hero.cast|.svg|.gif or docs/demo/hero.txt
set -euo pipefail

OUT_DIR="docs/demo"
CAST_FILE="${OUT_DIR}/hero.cast"
SVG_FILE="${OUT_DIR}/hero.svg"
GIF_FILE="${OUT_DIR}/hero.gif"
TXT_FILE="${OUT_DIR}/hero.txt"

QUERIES=(
    "Review my portfolio and flag risks"
    "Calculate tax on ₹2,00,000 LTCG from equity"
    "Should I put my entire emergency fund into a hot small-cap stock?"
)

export PYTHONPATH=src
export FINROOT_LLM_PROVIDER=mock

mkdir -p "${OUT_DIR}"

recorded=0

if command -v asciinema >/dev/null 2>&1; then
    echo "asciinema found — recording cast..."

    asciinema rec "${CAST_FILE}" --overwrite --command="
        echo 'Query 1: Portfolio review'
        python3 -m interface.cli --mock ${QUERIES[0]@Q}
        echo ''
        echo 'Query 2: Tax calculation'
        python3 -m interface.cli --mock ${QUERIES[1]@Q}
        echo ''
        echo 'Query 3: Prudence refusal'
        python3 -m interface.cli --mock ${QUERIES[2]@Q}
    "

    if [[ -f "${CAST_FILE}" ]] && [[ -s "${CAST_FILE}" ]]; then
        recorded=1
        echo "Cast written to ${CAST_FILE}"

        if command -v agg >/dev/null 2>&1; then
            echo "agg found — rendering SVG..."
            agg "${CAST_FILE}" "${SVG_FILE}" 2>/dev/null || true
        elif command -v svg-term >/dev/null 2>&1; then
            echo "svg-term found — rendering SVG..."
            cat "${CAST_FILE}" | svg-term --out "${SVG_FILE}" --window 2>/dev/null || true
        fi

        if command -v agg >/dev/null 2>&1 && command -v convert >/dev/null 2>&1; then
            echo "agg + ImageMagick found — rendering GIF..."
            agg "${CAST_FILE}" "${GIF_FILE}" --format gif 2>/dev/null || true
        fi

        if [[ -f "${SVG_FILE}" ]]; then echo "  SVG: ${SVG_FILE}"; fi
        if [[ -f "${GIF_FILE}" ]]; then echo "  GIF: ${GIF_FILE}"; fi
    fi
fi

if [[ "${recorded}" -eq 0 ]]; then
    echo "asciinema NOT found — falling back to plain text transcript."
    echo "Install asciinema for animated casts: pip install asciinema"
    echo

    {
        echo "=== FinRoot README Hero Demo (Mock Mode) ==="
        echo "Generated: $(date)"
        echo "Environment: PYTHONPATH=src FINROOT_LLM_PROVIDER=mock"
        echo ""

        for q in "${QUERIES[@]}"; do
            echo "======================================================================"
            echo "COMMAND: python3 -m interface.cli --mock \"${q}\""
            echo "======================================================================"
            echo ""
            python3 -m interface.cli --mock "${q}" 2>&1 \
                | grep -v "^/" | grep -v "LangChain" | grep -v "Pydantic" | grep -v "LangGraph" \
                | grep -v "UserWarning" | grep -v "DeprecationWarning" || true
            echo ""
            echo ""
        done
    } > "${TXT_FILE}"

    if [[ -f "${TXT_FILE}" ]] && [[ -s "${TXT_FILE}" ]]; then
        recorded=1
        echo "Transcript written to: ${TXT_FILE}"
    fi
fi

if [[ "${recorded}" -eq 0 ]]; then
    echo "ERROR: No recording method succeeded."
    echo "Install asciinema: pip install asciinema"
    echo "Or ensure python3 -m interface.cli runs without error."
    exit 1
fi

echo "Hero demo recording complete."
