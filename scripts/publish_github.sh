#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

# ── defaults ─────────────────────────────────────────────────────────────────
VISIBILITY="--public"
CONFIRM=false
REPO_NAME=""

# ── usage ────────────────────────────────────────────────────────────────────
usage() {
    cat <<EOF
Usage: $(basename "$0") <repo-name> [--private] [--confirm]

Create a GitHub repo, push main, tag v1.0.0, and create a release with notes.

Options:
  <repo-name>   Name for the GitHub repository (required)
  --private     Make the repository private (default: public)
  --confirm     Actually push (default: dry-run mode)
  -h, --help    Show this help

Without --confirm the script prints what it would do and exits 0 (dry-run).
EOF
    exit 0
}

# ── parse args ───────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help) usage ;;
        --private) VISIBILITY="--private"; shift ;;
        --confirm) CONFIRM=true; shift ;;
        -*)        echo "ERROR: unknown flag: $1" >&2; exit 1 ;;
        *)
            if [[ -z "${REPO_NAME}" ]]; then
                REPO_NAME="$1"; shift
            else
                echo "ERROR: unexpected argument: $1" >&2; exit 1
            fi
            ;;
    esac
done

if [[ -z "${REPO_NAME}" ]]; then
    echo "ERROR: <repo-name> is required." >&2
    usage
fi

# ── pre-flight checks ───────────────────────────────────────────────────────

# 1. gh CLI must be installed and authenticated
if ! command -v gh &>/dev/null; then
    echo "ERROR: GitHub CLI (gh) not found." >&2
    echo "  Install : brew install gh  (macOS)  |  https://cli.github.com/" >&2
    echo "  Auth    : gh auth login" >&2
    exit 1
fi

if ! gh auth status &>/dev/null; then
    echo "ERROR: gh CLI is not authenticated." >&2
    echo "  Run: gh auth login" >&2
    exit 1
fi

# 2. Clean working tree
if [[ -n "$(git status --porcelain 2>/dev/null)" ]]; then
    echo "ERROR: working tree is dirty. Commit or stash changes first." >&2
    git status --short >&2
    exit 1
fi

# 3. No .env tracked
if git ls-files --error-unmatch .env &>/dev/null; then
    echo "ERROR: .env is tracked in git. Remove it (git rm --cached .env) before publishing." >&2
    exit 1
fi

# 4. No secret-like files tracked
secret_patterns=("*.key" "*.pem" ".env" "*secret*")
for pat in "${secret_patterns[@]}"; do
    matches=$(git ls-files "${pat}" 2>/dev/null || true)
    if [[ -n "${matches}" ]]; then
        echo "ERROR: files matching '${pat}' are tracked in git:" >&2
        echo "${matches}" >&2
        echo "Remove them before publishing (FM-07)." >&2
        exit 1
    fi
done

# 5. results/metrics.json present
if [[ ! -f results/metrics.json ]]; then
    echo "ERROR: results/metrics.json not found. Run evals first (FM-05/12)." >&2
    exit 1
fi

# 6. Release notes present
if [[ ! -f docs/RELEASE_NOTES.md ]]; then
    echo "ERROR: docs/RELEASE_NOTES.md not found." >&2
    exit 1
fi

# ── compute tag ──────────────────────────────────────────────────────────────
TAG="v1.0.0"
TAG_MSG="FinRoot v1.0.0 -- SCALE PS-1 submission"
RELEASE_TITLE="FinRoot v1.0.0"

# ── dry-run vs confirm ──────────────────────────────────────────────────────
if [[ "${CONFIRM}" == false ]]; then
    echo "=== DRY RUN (no changes made) ==="
    echo ""
    echo "Would execute:"
    echo "  1. gh repo create ${REPO_NAME} --source=. --push ${VISIBILITY}"
    echo "  2. git tag -a ${TAG} -m \"${TAG_MSG}\""
    echo "  3. git push origin ${TAG}"
    echo "  4. gh release create ${TAG} \\"
    echo "       --title \"${RELEASE_TITLE}\" \\"
    echo "       --notes-file docs/RELEASE_NOTES.md"
    if [[ -f finroot-submission.zip ]]; then
        echo "  5. Attach finroot-submission.zip to the release"
    fi
    echo ""
    echo "Re-run with --confirm to execute."
    exit 0
fi

# ── confirm path: create repo + push ────────────────────────────────────────
echo "Creating repo '${REPO_NAME}' on GitHub (${VISIBILITY})..."
gh repo create "${REPO_NAME}" --source=. --push ${VISIBILITY}

# ── tag ──────────────────────────────────────────────────────────────────────
echo "Tagging ${TAG}..."
git tag -a "${TAG}" -m "${TAG_MSG}"
git push origin "${TAG}"

# ── release ──────────────────────────────────────────────────────────────────
echo "Creating release ${TAG}..."
release_args=(
    "${TAG}"
    --title "${RELEASE_TITLE}"
    --notes-file docs/RELEASE_NOTES.md
)
if [[ -f finroot-submission.zip ]]; then
    release_args+=( --attach finroot-submission.zip )
    echo "  Attaching finroot-submission.zip"
fi

gh release create "${release_args[@]}"

# ── done ─────────────────────────────────────────────────────────────────────
REPO_URL="https://github.com/$(gh api user --jq .login)/${REPO_NAME}"
echo ""
echo "Done! Repo: ${REPO_URL}"
echo "Release: ${REPO_URL}/releases/tag/${TAG}"
