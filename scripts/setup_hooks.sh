#!/usr/bin/env bash
# Install all FinRoot git hooks
set -euo pipefail
cd "$(dirname "$0")/.." || exit

HOOKS_DIR=".git/hooks"
mkdir -p "$HOOKS_DIR"

# Pre-commit hook
cat > "$HOOKS_DIR/pre-commit" << 'HOOK'
#!/usr/bin/env bash
set -euo pipefail
echo "=== FinRoot pre-commit ==="

# Ruff lint + format
echo "  ruff check ..."
ruff check src/ tests/ scripts/ config/ --fix
ruff format src/ tests/ scripts/ config/

# Block secrets
echo "  block-secrets ..."
bash orchestrator/hooks/block-secrets.sh

# Validate execution docs
echo "  validate-execution ..."
bash orchestrator/scripts/validate_execution.sh

echo "=== pre-commit passed ==="
HOOK
chmod +x "$HOOKS_DIR/pre-commit"

# Pre-push hook (optional)
if [ ! -f "$HOOKS_DIR/pre-push" ]; then
  cat > "$HOOKS_DIR/pre-push" << 'HOOK'
#!/usr/bin/env bash
set -euo pipefail
echo "=== FinRoot pre-push ==="
bash orchestrator/hooks/pre-push
echo "=== pre-push passed ==="
HOOK
  chmod +x "$HOOKS_DIR/pre-push"
fi

echo "Hooks installed to $HOOKS_DIR"
