#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ZIP_NAME="finroot-submission.zip"
ZIP_PATH="${REPO_ROOT}/${ZIP_NAME}"
cd "${REPO_ROOT}"

# ---- required files / dirs ----
required=(
    src/ tests/ docs/ evals/ config/ scripts/
    data/samples/ data/gold/ data/tax_rules.json
    README.md pyproject.toml Dockerfile docker-compose.yml
    .github/ CHANGELOG.md
)
kernel_docs=(
    AGENTS.md HANDOFF.md HIERARCHY.md OS_SETUP.md
    BACKLOG.md CONTRIBUTING.md HOW_TO_RUN.md LICENSE
)
for item in "${required[@]}" "${kernel_docs[@]}"; do
    if ! test -e "${REPO_ROOT}/${item}"; then
        echo "FATAL: required path missing: ${item}" >&2
        exit 1
    fi
done

# ---- include list ----
include=(
    "${required[@]}"
    "${kernel_docs[@]}"
)

# results/metrics.json is optional
if test -f results/metrics.json; then
    include+=( results/ )
fi

# ---- exclude patterns ----
exclude=(
    ".git/*"
    "*/__pycache__/*"
    "*.pyc"
    ".venv/*" "venv/*"
    "*.db"
    "data/chroma/*"
    "data/watchlists/*"
    "logs/*"
    ".env"
    "*secret*"
    "*.key"
    "work/*"
    ".pytest_cache/*"
    ".ruff_cache/*"
)

# ---- build zip ----
rm -f "${ZIP_PATH}"
zip_cmd=(zip -r "${ZIP_PATH}" "${include[@]}" -x "${exclude[@]}")
echo "Packaging submission..."
"${zip_cmd[@]}"

# ---- print result ----
size_bytes=$(stat -f%z "${ZIP_PATH}" 2>/dev/null || stat -c%s "${ZIP_PATH}" 2>/dev/null)
file_count=$(unzip -l "${ZIP_PATH}" 2>/dev/null | tail -1 | awk '{print $2}')
echo ""
echo "  ZIP: ${ZIP_NAME}"
echo "  Size: ${size_bytes} bytes"
echo "  Files: ${file_count}"
