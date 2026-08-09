#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# --- Step 1: recover the authoritative snapshot inventory (#RET-7170) -------
# The rollout left /app/data/snapshots.json truncated. Merge the pre-incident
# catalogue with the replay journal and write the result back to that path;
# nothing the reconciler emits is correct until this is done.

python3 "${SCRIPT_DIR}/recover_inventory.py"

# --- Step 2: restore the reconciler and produce the retention artifacts -----

cp "${SCRIPT_DIR}/reconcile_retention_fixed.py" /app/workflow/reconcile_retention.py
python3 /app/workflow/reconcile_retention.py --output-dir /app/output
