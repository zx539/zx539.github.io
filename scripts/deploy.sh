#!/usr/bin/env bash
# Pull the published branch, build the Hugo site, and sync it to Nginx.
# The GitCode webhook service invokes this file after a push.

set -Eeuo pipefail

REPO_DIR="${REPO_DIR:-$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)}"
DEPLOY_DIR="${DEPLOY_DIR:-/var/www/myblog/html}"
REMOTE="${DEPLOY_REMOTE:-origin}"
BRANCH="${DEPLOY_BRANCH:-codex/sakura-template-layout}"
HUGO_BIN="${HUGO_BIN:-hugo}"
export GIT_TERMINAL_PROMPT=0

if [[ ! "$BRANCH" =~ ^[A-Za-z0-9._/-]+$ ]]; then
  echo "invalid DEPLOY_BRANCH: $BRANCH" >&2
  exit 2
fi

if [[ ! -d "$REPO_DIR/.git" ]]; then
  echo "repository not found: $REPO_DIR" >&2
  exit 1
fi

cd "$REPO_DIR"
REPO_DIR="$(pwd -P)"
DEPLOY_DIR="$(realpath -m -- "$DEPLOY_DIR")"
if [[ "$DEPLOY_DIR" == / || "$DEPLOY_DIR" == "$REPO_DIR" || "$REPO_DIR" == "$DEPLOY_DIR/"* ]]; then
  echo "DEPLOY_DIR must be a dedicated website directory" >&2
  exit 2
fi

# Wait instead of discarding a push that arrives during another deployment.
exec 9>"$(git rev-parse --git-path myblog-deploy.lock)"
flock 9
if [[ "$(git branch --show-current)" != "$BRANCH" ]]; then
  echo "checkout branch $BRANCH before deploying" >&2
  exit 1
fi
if [[ -n "$(git status --porcelain --untracked-files=normal)" ]]; then
  echo "repository has local changes; commit or move them before deploying" >&2
  exit 1
fi

echo "[$(date --iso-8601=seconds)] fetching $REMOTE/$BRANCH"
git fetch --no-tags "$REMOTE" "refs/heads/$BRANCH"
git merge --ff-only FETCH_HEAD

# A failed build must never delete or overwrite the currently published site.
BUILD_DIR="$(mktemp -d "${TMPDIR:-/tmp}/myblog-build.XXXXXXXX")"
trap 'rm -rf -- "$BUILD_DIR"' EXIT

echo "[$(date --iso-8601=seconds)] building Hugo site"
"$HUGO_BIN" \
  --gc \
  --minify \
  --panicOnWarning \
  --destination "$BUILD_DIR" \
  --cleanDestinationDir
test -s "$BUILD_DIR/index.html"

echo "[$(date --iso-8601=seconds)] publishing to $DEPLOY_DIR"
mkdir -p "$DEPLOY_DIR"
rsync -a --delete --chmod=D755,F644 "$BUILD_DIR/" "$DEPLOY_DIR/"
echo "[$(date --iso-8601=seconds)] deployment complete: $(git rev-parse --short HEAD)"
