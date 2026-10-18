#!/usr/bin/env bash
# Build hall_decorations_hook.gb from the authored RGBDS source.
# Output is written to the private workspace's work/ directory so the main
# builder can read it. Requires legacy RGBDS 0.2.5 (rgbasm + rgblink).
set -euo pipefail

SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE="${PC_WORKSPACE:-$(cd "${SOURCE_DIR}/.." && pwd)}"
OUTPUT_DIR="${WORKSPACE}/work"
RGBDS_DIR="${PC_RGBDS:-${WORKSPACE}/rgbds-0.2.5}"

mkdir -p "${OUTPUT_DIR}"

RGBASM="${RGBDS_DIR}/rgbasm"
RGBLINK="${RGBDS_DIR}/rgblink"

ASM="${SOURCE_DIR}/hall_decorations_hook.asm"
OBJ="${OUTPUT_DIR}/hall_decorations_hook.o"
GB="${OUTPUT_DIR}/hall_decorations_hook.gb"

"${RGBASM}" -o "${OBJ}" "${ASM}"
"${RGBLINK}" -o "${GB}" "${OBJ}"

echo "Built ${GB}"
