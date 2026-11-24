#!/usr/bin/env bash
set -euo pipefail
package=av3-05ar-deliverables.zip
files=(README.md technical_review.md decision_register.md source_register.md verification_report.md
       model.py review.py checks.py plot_maps.py original_reproduction.sh package.sh environment.json original_run.log)
find inputs original outputs -type f -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS
sha256sum "${files[@]}" >> SHA256SUMS
rm -f "$package"
zip -q -9 -r "$package" "${files[@]}" SHA256SUMS inputs original outputs
sha256sum "$package" > "$package.sha256"
sha256sum -c "$package.sha256"
unzip -tq "$package"
