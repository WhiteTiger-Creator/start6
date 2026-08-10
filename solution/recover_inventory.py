#!/usr/bin/env python3
"""Rebuild the authoritative snapshot inventory truncated by the failed rollout.

Implements the storage governance board's final recovery decision (#RET-7170 in
/app/incident/retention_governance_log.md), which supersedes the #RET-7002 draft
and revises the #RET-7009 interim: start from the pre-incident catalogue in file
order, then replay the journal in ascending journal_seq order; an ``append``
entry overwrites the first record already carrying that snapshot_id in place
(and is otherwise appended to the end), a ``retract`` entry removes every record
with that snapshot_id, journal bookkeeping fields never reach the recovered
inventory, and the result is written back to /app/data/snapshots.json.
"""

from __future__ import annotations

import json
from pathlib import Path

INVENTORY_PATH = Path("/app/data/snapshots.json")
CATALOGUE_PATH = Path("/app/data/snapshot_catalogue_pre_incident.json")
JOURNAL_PATH = Path("/app/data/snapshot_replay_journal.json")

SNAPSHOT_FIELDS = ("snapshot_id", "repo", "vault", "ts", "size_bytes", "pinned", "note")


def recover(catalogue: list[dict], journal: list[dict]) -> list[dict]:
    """Replay the journal onto the catalogue.

    The position of the FIRST record carrying each snapshot_id is indexed once,
    so an append overwrites in place without rescanning the inventory and a
    retract is applied as a single filtering pass at the end. Rescanning the
    whole inventory per journal entry is quadratic at catalogue scale.
    """
    inventory: list[dict | None] = [dict(record) for record in catalogue]
    first: dict[str, int] = {}
    for index, record in enumerate(inventory):
        first.setdefault(record["snapshot_id"], index)

    for entry in sorted(journal, key=lambda e: e["journal_seq"]):
        snapshot_id = entry["snapshot_id"]
        if entry["journal_op"] == "retract":
            for index, existing in enumerate(inventory):
                if existing is not None and existing["snapshot_id"] == snapshot_id:
                    inventory[index] = None
            first.pop(snapshot_id, None)
            continue
        record = {field: entry[field] for field in SNAPSHOT_FIELDS}
        index = first.get(snapshot_id)
        if index is not None:
            inventory[index] = record
        else:
            first[snapshot_id] = len(inventory)
            inventory.append(record)
    return [record for record in inventory if record is not None]


def main() -> None:
    catalogue = json.loads(CATALOGUE_PATH.read_text(encoding="utf-8"))
    journal = json.loads(JOURNAL_PATH.read_text(encoding="utf-8"))
    recovered = recover(catalogue, journal)
    INVENTORY_PATH.write_text(json.dumps(recovered, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
