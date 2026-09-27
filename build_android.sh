#!/usr/bin/env bash
# Build the Android package for Humbly Plural using Buildozer.
# Run this from the repo root in a Linux environment or WSL.

set -e

if ! command -v buildozer >/dev/null 2>&1; then
  echo "Buildozer is not installed. Install it first with:"
  echo "  python3 -m pip install buildozer"
  exit 1
fi

cd "$(dirname "$0")"

echo "Running Buildozer debug build..."
buildozer android debug

echo "Build complete."
echo "The output APK should be in the ./.buildozer/android/platform/build/dists/humblyplural/bin/ directory."
