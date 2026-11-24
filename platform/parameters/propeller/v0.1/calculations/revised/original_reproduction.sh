#!/usr/bin/env bash
# Run from the package root. Destination must be a new directory.
set -euo pipefail
original_zip=original/av3-05a-deliverables.zip
destination=${1:-original_replay_check}
test ! -e "$destination"
sha256sum -c original/05A-ZIP-SHA256
unzip -tq "$original_zip"
mkdir -p "$destination"
unzip -q "$original_zip" -d "$destination"
cd "$destination"
sha256sum -c SHA256SUMS
python study.py --out reproduced
python verify_interpolation.py --map reproduced/propeller_map.csv --out reproduced/verification_interpolation.json
python annotate_parameter_sources.py reproduced/propeller_parameters.json
for generated in reproduced/*; do cmp "$generated" "${generated##*/}"; done
echo "PASS: all nine numerical files reproduced byte for byte."
