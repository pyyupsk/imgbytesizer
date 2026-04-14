#!/usr/bin/env bash
set -euo pipefail

# Usage: scripts/release.sh <patch|minor|major|VERSION>

BUMP="${1:?Usage: scripts/release.sh <patch|minor|major|VERSION>}"

# Ensure clean working tree
if [ -n "$(git status --porcelain)" ]; then
  echo "❌ Working tree is dirty. Commit or stash changes first."
  exit 1
fi

# Ensure on main branch
BRANCH=$(git branch --show-current)
if [ "$BRANCH" != "main" ]; then
  echo "❌ Must be on main branch (currently on $BRANCH)"
  exit 1
fi

# Bump version
case "$BUMP" in
  patch|minor|major)
    uv version --bump "$BUMP"
    ;;
  *)
    uv version "$BUMP"
    ;;
esac

VERSION=$(uv version --short)
TAG="v${VERSION}"

echo "📦 Releasing ${TAG}..."

# Stage and commit
git add pyproject.toml uv.lock
git commit -m "chore: release ${TAG}"

# Tag
git tag -a "$TAG" -m "Release ${TAG}"

# Push commit and tag
git push origin main --tags

echo "✅ ${TAG} pushed. CI will publish to PyPI and generate changelog."
