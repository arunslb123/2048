#!/usr/bin/env bash
# Clone every source repo (shallow) into ./repos, the layout the scripts expect.
# repos_pinned.txt records the exact commit analysed; re-clones get the current HEAD.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p repos
while read -r repo sha date; do
  dir="repos/${repo/\//__}"
  [ -d "$dir" ] || git clone --depth 1 -q "https://github.com/$repo" "$dir"
  echo "$repo  analysed=$sha ($date)  now=$(git -C "$dir" rev-parse --short HEAD)"
done < repos_pinned.txt
