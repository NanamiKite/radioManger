#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."
tools=$(mktemp -d)
trap 'rm -rf "$tools"' EXIT
archive=actionlint_1.7.12_linux_amd64.tar.gz
curl --fail --silent --show-error --location \
    "https://github.com/rhysd/actionlint/releases/download/v1.7.12/$archive" \
    --output "$tools/$archive"
printf '%s  %s\n' \
    8aca8db96f1b94770f1b0d72b6dddcb1ebb8123cb3712530b08cc387b349a3d8 \
    "$tools/$archive" | sha256sum --check --status
tar -xzf "$tools/$archive" -C "$tools" actionlint
"$tools/actionlint" -color -shellcheck= -pyflakes= .github/workflows/*.yml
