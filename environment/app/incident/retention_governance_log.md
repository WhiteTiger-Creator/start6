# Backup / Storage Retention Reconciler — Governance Review Log
Storage governance archive for the failed backup-platform rollout (2026-Q1 through 2026-Q2).

## Executive Summary
How the retention reconciler is *meant* to behave — the recovery of the truncated snapshot inventory, canonicalization, deduplication, the governance calendar bucket assignment, per-bucket representative selection, per-tier caps, the pinned-hold exemption, cross-tier promotion, the stateful per-repo quota ledger, prune ordering and the per-repo prune cap — was settled incrementally by the storage governance board, and those decisions live in the review entries below, not in any single summary. Several stages deliberately DEVIATE from a standard age-based GFS ("keep the last N per period"): the calendar boundaries, the earliest-of-bucket representative, the pinned exemption and the cross-tier promotion are governance dialects, so a stock GFS scheduler keeps a DIFFERENT set. The February draft proposals were revisited during the 2026-05 governance review and several were reversed; where a draft or interim conflicts with a later decision, the later dated decision governs. `/app/docs/report_spec.json` is the output contract only.

## Governance Review Archive
Routine entries are context only. #RET-ticketed proposal and decision quotes are the authoritative record for reconciler behaviour.

### Review entry 1000 — vault/pg repo
Shift lead logged a routine observation for vault/pg during retention window 1000. Snapshot volume tiles lagged during the retention sweep; attributed to catalog cache staleness, not the reconciler.
Reviewers should reconcile behaviour questions against #RET governance decisions rather than chat excerpts.

### Review entry 1001 — vault/redis repo
Shift lead logged a routine observation for vault/redis during retention window 1001. Vault key-rotation drill touched this repo; no reconciler-relevant configuration changed.
Thread archived; see the #RET decision entries for anything affecting reconciler behaviour.

### Review entry 1002 — media/assets repo
Shift lead logged a routine observation for media/assets during retention window 1002. Object-store lifecycle audit sampled cross-account roles; no reconciler-relevant findings for this repo.
Historical tape indices remain archived and non-authoritative for the JSON reconciler acceptance.

### Review entry 1003 — vault/obj repo
Shift lead logged a routine observation for vault/obj during retention window 1003. Synthetic restore verification confirmed the snapshot chain for this repo mounts cleanly.
> **Recovery draft proposal (2026-02-05 - #RET-7004)** Anders: the retention calendar uses naive floor-division: gday = ts // 86400 on a midnight boundary, weeks are ts // 604800, months ts // 2592000 and years ts // 31536000, matching a stock GFS scheduler *(Superseded — see the 2026-05 governance review.)*
No reconciler semantics changed in this entry; parameters remain as approved by the governance board.

### Review entry 1004 — archive/cold repo
Shift lead logged a routine observation for archive/cold during retention window 1004. Noise review: repeated snapshot ids traced to a flapping backup agent, quiesced at the source.
> **Recovery draft proposal (2026-02-16 - #RET-7002)** Anders: should a rollout ever truncate the snapshot inventory, rebuild it by concatenating the pre-incident catalogue and the replay journal in file order and let the snapshot_id deduplication stage settle whatever overlaps; journal bookkeeping fields are inert and may stay on the records *(Superseded — reversed in the 2026-06 governance review.)*
Reviewers should reconcile behaviour questions against #RET governance decisions rather than chat excerpts.

### Review entry 1005 — vault/app repo
Shift lead logged a routine observation for vault/app during retention window 1005. Capacity review noted rising snapshot sizes; caps unchanged outside the governance process.
> **Recovery draft proposal (2026-02-06 - #RET-7006)** Anders: per-bucket representative is the LATEST snapshot in each period (standard GFS keep-newest), tie-break by larger size *(Superseded — see the 2026-05 governance review.)*
Thread archived; see the #RET decision entries for anything affecting reconciler behaviour.

### Review entry 1006 — vault/pg repo
Shift lead logged a routine observation for vault/pg during retention window 1006. Replica scrub drill completed; snapshot manifests stayed within the retention SLO.
Historical tape indices remain archived and non-authoritative for the JSON reconciler acceptance.

### Review entry 1007 — vault/redis repo
Shift lead logged a routine observation for vault/redis during retention window 1007. Change-board reviewed stale retention exceptions; owners pinged before the next reconcile cycle.
> **Recovery draft proposal (2026-02-07 - #RET-7020)** Rosa: keep the last cap_daily/cap_weekly/cap_monthly/cap_yearly snapshots per tier purely by age *(Superseded — see the 2026-05 governance review.)*
No reconciler semantics changed in this entry; parameters remain as approved by the governance board.

### Review entry 1008 — media/assets repo
Shift lead logged a routine observation for media/assets during retention window 1008. Cold-tier tape rehearsal ran clean; no changes to reconciler parameters were approved.
Reviewers should reconcile behaviour questions against #RET governance decisions rather than chat excerpts.

### Review entry 1009 — vault/obj repo
Shift lead logged a routine observation for vault/obj during retention window 1009. Vendor ticket on backup-agent retries closed; catalog delivery within the contractual budget.
> **Recovery draft proposal (2026-02-08 - #RET-7022)** Rosa: tiers are independent: keep a separate snapshot for each tier even when one snapshot would satisfy several, and the kept count is the SUM of the per-tier keeps *(Superseded — see the 2026-05 governance review.)*
Thread archived; see the #RET decision entries for anything affecting reconciler behaviour.

### Review entry 1010 — archive/cold repo
Shift lead logged a routine observation for archive/cold during retention window 1010. Snapshot volume tiles lagged during the retention sweep; attributed to catalog cache staleness, not the reconciler.
Historical tape indices remain archived and non-authoritative for the JSON reconciler acceptance.

### Review entry 1011 — vault/app repo
Shift lead logged a routine observation for vault/app during retention window 1011. Vault key-rotation drill touched this repo; no reconciler-relevant configuration changed.
> **Recovery draft proposal (2026-02-09 - #RET-7024)** Anders: the pinned flag and the pin registry are advisory only and never change which snapshots are kept or pruned *(Superseded — see the 2026-05 governance review.)*
No reconciler semantics changed in this entry; parameters remain as approved by the governance board.

### Review entry 1012 — vault/pg repo
Shift lead logged a routine observation for vault/pg during retention window 1012. Object-store lifecycle audit sampled cross-account roles; no reconciler-relevant findings for this repo.
Reviewers should reconcile behaviour questions against #RET governance decisions rather than chat excerpts.

### Review entry 1013 — vault/redis repo
Shift lead logged a routine observation for vault/redis during retention window 1013. Synthetic restore verification confirmed the snapshot chain for this repo mounts cleanly.
> **Recovery draft proposal (2026-02-11 - #RET-7040)** Rosa: prune every snapshot that is not kept in a single cycle; there is no per-repo prune cap and no deferral *(Superseded — see the 2026-05 governance review.)*
Thread archived; see the #RET decision entries for anything affecting reconciler behaviour.

### Review entry 1014 — media/assets repo
Shift lead logged a routine observation for media/assets during retention window 1014. Noise review: repeated snapshot ids traced to a flapping backup agent, quiesced at the source.
Historical tape indices remain archived and non-authoritative for the JSON reconciler acceptance.

### Review entry 1015 — vault/obj repo
Shift lead logged a routine observation for vault/obj during retention window 1015. Capacity review noted rising snapshot sizes; caps unchanged outside the governance process.
> **Governance decision (2026-03-05 - #RET-7109)** Rosa: deduplicate by snapshot_id keeping the FIRST-seen row in input order; ts and size do not override that *(Revised — see the 2026-05 governance review.)*
No reconciler semantics changed in this entry; parameters remain as approved by the governance board.

### Review entry 1016 — archive/cold repo
Shift lead logged a routine observation for archive/cold during retention window 1016. Replica scrub drill completed; snapshot manifests stayed within the retention SLO.
> **Governance decision (2026-03-09 - #RET-7009)** Priya: inventory recovery interim: the replay journal outranks the pre-incident catalogue on overlap, but a replayed snapshot is appended to the END of the rebuilt inventory rather than taking the catalogue record's position, and a retraction only applies to snapshot_ids the catalogue never held *(Revised — see the 2026-06 governance review.)*
Reviewers should reconcile behaviour questions against #RET governance decisions rather than chat excerpts.

### Review entry 1017 — vault/app repo
Shift lead logged a routine observation for vault/app during retention window 1017. Change-board reviewed stale retention exceptions; owners pinged before the next reconcile cycle.
> **Governance decision (2026-03-06 - #RET-7115)** Priya: quota ledger interim: decay and size both FLOOR — carry_in = max(prev.used_quota - idle_gap // 86400, 0), size_mb = size_bytes // 1048576, and there is NO reset boundary *(Revised — see the 2026-05 governance review.)*
Thread archived; see the #RET decision entries for anything affecting reconciler behaviour.

### Review entry 1018 — vault/pg repo
Shift lead logged a routine observation for vault/pg during retention window 1018. Cold-tier tape rehearsal ran clean; no changes to reconciler parameters were approved.
Historical tape indices remain archived and non-authoritative for the JSON reconciler acceptance.

### Review entry 1019 — vault/redis repo
Shift lead logged a routine observation for vault/redis during retention window 1019. Vendor ticket on backup-agent retries closed; catalog delivery within the contractual budget.
> **Governance decision (2026-03-08 - #RET-7048)** Yusuf: max_quota_used is taken over the FINAL pruned rows only *(Revised — see the 2026-05 governance review.)*
No reconciler semantics changed in this entry; parameters remain as approved by the governance board.

### Review entry 1020 — media/assets repo
Shift lead logged a routine observation for media/assets during retention window 1020. Snapshot volume tiles lagged during the retention sweep; attributed to catalog cache staleness, not the reconciler.
Reviewers should reconcile behaviour questions against #RET governance decisions rather than chat excerpts.

### Review entry 1021 — vault/obj repo
Shift lead logged a routine observation for vault/obj during retention window 1021. Vault key-rotation drill touched this repo; no reconciler-relevant configuration changed.
> **Governance decision (2026-05-02 - #RET-7101)** Yusuf: canonicalization: repo and vault via str(...).strip().lower() (empty -> 'unassigned'); note collapses internal whitespace; size_bytes and ts coerce int(str(x).strip()), else int(float(...)), else 0 — a size or ts that fails still KEEPS the row; pinned — booleans unchanged, strings true/1/yes/pinned => true, other strings => false, non-string/non-bool via bool(value)
Thread archived; see the #RET decision entries for anything affecting reconciler behaviour.

### Review entry 1022 — archive/cold repo
Shift lead logged a routine observation for archive/cold during retention window 1022. Object-store lifecycle audit sampled cross-account roles; no reconciler-relevant findings for this repo.
Historical tape indices remain archived and non-authoritative for the JSON reconciler acceptance.

### Review entry 1023 — vault/app repo
Shift lead logged a routine observation for vault/app during retention window 1023. Synthetic restore verification confirmed the snapshot chain for this repo mounts cleanly.
> **Governance decision (2026-05-03 - #RET-7102)** Yusuf: deduplicate by snapshot_id (final chain, revising #RET-7109): keep the row with the HIGHEST ts; tie-break by size_bytes (direction set by #RET-7142), then longer normalized note, then lexicographically larger normalized repo, then first-seen input order
No reconciler semantics changed in this entry; parameters remain as approved by the governance board.

### Review entry 1024 — vault/pg repo
Shift lead logged a routine observation for vault/pg during retention window 1024. Noise review: repeated snapshot ids traced to a flapping backup agent, quiesced at the source.
Reviewers should reconcile behaviour questions against #RET governance decisions rather than chat excerpts.

### Review entry 1025 — vault/redis repo
Shift lead logged a routine observation for vault/redis during retention window 1025. Capacity review noted rising snapshot sizes; caps unchanged outside the governance process.
> **Governance decision (2026-05-14 - #RET-7142)** Yusuf: duplicate size precedence is REVERSED. Watchdog re-emissions inflate a repeated snapshot's recorded size before an operator confirms it, so where two rows share a snapshot_id and tie on ts, keep the row with the LOWER size_bytes. Only this comparison changes; the rest of the #RET-7102 chain runs unchanged after it
Thread archived; see the #RET decision entries for anything affecting reconciler behaviour.

### Review entry 1026 — media/assets repo
Shift lead logged a routine observation for media/assets during retention window 1026. Replica scrub drill completed; snapshot manifests stayed within the retention SLO.
Historical tape indices remain archived and non-authoritative for the JSON reconciler acceptance.

### Review entry 1027 — vault/obj repo
Shift lead logged a routine observation for vault/obj during retention window 1027. Change-board reviewed stale retention exceptions; owners pinged before the next reconcile cycle.
> **Governance decision (2026-05-04 - #RET-7104)** Lena: governance retention calendar (integer epoch-seconds, deviates from ISO week and naive floor-division): a retention DAY rolls at 04:00 UTC not midnight so gday = (ts - 14400) // 86400; the retention WEEK starts Sunday not ISO Monday so gweek = (gday - 3) // 7; the retention MONTH is a fixed 30-day block gmonth = gday // 30 (NOT a calendar month); the retention YEAR is a fixed 360-day block gyear = gday // 360. Compute every bucket id from these integer formulas: not one of these boundaries is the one a calendar library would give you, so a library's own day, week, month or year semantics will not reproduce them. Supersedes #RET-7004
No reconciler semantics changed in this entry; parameters remain as approved by the governance board.

### Review entry 1028 — archive/cold repo
Shift lead logged a routine observation for archive/cold during retention window 1028. Cold-tier tape rehearsal ran clean; no changes to reconciler parameters were approved.
Reviewers should reconcile behaviour questions against #RET governance decisions rather than chat excerpts.

### Review entry 1029 — vault/app repo
Shift lead logged a routine observation for vault/app during retention window 1029. Vendor ticket on backup-agent retries closed; catalog delivery within the contractual budget.
> **Governance decision (2026-05-04 - #RET-7106)** Lena: per-bucket representative (deviates from standard GFS keep-newest): within a bucket the representative is the snapshot with the SMALLEST ts (the sealed period marker), tie-break by LARGER size_bytes then snapshot_id ascending. Supersedes #RET-7006
Thread archived; see the #RET decision entries for anything affecting reconciler behaviour.

### Review entry 1030 — vault/pg repo
Shift lead logged a routine observation for vault/pg during retention window 1030. Snapshot volume tiles lagged during the retention sweep; attributed to catalog cache staleness, not the reconciler.
Historical tape indices remain archived and non-authoritative for the JSON reconciler acceptance.

### Review entry 1031 — vault/redis repo
Shift lead logged a routine observation for vault/redis during retention window 1031. Vault key-rotation drill touched this repo; no reconciler-relevant configuration changed.
> **Governance decision (2026-05-07 - #RET-7120)** Lena: per-tier caps select the most-recent buckets: for each tier compute every bucket's representative, then select the C buckets with the GREATEST bucket id (most recent), C being the resolved cap_daily/cap_weekly/cap_monthly/cap_yearly; the representative of each selected bucket is kept for that tier. Supersedes #RET-7020
No reconciler semantics changed in this entry; parameters remain as approved by the governance board.

### Review entry 1032 — media/assets repo
Shift lead logged a routine observation for media/assets during retention window 1032. Object-store lifecycle audit sampled cross-account roles; no reconciler-relevant findings for this repo.
Reviewers should reconcile behaviour questions against #RET governance decisions rather than chat excerpts.

### Review entry 1033 — vault/obj repo
Shift lead logged a routine observation for vault/obj during retention window 1033. Synthetic restore verification confirmed the snapshot chain for this repo mounts cleanly.
> **Governance decision (2026-05-08 - #RET-7124)** Priya: pinned-hold exemption (deviates from GFS which ignores pins): a snapshot is HELD if its event pinned flag is true OR (repo, snapshot_id) appears in /app/data/pin_registry.json with a recognized hold in {compliance, legal, manual}; a held snapshot is ALWAYS kept regardless of caps and buckets, and carries the 'pinned' role. Every emitted row also carries a hold label: 'flag' when the snapshot is held by its own event pinned flag, otherwise the recognized registry hold label, otherwise the empty string. Supersedes #RET-7024
Thread archived; see the #RET decision entries for anything affecting reconciler behaviour.

### Review entry 1034 — archive/cold repo
Shift lead logged a routine observation for archive/cold during retention window 1034. Noise review: repeated snapshot ids traced to a flapping backup agent, quiesced at the source.
Historical tape indices remain archived and non-authoritative for the JSON reconciler acceptance.

### Review entry 1035 — vault/app repo
Shift lead logged a routine observation for vault/app during retention window 1035. Capacity review noted rising snapshot sizes; caps unchanged outside the governance process.
> **Governance decision (2026-05-08 - #RET-7122)** Priya: cross-tier promotion (deviates from independent-tier GFS): the kept set is the UNION over tiers of the selected-bucket representatives plus the held snapshots. A single snapshot that represents selected buckets in several tiers carries ALL those tier roles at once — a kept daily also satisfies the weekly/monthly/yearly slot it marks — so the kept COUNT is the union, not the sum, of the per-tier selections. A kept snapshot's roles list the tiers it represents in daily,weekly,monthly,yearly order, with 'pinned' appended when held. Supersedes #RET-7022
No reconciler semantics changed in this entry; parameters remain as approved by the governance board.

### Review entry 1036 — vault/pg repo
Shift lead logged a routine observation for vault/pg during retention window 1036. Replica scrub drill completed; snapshot manifests stayed within the retention SLO.
Reviewers should reconcile behaviour questions against #RET governance decisions rather than chat excerpts.

### Review entry 1037 — vault/redis repo
Shift lead logged a routine observation for vault/redis during retention window 1037. Change-board reviewed stale retention exceptions; owners pinged before the next reconcile cycle.
> **Governance decision (2026-05-06 - #RET-7116)** Yusuf: per-repo quota ledger: state is independent per repo; process each repo's KEPT snapshots in ascending (ts, snapshot_id) order. First kept snapshot: idle_gap=0, carry_in=0. Later: idle_gap = max(current.ts - previous.ts, 0); if idle_gap exceeds the reset boundary of 2592000 seconds (30 days) the quota RESETS so carry_in=0, otherwise carry_in = max(previous.used_quota - decay(idle_gap), 0); used_quota = min(carry_in + size_mb, quota_cap) with quota_cap the resolved policy value. Decay rounding is set by #RET-7160 and size_mb by #RET-7162. The ledger runs over kept snapshots only, so idle_gap, carry_in and used_quota are reported as 0 on pruned and deferred rows, while size_mb is reported on every row from that row's own size_bytes. Supersedes #RET-7115 on structure
Thread archived; see the #RET decision entries for anything affecting reconciler behaviour.

### Review entry 1038 — media/assets repo
Shift lead logged a routine observation for media/assets during retention window 1038. Cold-tier tape rehearsal ran clean; no changes to reconciler parameters were approved.
Historical tape indices remain archived and non-authoritative for the JSON reconciler acceptance.

### Review entry 1039 — vault/obj repo
Shift lead logged a routine observation for vault/obj during retention window 1039. Vendor ticket on backup-agent retries closed; catalog delivery within the contractual budget.
> **Governance decision (2026-05-28 - #RET-7160)** Yusuf: ledger idle-gap decay rounding, final: decay(idle_gap) = ceil(idle_gap / 86400) — one quota unit per whole idle day, ROUNDED UP, revising the floor in #RET-7115. In integer arithmetic ceil(x/n) is -(-x // n)
No reconciler semantics changed in this entry; parameters remain as approved by the governance board.

### Review entry 1040 — archive/cold repo
Shift lead logged a routine observation for archive/cold during retention window 1040. Snapshot volume tiles lagged during the retention sweep; attributed to catalog cache staleness, not the reconciler.
Reviewers should reconcile behaviour questions against #RET governance decisions rather than chat excerpts.

### Review entry 1041 — vault/app repo
Shift lead logged a routine observation for vault/app during retention window 1041. Vault key-rotation drill touched this repo; no reconciler-relevant configuration changed.
> **Governance decision (2026-05-29 - #RET-7162)** Yusuf: ledger size quantum, final: size_mb = ceil(size_bytes / 1048576) (bytes per MiB, ROUNDED UP), revising the floor draft — a partially filled MiB still consumes a whole quota unit; used_quota accumulates size_mb
Thread archived; see the #RET decision entries for anything affecting reconciler behaviour.

### Review entry 1042 — vault/pg repo
Shift lead logged a routine observation for vault/pg during retention window 1042. Object-store lifecycle audit sampled cross-account roles; no reconciler-relevant findings for this repo.
Historical tape indices remain archived and non-authoritative for the JSON reconciler acceptance.

### Review entry 1043 — vault/redis repo
Shift lead logged a routine observation for vault/redis during retention window 1043. Synthetic restore verification confirmed the snapshot chain for this repo mounts cleanly.
> **Governance decision (2026-05-10 - #RET-7145)** Marek: prune and decision ordering: order every prune candidate WITHIN a repo by size_bytes DESC, then ts ASC, then snapshot_id ASC (reclaim the largest, oldest first). The retention_decisions rows are emitted globally sorted by decision class rank prune < defer < keep, then size_bytes DESC, then ts ASC, then repo ASC, then snapshot_id ASC
No reconciler semantics changed in this entry; parameters remain as approved by the governance board.

### Review entry 1044 — media/assets repo
Shift lead logged a routine observation for media/assets during retention window 1044. Noise review: repeated snapshot ids traced to a flapping backup agent, quiesced at the source.
Reviewers should reconcile behaviour questions against #RET governance decisions rather than chat excerpts.

### Review entry 1045 — vault/obj repo
Shift lead logged a routine observation for vault/obj during retention window 1045. Capacity review noted rising snapshot sizes; caps unchanged outside the governance process.
> **Governance decision (2026-05-24 - #RET-7146)** Marek: per-repo prune cap: after ordering a repo's prune candidates by #RET-7145, only the FIRST prune_cap (resolved policy) candidates are pruned this cycle with decision 'prune'; the remainder are DEFERRED with decision 'defer' for a later cycle. Kept snapshots take decision 'keep'. Supersedes #RET-7040
Thread archived; see the #RET decision entries for anything affecting reconciler behaviour.

### Review entry 1046 — archive/cold repo
Shift lead logged a routine observation for archive/cold during retention window 1046. Replica scrub drill completed; snapshot manifests stayed within the retention SLO.
Historical tape indices remain archived and non-authoritative for the JSON reconciler acceptance.

### Review entry 1047 — vault/app repo
Shift lead logged a routine observation for vault/app during retention window 1047. Change-board reviewed stale retention exceptions; owners pinged before the next reconcile cycle.
> **Governance decision (2026-05-10 - #RET-7148)** Yusuf: summary aggregation (final, revising #RET-7048): decision_counts enumerates keep, prune, defer in that fixed order using 0 when absent; max_quota_used is the maximum used_quota over EVERY kept snapshot using 0 when none; reclaimed_size_bytes sums the size_bytes of pruned snapshots and deferred_size_bytes the deferred ones
No reconciler semantics changed in this entry; parameters remain as approved by the governance board.

### Review entry 1048 — vault/pg repo
Shift lead logged a routine observation for vault/pg during retention window 1048. Cold-tier tape rehearsal ran clean; no changes to reconciler parameters were approved.
Reviewers should reconcile behaviour questions against #RET governance decisions rather than chat excerpts.

### Review entry 1049 — vault/redis repo
Shift lead logged a routine observation for vault/redis during retention window 1049. Vendor ticket on backup-agent retries closed; catalog delivery within the contractual budget.
> **Governance decision (2026-05-16 - #RET-7144)** Priya: retention week boundary realigned to the ISO Monday start so the weekly rollup lines up with the platform reporting week: gweek = (gday - 4) // 7. This revises the Sunday start of #RET-7104; the day, month and year boundaries stated there are untouched

> **Governance decision (2026-05-18 - #RET-7150)** Priya: retention policy baseline (read from /app/data/retention_policy.json at that fixed absolute path; --input never relocates it). Any field the policy file omits keeps its baseline: cap_daily=7; cap_weekly=4; cap_monthly=6; cap_yearly=2; quota_cap=100000; prune_cap=4200; protection_days=21
Thread archived; see the #RET decision entries for anything affecting reconciler behaviour.

### Review entry 1050 — media/assets repo
Shift lead logged a routine observation for media/assets during retention window 1050. Snapshot volume tiles lagged during the retention sweep; attributed to catalog cache staleness, not the reconciler.
Historical tape indices remain archived and non-authoritative for the JSON reconciler acceptance.

### Review entry 1051 — vault/obj repo
Shift lead logged a routine observation for vault/obj during retention window 1051. Vault key-rotation drill touched this repo; no reconciler-relevant configuration changed.
> **Governance decision (2026-05-18 - #RET-7152)** Priya: policy resolution, per repo, in three layers: start from the #RET-7150 baseline; overlay every field the policy file's default object supplies (it need not be complete — an omitted field keeps its baseline); then overlay every field that repo's entry in repo_overrides supplies (an override names only the fields it changes and inherits the rest). Coerce every value to int
No reconciler semantics changed in this entry; parameters remain as approved by the governance board.

### Review entry 1052 — archive/cold repo
Shift lead logged a routine observation for archive/cold during retention window 1052. Object-store lifecycle audit sampled cross-account roles; no reconciler-relevant findings for this repo.
Reviewers should reconcile behaviour questions against #RET governance decisions rather than chat excerpts.

### Review entry 1053 — vault/app repo
Shift lead logged a routine observation for vault/app during retention window 1053. Synthetic restore verification confirmed the snapshot chain for this repo mounts cleanly.
Thread archived; see the #RET decision entries for anything affecting reconciler behaviour.

### Review entry 1054 — vault/pg repo
Shift lead logged a routine observation for vault/pg during retention window 1054. Noise review: repeated snapshot ids traced to a flapping backup agent, quiesced at the source.
Historical tape indices remain archived and non-authoritative for the JSON reconciler acceptance.

### Review entry 1055 — vault/redis repo
Shift lead logged a routine observation for vault/redis during retention window 1055. Capacity review noted rising snapshot sizes; caps unchanged outside the governance process.
No reconciler semantics changed in this entry; parameters remain as approved by the governance board.

### Review entry 1056 — media/assets repo
Shift lead logged a routine observation for media/assets during retention window 1056. Replica scrub drill completed; snapshot manifests stayed within the retention SLO.
Reviewers should reconcile behaviour questions against #RET governance decisions rather than chat excerpts.

### Review entry 1057 — vault/obj repo
Shift lead logged a routine observation for vault/obj during retention window 1057. Change-board reviewed stale retention exceptions; owners pinged before the next reconcile cycle.
Thread archived; see the #RET decision entries for anything affecting reconciler behaviour.

### Review entry 1058 — archive/cold repo
Shift lead logged a routine observation for archive/cold during retention window 1058. Cold-tier tape rehearsal ran clean; no changes to reconciler parameters were approved.
Historical tape indices remain archived and non-authoritative for the JSON reconciler acceptance.

### Review entry 1059 — vault/app repo
Shift lead logged a routine observation for vault/app during retention window 1059. Vendor ticket on backup-agent retries closed; catalog delivery within the contractual budget.
No reconciler semantics changed in this entry; parameters remain as approved by the governance board.

### Review entry 1060 — vault/pg repo
Shift lead logged a routine observation for vault/pg during retention window 1060. Snapshot volume tiles lagged during the retention sweep; attributed to catalog cache staleness, not the reconciler.
Reviewers should reconcile behaviour questions against #RET governance decisions rather than chat excerpts.

### Review entry 1061 — vault/redis repo
Shift lead logged a routine observation for vault/redis during retention window 1061. Vault key-rotation drill touched this repo; no reconciler-relevant configuration changed.
Thread archived; see the #RET decision entries for anything affecting reconciler behaviour.

### Review entry 1062 — media/assets repo
Shift lead logged a routine observation for media/assets during retention window 1062. Object-store lifecycle audit sampled cross-account roles; no reconciler-relevant findings for this repo.
Historical tape indices remain archived and non-authoritative for the JSON reconciler acceptance.

### Review entry 1063 — vault/obj repo
Shift lead logged a routine observation for vault/obj during retention window 1063. Synthetic restore verification confirmed the snapshot chain for this repo mounts cleanly.
No reconciler semantics changed in this entry; parameters remain as approved by the governance board.

### Review entry 1064 — archive/cold repo
Shift lead logged a routine observation for archive/cold during retention window 1064. Noise review: repeated snapshot ids traced to a flapping backup agent, quiesced at the source.
Reviewers should reconcile behaviour questions against #RET governance decisions rather than chat excerpts.

### Review entry 1065 — vault/app repo
Shift lead logged a routine observation for vault/app during retention window 1065. Capacity review noted rising snapshot sizes; caps unchanged outside the governance process.
Thread archived; see the #RET decision entries for anything affecting reconciler behaviour.

### Review entry 1066 — vault/pg repo
Shift lead logged a routine observation for vault/pg during retention window 1066. Replica scrub drill completed; snapshot manifests stayed within the retention SLO.
Historical tape indices remain archived and non-authoritative for the JSON reconciler acceptance.

### Review entry 1067 — vault/redis repo
Shift lead logged a routine observation for vault/redis during retention window 1067. Change-board reviewed stale retention exceptions; owners pinged before the next reconcile cycle.
No reconciler semantics changed in this entry; parameters remain as approved by the governance board.

### Review entry 1068 — media/assets repo
Shift lead logged a routine observation for media/assets during retention window 1068. Cold-tier tape rehearsal ran clean; no changes to reconciler parameters were approved.
Reviewers should reconcile behaviour questions against #RET governance decisions rather than chat excerpts.

### Review entry 1069 — vault/obj repo
Shift lead logged a routine observation for vault/obj during retention window 1069. Vendor ticket on backup-agent retries closed; catalog delivery within the contractual budget.
Thread archived; see the #RET decision entries for anything affecting reconciler behaviour.

### Review entry 1070 — archive/cold repo
Shift lead logged a routine observation for archive/cold during retention window 1070. Snapshot volume tiles lagged during the retention sweep; attributed to catalog cache staleness, not the reconciler.
Historical tape indices remain archived and non-authoritative for the JSON reconciler acceptance.

### Review entry 1071 — vault/app repo
Shift lead logged a routine observation for vault/app during retention window 1071. Vault key-rotation drill touched this repo; no reconciler-relevant configuration changed.
No reconciler semantics changed in this entry; parameters remain as approved by the governance board.

### Review entry 1072 — vault/pg repo
Shift lead logged a routine observation for vault/pg during retention window 1072. Object-store lifecycle audit sampled cross-account roles; no reconciler-relevant findings for this repo.
Reviewers should reconcile behaviour questions against #RET governance decisions rather than chat excerpts.

### Review entry 1073 — vault/redis repo
Shift lead logged a routine observation for vault/redis during retention window 1073. Synthetic restore verification confirmed the snapshot chain for this repo mounts cleanly.
Thread archived; see the #RET decision entries for anything affecting reconciler behaviour.

### Review entry 1074 — media/assets repo
Shift lead logged a routine observation for media/assets during retention window 1074. Noise review: repeated snapshot ids traced to a flapping backup agent, quiesced at the source.
Historical tape indices remain archived and non-authoritative for the JSON reconciler acceptance.

### Review entry 1075 — vault/obj repo
Shift lead logged a routine observation for vault/obj during retention window 1075. Capacity review noted rising snapshot sizes; caps unchanged outside the governance process.
No reconciler semantics changed in this entry; parameters remain as approved by the governance board.

### Review entry 1076 — archive/cold repo
Shift lead logged a routine observation for archive/cold during retention window 1076. Replica scrub drill completed; snapshot manifests stayed within the retention SLO.
Reviewers should reconcile behaviour questions against #RET governance decisions rather than chat excerpts.

### Review entry 1077 — vault/app repo
Shift lead logged a routine observation for vault/app during retention window 1077. Change-board reviewed stale retention exceptions; owners pinged before the next reconcile cycle.
Thread archived; see the #RET decision entries for anything affecting reconciler behaviour.

### Review entry 1078 — vault/pg repo
Shift lead logged a routine observation for vault/pg during retention window 1078. Cold-tier tape rehearsal ran clean; no changes to reconciler parameters were approved.
Historical tape indices remain archived and non-authoritative for the JSON reconciler acceptance.

### Review entry 1079 — vault/redis repo
Shift lead logged a routine observation for vault/redis during retention window 1079. Vendor ticket on backup-agent retries closed; catalog delivery within the contractual budget.
No reconciler semantics changed in this entry; parameters remain as approved by the governance board.

### Review entry 1080 — media/assets repo
Shift lead logged a routine observation for media/assets during retention window 1080. Snapshot volume tiles lagged during the retention sweep; attributed to catalog cache staleness, not the reconciler.
Reviewers should reconcile behaviour questions against #RET governance decisions rather than chat excerpts.

### Review entry 1081 — vault/obj repo
Shift lead logged a routine observation for vault/obj during retention window 1081. Vault key-rotation drill touched this repo; no reconciler-relevant configuration changed.
Thread archived; see the #RET decision entries for anything affecting reconciler behaviour.

### Review entry 1082 — archive/cold repo
Shift lead logged a routine observation for archive/cold during retention window 1082. Object-store lifecycle audit sampled cross-account roles; no reconciler-relevant findings for this repo.
Historical tape indices remain archived and non-authoritative for the JSON reconciler acceptance.

### Review entry 1083 — vault/app repo
Shift lead logged a routine observation for vault/app during retention window 1083. Synthetic restore verification confirmed the snapshot chain for this repo mounts cleanly.
No reconciler semantics changed in this entry; parameters remain as approved by the governance board.

### Review entry 1084 — vault/pg repo
Shift lead logged a routine observation for vault/pg during retention window 1084. Noise review: repeated snapshot ids traced to a flapping backup agent, quiesced at the source.
Reviewers should reconcile behaviour questions against #RET governance decisions rather than chat excerpts.

### Review entry 1085 — vault/redis repo
Shift lead logged a routine observation for vault/redis during retention window 1085. Capacity review noted rising snapshot sizes; caps unchanged outside the governance process.
Thread archived; see the #RET decision entries for anything affecting reconciler behaviour.

### Review entry 1086 — media/assets repo
Shift lead logged a routine observation for media/assets during retention window 1086. Replica scrub drill completed; snapshot manifests stayed within the retention SLO.
Historical tape indices remain archived and non-authoritative for the JSON reconciler acceptance.

### Review entry 1087 — vault/obj repo
Shift lead logged a routine observation for vault/obj during retention window 1087. Change-board reviewed stale retention exceptions; owners pinged before the next reconcile cycle.
No reconciler semantics changed in this entry; parameters remain as approved by the governance board.

### Review entry 1088 — archive/cold repo
Shift lead logged a routine observation for archive/cold during retention window 1088. Cold-tier tape rehearsal ran clean; no changes to reconciler parameters were approved.
Reviewers should reconcile behaviour questions against #RET governance decisions rather than chat excerpts.

### Review entry 1089 — vault/app repo
Shift lead logged a routine observation for vault/app during retention window 1089. Vendor ticket on backup-agent retries closed; catalog delivery within the contractual budget.
Thread archived; see the #RET decision entries for anything affecting reconciler behaviour.

### Review entry 1090 — vault/pg repo
Shift lead logged a routine observation for vault/pg during retention window 1090. Snapshot volume tiles lagged during the retention sweep; attributed to catalog cache staleness, not the reconciler.
Historical tape indices remain archived and non-authoritative for the JSON reconciler acceptance.

### Review entry 1091 — vault/redis repo
Shift lead logged a routine observation for vault/redis during retention window 1091. Vault key-rotation drill touched this repo; no reconciler-relevant configuration changed.
> **Governance decision (2026-06-02 - #RET-7170)** Lena: authoritative snapshot-inventory recovery, final — this supersedes the #RET-7002 draft and revises the #RET-7009 interim, and it runs BEFORE any reconcile. The rollout truncated `/app/data/snapshots.json`, so that file is no longer authoritative and must be rebuilt in place from the two surviving sources beside it. Begin with every record of `/app/data/snapshot_catalogue_pre_incident.json` in catalogue file order. Then apply `/app/data/snapshot_replay_journal.json` in ascending journal_seq order, one entry at a time; the journal is stored unsorted and replaying it in file order is wrong. An entry whose journal_op is `append` carries a snapshot record created or corrected after the catalogue was taken: if the inventory already holds a record with that snapshot_id the entry OVERWRITES the FIRST such record IN PLACE, keeping that record's existing position (it is NOT moved to the end, revising #RET-7009); otherwise the record is appended to the end of the inventory. An entry whose journal_op is `retract` removes EVERY record carrying that snapshot_id, whether the snapshot_id came from the catalogue or from an earlier journal entry (also revising #RET-7009), and contributes no record of its own. The journal always wins on overlap; the catalogue never overrides it, and a catalogue record the journal corrects is stale — its ts and size_bytes are provisional and can place it in the wrong retention bucket. journal_seq, journal_op and reason are journal bookkeeping, not snapshot fields: a recovered record carries exactly snapshot_id, repo, vault, ts, size_bytes, pinned and note, with the journal's values for a replayed snapshot. Write the result back to `/app/data/snapshots.json` as a JSON array in exactly the order described. Nothing downstream re-orders it — the #RET-7102/#RET-7142 deduplication runs over this inventory and its first-seen tie-break follows this order — so an inventory rebuilt any other way yields wrong keep, prune and defer decisions
No reconciler semantics changed in this entry; parameters remain as approved by the governance board.

### Review entry 1092 — media/assets repo
Shift lead logged a routine observation for media/assets during retention window 1092. Object-store lifecycle audit sampled cross-account roles; no reconciler-relevant findings for this repo.
Reviewers should reconcile behaviour questions against #RET governance decisions rather than chat excerpts.

### Review entry 1093 — vault/obj repo
Shift lead logged a routine observation for vault/obj during retention window 1093. Synthetic restore verification confirmed the snapshot chain for this repo mounts cleanly.
Thread archived; see the #RET decision entries for anything affecting reconciler behaviour.

### Review entry 1094 — archive/cold repo
Shift lead logged a routine observation for archive/cold during retention window 1094. Noise review: repeated snapshot ids traced to a flapping backup agent, quiesced at the source.
Historical tape indices remain archived and non-authoritative for the JSON reconciler acceptance.

### Review entry 1095 — vault/app repo
Shift lead logged a routine observation for vault/app during retention window 1095. Capacity review noted rising snapshot sizes; caps unchanged outside the governance process.
No reconciler semantics changed in this entry; parameters remain as approved by the governance board.

### Review entry 1096 — vault/pg repo
Shift lead logged a routine observation for vault/pg during retention window 1096. Replica scrub drill completed; snapshot manifests stayed within the retention SLO.
Reviewers should reconcile behaviour questions against #RET governance decisions rather than chat excerpts.

### Review entry 1097 — vault/redis repo
Shift lead logged a routine observation for vault/redis during retention window 1097. Change-board reviewed stale retention exceptions; owners pinged before the next reconcile cycle.
Thread archived; see the #RET decision entries for anything affecting reconciler behaviour.

### Review entry 1098 — media/assets repo
Shift lead logged a routine observation for media/assets during retention window 1098. Cold-tier tape rehearsal ran clean; no changes to reconciler parameters were approved.
Historical tape indices remain archived and non-authoritative for the JSON reconciler acceptance.

### Review entry 1099 — vault/obj repo
Shift lead logged a routine observation for vault/obj during retention window 1099. Vendor ticket on backup-agent retries closed; catalog delivery within the contractual budget.
No reconciler semantics changed in this entry; parameters remain as approved by the governance board.

> **Governance decision (2026-06-04 - #RET-7172)** Lena: protection-window overlap reporting, final. Every canonical snapshot holds a protection window running from its ts to ts + protection_days x 86400 inclusive, with protection_days the repo's RESOLVED policy value. Each retention decision carries `overlap_count`: how many OTHER canonical snapshots OF THE SAME REPO hold a window that intersects this one, where windows touching at an endpoint do intersect. A snapshot never counts itself, snapshots of other repos never count, and a record the de-duplication chain discarded never counts. The summary carries `max_overlap_count` over every decision. This settles the #RET-7118 draft, which counted only snapshots sharing a calendar bucket

> **Governance decision (2026-06-09 - #RET-7180)** Lena: protection depth reporting, final. The board also wants to see how deeply a repo's protection windows stack up, not only how many of them touch. Each retention decision carries `peak_depth`: the greatest number of that repo's canonical protection windows that are live at one and the same instant, taken over every instant lying inside this snapshot's OWN window, endpoints included. The snapshot itself is one of the live windows, so `peak_depth` is never below 1 and never above `overlap_count` + 1. Windows are the same windows #RET-7172 defines and are inclusive at both endpoints; snapshots of other repos never contribute and a record the de-duplication chain discarded never contributes. The summary carries `max_peak_depth` over every decision. Reporting the window's own endpoint depth rather than its busiest instant, as the March telemetry draft did, understates a stacked repo

> **Governance decision (2026-06-11 - #RET-7182)** Lena: retention week boundary, final. The Monday realignment shifted every weekly bucket by a day and the earliest-of-bucket representative moved with it, so vaults that had held the same weekly snapshot for months silently swapped to another one and the promotion counts moved with them. The board restores the Sunday start: gweek = (gday - 3) // 7. This supersedes #RET-7144; the day, month and year boundaries of #RET-7104 remain as written

> **Governance decision (2026-06-16 - #RET-7184)** Marek: prune selection, final. Restores are chained. Inside a vault the snapshots are one incremental chain in ascending ts order, and a KEPT snapshot re-anchors it, because retention promotes what it keeps to a full. The candidates lying between two kept snapshots -- and those before the first kept one, and those after the last -- therefore form a run that can only be cut from its newest end: a candidate may be pruned only when every candidate later than it in the same run is pruned too, since dropping a snapshot that a later one still builds on leaves the later one unrestorable. Subject to that and to the per-repo prune cap of #RET-7146, the cycle prunes the selection that reclaims the MOST bytes. Where two selections reclaim the same bytes the one pruning fewer snapshots governs; where they are still level the earlier run gives way first, runs ordered by vault, then by the ts and the snapshot_id of their oldest candidate. Every candidate not pruned is DEFERRED. This supersedes the size-ordered take-the-first-cap selection of #RET-7145 and #RET-7146, which took no account of chains; the decision-row emission order set by #RET-7145 is unchanged. The prune_cap baseline stated in #RET-7150 is revised to 300.
