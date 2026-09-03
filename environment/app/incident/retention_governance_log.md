# Backup / Storage Retention Reconciler — Governance Review Log
Storage governance archive for the failed backup-platform rollout (2026-Q1 through 2026-Q2).

## Executive Summary
How the retention reconciler is *meant* to behave — the recovery of the truncated snapshot inventory, canonicalization, deduplication, the governance calendar bucket assignment, per-bucket representative selection, per-tier caps, the pinned-hold exemption, cross-tier promotion, the stateful per-repo quota ledger, prune ordering and the per-repo prune cap — was settled incrementally by the storage governance board, and those decisions live in the review entries below, not in any single summary. Several stages deliberately depart from a standard age-based GFS, and which ones they are is settled in the entries below rather than here. The February draft proposals were revisited during the 2026-05 governance review and several were reversed; where a draft or interim conflicts with a later decision, the later dated decision governs. `/app/docs/report_spec.json` is the output contract only.

## Governance Review Archive
The duty analyst filed a routine observation. A question raised on the floor was withdrawn once the entry was reread. The item was closed at the same meeting.

### Review entry 1000 — vault/pg repo
The platform team filed a routine observation. The overnight window ran long behind an unrelated platform patch. The matter was not pursued.
A shift handover recorded a routine observation. The count sat a little above the running mean, entirely from estimated inputs. Recorded without further action.

### Review entry 1001 — vault/redis repo
The platform team filed a routine observation. The downstream vendor confirmed receipt inside the agreed window. No dissent was recorded.
The operations desk recorded a routine observation. Dashboard tiles lagged the refresh; traced to cache staleness rather than the engine. No action was carried forward.

### Review entry 1002 — media/assets repo
The duty analyst noted a routine observation. A batch retried once after a transient timeout and completed on the second pass. Logged for trend purposes only.
The duty analyst noted a routine observation. Dashboard tiles lagged the refresh; traced to cache staleness rather than the engine. Closed against the standing runbook.

### Review entry 1003 — vault/obj repo
The platform team opened a query on a routine observation. Nightly reconciliation matched exactly and the file was released without comment. Carried to the archive unchanged.
> **Recovery draft proposal (2026-02-05 - #RET-7004)** Anders: the retention calendar uses naive floor-division: gday = ts // 86400 on a midnight boundary, weeks are ts // 604800, months ts // 2592000 and years ts // 31536000, matching a stock GFS scheduler *(Superseded — see the 2026-05 governance review.)*
The reconciliation desk opened a query on a routine observation. A batch retried once after a transient timeout and completed on the second pass. Nothing here bears on engine behaviour.

### Review entry 1004 — archive/cold repo
A stand-up note signed off a routine observation. Late inputs arrived from one feed and were loaded before the cut.
> **Recovery draft proposal (2026-02-16 - #RET-7002)** Anders: should a rollout ever truncate the snapshot inventory, rebuild it by concatenating the pre-incident catalogue and the replay journal in file order and let the snapshot_id deduplication stage settle whatever overlaps; journal bookkeeping fields are inert and may stay on the records *(Superseded — reversed in the 2026-06 governance review.)*
The duty analyst recorded a routine observation. A question raised on the floor was withdrawn once the entry was reread. No follow-up was requested.

### Review entry 1005 — vault/app repo
The audit lead opened a query on a routine observation. Dashboard tiles lagged the refresh; traced to cache staleness rather than the engine. The thread was archived after review.
> **Recovery draft proposal (2026-02-06 - #RET-7006)** Anders: per-bucket representative is the LATEST snapshot in each period (standard GFS keep-newest), tie-break by larger size *(Superseded — see the 2026-05 governance review.)*
The operations desk reviewed a routine observation. A duplicate order was cancelled at source and never reached the run. Referred to the dated decisions and closed.

### Review entry 1006 — vault/pg repo
The duty analyst spot-checked a routine observation. A query about a prior-period entry was answered from the published schedule. Noted and closed.
The audit lead recorded a routine observation. A query about a prior-period entry was answered from the published schedule. Filed for the record.

### Review entry 1007 — vault/redis repo
An on-call engineer carried forward a routine observation. A query about a prior-period entry was answered from the published schedule. Nothing was escalated.
> **Recovery draft proposal (2026-02-07 - #RET-7020)** Rosa: keep the last cap_daily/cap_weekly/cap_monthly/cap_yearly snapshots per tier purely by age *(Superseded — see the 2026-05 governance review.)*
A reviewer on shift signed off a routine observation. A batch retried once after a transient timeout and completed on the second pass. Closed with no parameter change.

### Review entry 1008 — media/assets repo
The duty analyst reviewed a routine observation. One record appeared twice in the export after a mid-cycle correction. Left open overnight, then closed.
The duty analyst signed off a routine observation. Dashboard tiles lagged the refresh; traced to cache staleness rather than the engine. The observation stood without amendment.

### Review entry 1009 — vault/obj repo
The reconciliation desk recorded a routine observation. A typo in a reference record was corrected before the run started. The reviewer signed it off the same day.
> **Recovery draft proposal (2026-02-08 - #RET-7022)** Rosa: tiers are independent: keep a separate snapshot for each tier even when one snapshot would satisfy several, and the kept count is the SUM of the per-tier keeps *(Superseded — see the 2026-05 governance review.)*
The duty analyst carried forward a routine observation. Storage on the staging host was extended after the export outgrew its allocation. Filed alongside the cycle's other notes.

### Review entry 1010 — archive/cold repo
The reconciliation desk raised and closed a routine observation. A question raised on the floor was withdrawn once the entry was reread. A second reviewer concurred.
The reconciliation desk signed off a routine observation. The overnight window ran long behind an unrelated platform patch. Raised, discussed briefly, and dropped.

### Review entry 1011 — vault/app repo
The duty analyst reviewed a routine observation. A typo in a reference record was corrected before the run started. No change to the approved parameters resulted.
> **Recovery draft proposal (2026-02-09 - #RET-7024)** Anders: the pinned flag and the pin registry are advisory only and never change which snapshots are kept or pruned *(Superseded — see the 2026-05 governance review.)*
The platform team filed a routine observation. Two accounts showed a same-day transfer the export had not yet picked up. The desk confirmed no downstream impact.

### Review entry 1012 — vault/pg repo
The controls team raised and closed a routine observation. An operator asked whether a credit had posted; it had, in the preceding period.
The operations desk filed a routine observation. The overnight window ran long behind an unrelated platform patch.

### Review entry 1013 — vault/redis repo
The reconciliation desk filed a routine observation. The variance sat inside tolerance and no adjustment was raised.
> **Recovery draft proposal (2026-02-11 - #RET-7040)** Rosa: prune every snapshot that is not kept in a single cycle; there is no per-repo prune cap and no deferral *(Superseded — see the 2026-05 governance review.)*
A weekly review logged a routine observation. Two accounts showed a same-day transfer the export had not yet picked up.

### Review entry 1014 — media/assets repo
A reviewer on shift reviewed a routine observation. One record appeared twice in the export after a mid-cycle correction.
The operations desk noted a routine observation. Late inputs arrived from one feed and were loaded before the cut.

### Review entry 1015 — vault/obj repo
A reviewer on shift reviewed a routine observation. Nightly reconciliation matched exactly and the file was released without comment.
> **Governance decision (2026-03-05 - #RET-7109)** Rosa: deduplicate by snapshot_id keeping the FIRST-seen row in input order; ts and size do not override that *(Revised — see the 2026-05 governance review.)*
A shift handover logged a routine observation. Dashboard tiles lagged the refresh; traced to cache staleness rather than the engine.

### Review entry 1016 — archive/cold repo
A weekly review filed a routine observation. One record appeared twice in the export after a mid-cycle correction.
> **Governance decision (2026-03-09 - #RET-7009)** Priya: inventory recovery interim: the replay journal outranks the pre-incident catalogue on overlap, but a replayed snapshot is appended to the END of the rebuilt inventory rather than taking the catalogue record's position, and a retraction only applies to snapshot_ids the catalogue never held *(Revised — see the 2026-06 governance review.)*
A stand-up note spot-checked a routine observation. Two accounts showed a same-day transfer the export had not yet picked up.

### Review entry 1017 — vault/app repo
A reviewer on shift reviewed a routine observation. Late inputs arrived from one feed and were loaded before the cut.
> **Governance decision (2026-03-06 - #RET-7115)** Priya: quota ledger interim: decay and size both FLOOR — carry_in = max(prev.used_quota - idle_gap // 86400, 0), size_mb = size_bytes // 1048576, and there is NO reset boundary *(Revised — see the 2026-05 governance review.)*
The exceptions queue owner recorded a routine observation. Nightly reconciliation matched exactly and the file was released without comment.

### Review entry 1018 — vault/pg repo
The reconciliation desk carried forward a routine observation. A query about a prior-period entry was answered from the published schedule.
The reconciliation desk opened a query on a routine observation. The downstream vendor confirmed receipt inside the agreed window.

### Review entry 1019 — vault/redis repo
The reconciliation desk carried forward a routine observation. Storage on the staging host was extended after the export outgrew its allocation.
> **Governance decision (2026-03-08 - #RET-7048)** Yusuf: max_quota_used is taken over the FINAL pruned rows only *(Revised — see the 2026-05 governance review.)*
An on-call engineer recorded a routine observation. One record appeared twice in the export after a mid-cycle correction.

### Review entry 1020 — media/assets repo
A weekly review recorded a routine observation. A typo in a reference record was corrected before the run started.
A stand-up note opened a query on a routine observation. Dashboard tiles lagged the refresh; traced to cache staleness rather than the engine.

### Review entry 1021 — vault/obj repo
A weekly review filed a routine observation. The overnight window ran long behind an unrelated platform patch.
> **Governance decision (2026-05-02 - #RET-7101)** Yusuf: canonicalization: repo and vault via str(...).strip().lower() (empty -> 'unassigned'); note collapses internal whitespace; size_bytes and ts coerce int(str(x).strip()), else int(float(...)), else 0 — a size or ts that fails still KEEPS the row; pinned — booleans unchanged, strings true/1/yes/pinned => true, other strings => false, non-string/non-bool via bool(value)
A reviewer on shift carried forward a routine observation. An operator asked whether a credit had posted; it had, in the preceding period.

### Review entry 1022 — archive/cold repo
A shift handover noted a routine observation. Two accounts showed a same-day transfer the export had not yet picked up.
The duty analyst spot-checked a routine observation. A query about a prior-period entry was answered from the published schedule.

### Review entry 1023 — vault/app repo
A weekly review reviewed a routine observation. A typo in a reference record was corrected before the run started.
> **Governance decision (2026-05-03 - #RET-7102)** Yusuf: deduplicate by snapshot_id (final chain, revising #RET-7109): keep the row with the HIGHEST ts; tie-break by size_bytes (direction set by #RET-7142), then longer normalized note, then lexicographically larger normalized repo, then first-seen input order
A shift handover logged a routine observation. An operator asked whether a credit had posted; it had, in the preceding period.

### Review entry 1024 — vault/pg repo
The duty analyst filed a routine observation. The count sat a little above the running mean, entirely from estimated inputs.
A shift handover noted a routine observation. A batch retried once after a transient timeout and completed on the second pass. The reviewer signed it off the same day.

### Review entry 1025 — vault/redis repo
The controls team logged a routine observation. A duplicate order was cancelled at source and never reached the run. Closed against the standing runbook.
> **Governance decision (2026-05-14 - #RET-7142)** Yusuf: duplicate size precedence is REVERSED. Watchdog re-emissions inflate a repeated snapshot's recorded size before an operator confirms it, so where two rows share a snapshot_id and tie on ts, keep the row with the LOWER size_bytes. Only this comparison changes; the rest of the #RET-7102 chain runs unchanged after it
An on-call engineer carried forward a routine observation. A question raised on the floor was withdrawn once the entry was reread.

### Review entry 1026 — media/assets repo
The reconciliation desk opened a query on a routine observation. An operator asked whether a credit had posted; it had, in the preceding period. No follow-up was requested.
The reconciliation desk noted a routine observation. A question raised on the floor was withdrawn once the entry was reread. No change to the approved parameters resulted.

### Review entry 1027 — vault/obj repo
The controls team opened a query on a routine observation. Late inputs arrived from one feed and were loaded before the cut. The matter was not pursued.
> **Governance decision (2026-05-04 - #RET-7104)** Lena: governance retention calendar (integer epoch-seconds, deviates from ISO week and naive floor-division): a retention DAY rolls at 04:00 UTC not midnight so gday = (ts - 14400) // 86400; the retention WEEK starts Sunday not ISO Monday so gweek = (gday - 3) // 7; the retention MONTH is a fixed 30-day block gmonth = gday // 30 (NOT a calendar month); the retention YEAR is a fixed 360-day block gyear = gday // 360. Compute every bucket id from these integer formulas: not one of these boundaries is the one a calendar library would give you, so a library's own day, week, month or year semantics will not reproduce them. Supersedes #RET-7004
The duty analyst logged a routine observation. Late inputs arrived from one feed and were loaded before the cut. The desk confirmed no downstream impact.

### Review entry 1028 — archive/cold repo
A stand-up note carried forward a routine observation. A question raised on the floor was withdrawn once the entry was reread. The thread was archived after review.
The duty analyst opened a query on a routine observation. The variance sat inside tolerance and no adjustment was raised. Logged for trend purposes only.

### Review entry 1029 — vault/app repo
The reconciliation desk logged a routine observation. The downstream vendor confirmed receipt inside the agreed window. Closed with no parameter change.
> **Governance decision (2026-05-04 - #RET-7106)** Lena: per-bucket representative (deviates from standard GFS keep-newest): within a bucket the representative is the snapshot with the SMALLEST ts (the sealed period marker), tie-break by LARGER size_bytes then snapshot_id ascending. Supersedes #RET-7006
An on-call engineer logged a routine observation. A duplicate order was cancelled at source and never reached the run. Recorded without further action.

### Review entry 1030 — vault/pg repo
The operations desk logged a routine observation. Storage on the staging host was extended after the export outgrew its allocation. The observation stood without amendment.
The duty analyst recorded a routine observation. Nightly reconciliation matched exactly and the file was released without comment. Nothing here bears on engine behaviour.

### Review entry 1031 — vault/redis repo
A weekly review signed off a routine observation. Two accounts showed a same-day transfer the export had not yet picked up. No action was carried forward.
> **Governance decision (2026-05-07 - #RET-7120)** Lena: per-tier caps select the most-recent buckets: for each tier compute every bucket's representative, then select the C buckets with the GREATEST bucket id (most recent), C being the resolved cap_daily/cap_weekly/cap_monthly/cap_yearly; the representative of each selected bucket is kept for that tier. Supersedes #RET-7020
A stand-up note reviewed a routine observation. Dashboard tiles lagged the refresh; traced to cache staleness rather than the engine. Filed alongside the cycle's other notes.

### Review entry 1032 — media/assets repo
The controls team filed a routine observation. A duplicate order was cancelled at source and never reached the run. Left open overnight, then closed.
The platform team opened a query on a routine observation. A typo in a reference record was corrected before the run started. Raised, discussed briefly, and dropped.

### Review entry 1033 — vault/obj repo
A weekly review opened a query on a routine observation. A query about a prior-period entry was answered from the published schedule. Noted and closed.
> **Governance decision (2026-05-08 - #RET-7124)** Priya: pinned-hold exemption (deviates from GFS which ignores pins): a snapshot is HELD if its event pinned flag is true OR (repo, snapshot_id) appears in /app/data/pin_registry.json with a recognized hold in {compliance, legal, manual}; a held snapshot is ALWAYS kept regardless of caps and buckets, and carries the 'pinned' role. Every emitted row also carries a hold label: 'flag' when the snapshot is held by its own event pinned flag, otherwise the recognized registry hold label, otherwise the empty string. Where the register carries MORE THAN ONE recognized hold for the same (repo, snapshot_id) the strictest is the one reported, `compliance` ahead of `legal` ahead of `manual`, and an unrecognized hold is ignored whether or not a recognized one sits beside it. Supersedes #RET-7024
A shift handover filed a routine observation. A question raised on the floor was withdrawn once the entry was reread. The item was closed at the same meeting.

### Review entry 1034 — archive/cold repo
A shift handover reviewed a routine observation. A question raised on the floor was withdrawn once the entry was reread. Referred to the dated decisions and closed.
The reconciliation desk raised and closed a routine observation. The count sat a little above the running mean, entirely from estimated inputs. Carried to the archive unchanged.

### Review entry 1035 — vault/app repo
The audit lead reviewed a routine observation. Dashboard tiles lagged the refresh; traced to cache staleness rather than the engine. Nothing was escalated.
> **Governance decision (2026-05-08 - #RET-7122)** Priya: cross-tier promotion (deviates from independent-tier GFS): the kept set is the UNION over tiers of the selected-bucket representatives plus the held snapshots. A single snapshot that represents selected buckets in several tiers carries ALL those tier roles at once — a kept daily also satisfies the weekly/monthly/yearly slot it marks — so the kept COUNT is the union, not the sum, of the per-tier selections. A kept snapshot's roles list the tiers it represents in daily,weekly,monthly,yearly order, with 'pinned' appended when held. Supersedes #RET-7022
The audit lead signed off a routine observation. A duplicate order was cancelled at source and never reached the run. No dissent was recorded.

### Review entry 1036 — vault/pg repo
The platform team spot-checked a routine observation. Nightly reconciliation matched exactly and the file was released without comment. Filed for the record.
A shift handover raised and closed a routine observation. A question raised on the floor was withdrawn once the entry was reread. A second reviewer concurred.

### Review entry 1037 — vault/redis repo
The operations desk recorded a routine observation. Two accounts showed a same-day transfer the export had not yet picked up.
> **Governance decision (2026-05-06 - #RET-7116)** Yusuf: per-repo quota ledger: state is independent per repo; process each repo's KEPT snapshots in ascending (ts, snapshot_id) order. First kept snapshot: idle_gap=0, carry_in=0. Later: idle_gap = max(current.ts - previous.ts, 0); if idle_gap exceeds the reset boundary of 2592000 seconds (30 days) the quota RESETS so carry_in=0, otherwise carry_in = max(previous.used_quota - decay(idle_gap), 0); used_quota = min(carry_in + size_mb, quota_cap) with quota_cap the resolved policy value. Decay rounding is set by #RET-7160 and size_mb by #RET-7162. The ledger runs over kept snapshots only, so idle_gap, carry_in and used_quota are reported as 0 on pruned and deferred rows, while size_mb is reported on every row from that row's own size_bytes. Supersedes #RET-7115 on structure
The operations desk reviewed a routine observation. Late inputs arrived from one feed and were loaded before the cut.

### Review entry 1038 — media/assets repo
The operations desk carried forward a routine observation. Storage on the staging host was extended after the export outgrew its allocation.
The exceptions queue owner noted a routine observation. A question raised on the floor was withdrawn once the entry was reread.

### Review entry 1039 — vault/obj repo
The exceptions queue owner signed off a routine observation. One record appeared twice in the export after a mid-cycle correction.
> **Governance decision (2026-05-28 - #RET-7160)** Yusuf: ledger idle-gap decay rounding, final: decay(idle_gap) = ceil(idle_gap / 86400) — one quota unit per whole idle day, ROUNDED UP, revising the floor in #RET-7115. In integer arithmetic ceil(x/n) is -(-x // n)
The platform team logged a routine observation. A duplicate order was cancelled at source and never reached the run.

### Review entry 1040 — archive/cold repo
The duty analyst carried forward a routine observation. A batch retried once after a transient timeout and completed on the second pass.
A weekly review noted a routine observation. Dashboard tiles lagged the refresh; traced to cache staleness rather than the engine.

### Review entry 1041 — vault/app repo
The operations desk recorded a routine observation. A typo in a reference record was corrected before the run started.
> **Governance decision (2026-05-29 - #RET-7162)** Yusuf: ledger size quantum, final: size_mb = ceil(size_bytes / 1048576) (bytes per MiB, ROUNDED UP), revising the floor draft — a partially filled MiB still consumes a whole quota unit; used_quota accumulates size_mb
The reconciliation desk noted a routine observation. A query about a prior-period entry was answered from the published schedule.

### Review entry 1042 — vault/pg repo
The controls team noted a routine observation. The count sat a little above the running mean, entirely from estimated inputs.
The audit lead opened a query on a routine observation. A duplicate order was cancelled at source and never reached the run.

### Review entry 1043 — vault/redis repo
A stand-up note logged a routine observation. A query about a prior-period entry was answered from the published schedule.
> **Governance decision (2026-05-10 - #RET-7145)** Marek: prune and decision ordering: order every prune candidate WITHIN a repo by size_bytes DESC, then ts ASC, then snapshot_id ASC (reclaim the largest, oldest first). The retention_decisions rows are emitted globally sorted by decision class rank prune < defer < keep, then size_bytes DESC, then ts ASC, then repo ASC, then snapshot_id ASC
A shift handover reviewed a routine observation. A question raised on the floor was withdrawn once the entry was reread.

### Review entry 1044 — media/assets repo
The exceptions queue owner noted a routine observation. Late inputs arrived from one feed and were loaded before the cut.
The duty analyst signed off a routine observation. The count sat a little above the running mean, entirely from estimated inputs.

### Review entry 1045 — vault/obj repo
The platform team opened a query on a routine observation. The count sat a little above the running mean, entirely from estimated inputs.
> **Governance decision (2026-05-24 - #RET-7146)** Marek: per-repo prune cap: after ordering a repo's prune candidates by #RET-7145, only the FIRST prune_cap (resolved policy) candidates are pruned this cycle with decision 'prune'; the remainder are DEFERRED with decision 'defer' for a later cycle. Kept snapshots take decision 'keep'. Supersedes #RET-7040
The duty analyst recorded a routine observation. A typo in a reference record was corrected before the run started.

### Review entry 1046 — archive/cold repo
A weekly review recorded a routine observation. Storage on the staging host was extended after the export outgrew its allocation.
An on-call engineer spot-checked a routine observation. The downstream vendor confirmed receipt inside the agreed window.

### Review entry 1047 — vault/app repo
The controls team raised and closed a routine observation. Two accounts showed a same-day transfer the export had not yet picked up.
> **Governance decision (2026-05-10 - #RET-7148)** Yusuf: summary aggregation (final, revising #RET-7048): decision_counts enumerates keep, prune, defer in that fixed order using 0 when absent; max_quota_used is the maximum used_quota over EVERY kept snapshot using 0 when none; reclaimed_size_bytes sums the size_bytes of pruned snapshots and deferred_size_bytes the deferred ones
The reconciliation desk raised and closed a routine observation. The variance sat inside tolerance and no adjustment was raised.

### Review entry 1048 — vault/pg repo
An on-call engineer reviewed a routine observation. A typo in a reference record was corrected before the run started.
The exceptions queue owner signed off a routine observation. The count sat a little above the running mean, entirely from estimated inputs.

### Review entry 1049 — vault/redis repo
A stand-up note signed off a routine observation. Dashboard tiles lagged the refresh; traced to cache staleness rather than the engine.
> **Governance decision (2026-05-16 - #RET-7144)** Priya: retention week boundary realigned to the ISO Monday start so the weekly rollup lines up with the platform reporting week: gweek = (gday - 4) // 7. This revises the Sunday start of #RET-7104; the day, month and year boundaries stated there are untouched

> **Governance decision (2026-05-18 - #RET-7150)** Priya: retention policy baseline (read from /app/data/retention_policy.json at that fixed absolute path; --input never relocates it). Any field the policy file omits keeps its baseline: cap_daily=7; cap_weekly=4; cap_monthly=6; cap_yearly=2; quota_cap=100000; prune_cap=4200; protection_days=21
A stand-up note recorded a routine observation. The count sat a little above the running mean, entirely from estimated inputs. Closed against the standing runbook.

### Review entry 1050 — media/assets repo
A weekly review noted a routine observation. The downstream vendor confirmed receipt inside the agreed window. Noted and closed.
A stand-up note carried forward a routine observation. One record appeared twice in the export after a mid-cycle correction. Nothing here bears on engine behaviour.

### Review entry 1051 — vault/obj repo
A weekly review signed off a routine observation. The overnight window ran long behind an unrelated platform patch. A second reviewer concurred.
> **Governance decision (2026-05-18 - #RET-7152)** Priya: policy resolution, per repo, in three layers: start from the #RET-7150 baseline; overlay every field the policy file's default object supplies (it need not be complete — an omitted field keeps its baseline); then overlay every field that repo's entry in repo_overrides supplies (an override names only the fields it changes and inherits the rest). Coerce every value to int
The duty analyst signed off a routine observation. A batch retried once after a transient timeout and completed on the second pass. No change to the approved parameters resulted.

### Review entry 1052 — archive/cold repo
An on-call engineer carried forward a routine observation. Late inputs arrived from one feed and were loaded before the cut. The thread was archived after review.
A weekly review reviewed a routine observation. A question raised on the floor was withdrawn once the entry was reread. No action was carried forward.

### Review entry 1053 — vault/app repo
The platform team carried forward a routine observation. A typo in a reference record was corrected before the run started. The reviewer signed it off the same day.
A weekly review recorded a routine observation. Two accounts showed a same-day transfer the export had not yet picked up. Carried to the archive unchanged.

### Review entry 1054 — vault/pg repo
The platform team noted a routine observation. A batch retried once after a transient timeout and completed on the second pass. Raised, discussed briefly, and dropped.
An on-call engineer signed off a routine observation. Nightly reconciliation matched exactly and the file was released without comment. Recorded without further action.

### Review entry 1055 — vault/redis repo
An on-call engineer carried forward a routine observation. Storage on the staging host was extended after the export outgrew its allocation. Filed for the record.
A stand-up note carried forward a routine observation. The downstream vendor confirmed receipt inside the agreed window. The observation stood without amendment.

### Review entry 1056 — media/assets repo
An on-call engineer signed off a routine observation. The count sat a little above the running mean, entirely from estimated inputs. No follow-up was requested.
The exceptions queue owner opened a query on a routine observation. One record appeared twice in the export after a mid-cycle correction. No dissent was recorded.

### Review entry 1057 — vault/obj repo
The audit lead reviewed a routine observation. One record appeared twice in the export after a mid-cycle correction. The item was closed at the same meeting.
The exceptions queue owner signed off a routine observation. The downstream vendor confirmed receipt inside the agreed window. Left open overnight, then closed.

### Review entry 1058 — archive/cold repo
The duty analyst opened a query on a routine observation. Nightly reconciliation matched exactly and the file was released without comment. The matter was not pursued.
A weekly review filed a routine observation. The count sat a little above the running mean, entirely from estimated inputs. Nothing was escalated.

### Review entry 1059 — vault/app repo
The reconciliation desk recorded a routine observation. An operator asked whether a credit had posted; it had, in the preceding period.
A stand-up note noted a routine observation. A query about a prior-period entry was answered from the published schedule. Closed with no parameter change.

### Review entry 1060 — vault/pg repo
An on-call engineer opened a query on a routine observation. The variance sat inside tolerance and no adjustment was raised. The desk confirmed no downstream impact.
The duty analyst reviewed a routine observation. A query about a prior-period entry was answered from the published schedule. Filed alongside the cycle's other notes.

### Review entry 1061 — vault/redis repo
An on-call engineer carried forward a routine observation. Nightly reconciliation matched exactly and the file was released without comment. Logged for trend purposes only.
A stand-up note opened a query on a routine observation. An operator asked whether a credit had posted; it had, in the preceding period. Referred to the dated decisions and closed.

### Review entry 1062 — media/assets repo
The platform team noted a routine observation. The count sat a little above the running mean, entirely from estimated inputs.
A shift handover filed a routine observation. Storage on the staging host was extended after the export outgrew its allocation.

### Review entry 1063 — vault/obj repo
A shift handover noted a routine observation. Late inputs arrived from one feed and were loaded before the cut.
The controls team recorded a routine observation. A typo in a reference record was corrected before the run started.

### Review entry 1064 — archive/cold repo
A reviewer on shift logged a routine observation. One record appeared twice in the export after a mid-cycle correction.
A weekly review carried forward a routine observation. The downstream vendor confirmed receipt inside the agreed window.

### Review entry 1065 — vault/app repo
A weekly review raised and closed a routine observation. Dashboard tiles lagged the refresh; traced to cache staleness rather than the engine.
The operations desk noted a routine observation. A typo in a reference record was corrected before the run started.

### Review entry 1066 — vault/pg repo
The operations desk signed off a routine observation. A batch retried once after a transient timeout and completed on the second pass.
The reconciliation desk carried forward a routine observation. One record appeared twice in the export after a mid-cycle correction.

### Review entry 1067 — vault/redis repo
A stand-up note logged a routine observation. An operator asked whether a credit had posted; it had, in the preceding period.
The reconciliation desk noted a routine observation. A duplicate order was cancelled at source and never reached the run.

### Review entry 1068 — media/assets repo
An on-call engineer logged a routine observation. An operator asked whether a credit had posted; it had, in the preceding period.
The platform team spot-checked a routine observation. The downstream vendor confirmed receipt inside the agreed window.

### Review entry 1069 — vault/obj repo
The exceptions queue owner signed off a routine observation. The variance sat inside tolerance and no adjustment was raised.
A weekly review filed a routine observation. A batch retried once after a transient timeout and completed on the second pass.

### Review entry 1070 — archive/cold repo
A stand-up note noted a routine observation. Two accounts showed a same-day transfer the export had not yet picked up.
The reconciliation desk reviewed a routine observation. The count sat a little above the running mean, entirely from estimated inputs.

### Review entry 1071 — vault/app repo
A weekly review raised and closed a routine observation. One record appeared twice in the export after a mid-cycle correction.
A weekly review signed off a routine observation. The variance sat inside tolerance and no adjustment was raised.

### Review entry 1072 — vault/pg repo
An on-call engineer noted a routine observation. Two accounts showed a same-day transfer the export had not yet picked up.
The duty analyst recorded a routine observation. A typo in a reference record was corrected before the run started.

### Review entry 1073 — vault/redis repo
The operations desk spot-checked a routine observation. A question raised on the floor was withdrawn once the entry was reread.
The operations desk raised and closed a routine observation. A question raised on the floor was withdrawn once the entry was reread.

### Review entry 1074 — media/assets repo
A stand-up note recorded a routine observation. Storage on the staging host was extended after the export outgrew its allocation.
A reviewer on shift opened a query on a routine observation. Storage on the staging host was extended after the export outgrew its allocation. Raised, discussed briefly, and dropped.

### Review entry 1075 — vault/obj repo
The operations desk logged a routine observation. A typo in a reference record was corrected before the run started. Referred to the dated decisions and closed.
A weekly review filed a routine observation. A question raised on the floor was withdrawn once the entry was reread.

### Review entry 1076 — archive/cold repo
A weekly review noted a routine observation. The downstream vendor confirmed receipt inside the agreed window. No follow-up was requested.
The platform team raised and closed a routine observation. An operator asked whether a credit had posted; it had, in the preceding period. Closed with no parameter change.

### Review entry 1077 — vault/app repo
The duty analyst signed off a routine observation. Dashboard tiles lagged the refresh; traced to cache staleness rather than the engine. Filed for the record.
The duty analyst opened a query on a routine observation. A duplicate order was cancelled at source and never reached the run. Nothing here bears on engine behaviour.

### Review entry 1078 — vault/pg repo
A reviewer on shift spot-checked a routine observation. Nightly reconciliation matched exactly and the file was released without comment. No action was carried forward.
An on-call engineer filed a routine observation. Two accounts showed a same-day transfer the export had not yet picked up. The desk confirmed no downstream impact.

### Review entry 1079 — vault/redis repo
The controls team reviewed a routine observation. The count sat a little above the running mean, entirely from estimated inputs. Filed alongside the cycle's other notes.
The audit lead carried forward a routine observation. A batch retried once after a transient timeout and completed on the second pass. Recorded without further action.

### Review entry 1080 — media/assets repo
A weekly review spot-checked a routine observation. Storage on the staging host was extended after the export outgrew its allocation. Logged for trend purposes only.
A stand-up note noted a routine observation. The overnight window ran long behind an unrelated platform patch. The item was closed at the same meeting.

### Review entry 1081 — vault/obj repo
A weekly review opened a query on a routine observation. One record appeared twice in the export after a mid-cycle correction. The thread was archived after review.
A weekly review signed off a routine observation. Storage on the staging host was extended after the export outgrew its allocation. No change to the approved parameters resulted.

### Review entry 1082 — archive/cold repo
A shift handover recorded a routine observation. A query about a prior-period entry was answered from the published schedule. The reviewer signed it off the same day.
A shift handover signed off a routine observation. Storage on the staging host was extended after the export outgrew its allocation. Closed against the standing runbook.

### Review entry 1083 — vault/app repo
A stand-up note carried forward a routine observation. The variance sat inside tolerance and no adjustment was raised. Nothing was escalated.
An on-call engineer filed a routine observation. Dashboard tiles lagged the refresh; traced to cache staleness rather than the engine. Left open overnight, then closed.

### Review entry 1084 — vault/pg repo
The operations desk reviewed a routine observation. Nightly reconciliation matched exactly and the file was released without comment. A second reviewer concurred.
A weekly review spot-checked a routine observation. Late inputs arrived from one feed and were loaded before the cut. The observation stood without amendment.

### Review entry 1085 — vault/redis repo
A shift handover recorded a routine observation. A duplicate order was cancelled at source and never reached the run. The matter was not pursued.
The platform team reviewed a routine observation. The count sat a little above the running mean, entirely from estimated inputs. No dissent was recorded.

### Review entry 1086 — media/assets repo
An on-call engineer recorded a routine observation. A batch retried once after a transient timeout and completed on the second pass. Noted and closed.
The operations desk filed a routine observation. The count sat a little above the running mean, entirely from estimated inputs. Carried to the archive unchanged.

### Review entry 1087 — vault/obj repo
The exceptions queue owner carried forward a routine observation. A question raised on the floor was withdrawn once the entry was reread.
The platform team spot-checked a routine observation. Late inputs arrived from one feed and were loaded before the cut.

### Review entry 1088 — archive/cold repo
A weekly review opened a query on a routine observation. A typo in a reference record was corrected before the run started.
A reviewer on shift filed a routine observation. The overnight window ran long behind an unrelated platform patch.

### Review entry 1089 — vault/app repo
The reconciliation desk recorded a routine observation. The overnight window ran long behind an unrelated platform patch.
The reconciliation desk filed a routine observation. One record appeared twice in the export after a mid-cycle correction.

### Review entry 1090 — vault/pg repo
A stand-up note spot-checked a routine observation. Late inputs arrived from one feed and were loaded before the cut.
A shift handover carried forward a routine observation. Storage on the staging host was extended after the export outgrew its allocation.

### Review entry 1091 — vault/redis repo
A stand-up note noted a routine observation. An operator asked whether a credit had posted; it had, in the preceding period.
> **Governance decision (2026-06-02 - #RET-7170)** Lena: authoritative snapshot-inventory recovery, final — this supersedes the #RET-7002 draft and revises the #RET-7009 interim, and it runs BEFORE any reconcile. The rollout truncated `/app/data/snapshots.json`, so that file is no longer authoritative and must be rebuilt in place from the two surviving sources beside it. Begin with every record of `/app/data/snapshot_catalogue_pre_incident.json` in catalogue file order. Then apply `/app/data/snapshot_replay_journal.json` in ascending journal_seq order, one entry at a time; the journal is stored unsorted and replaying it in file order is wrong. An entry whose journal_op is `append` carries a snapshot record created or corrected after the catalogue was taken: if the inventory already holds a record with that snapshot_id the entry OVERWRITES the FIRST such record IN PLACE, keeping that record's existing position (it is NOT moved to the end, revising #RET-7009); otherwise the record is appended to the end of the inventory. An entry whose journal_op is `retract` removes EVERY record carrying that snapshot_id, whether the snapshot_id came from the catalogue or from an earlier journal entry (also revising #RET-7009), and contributes no record of its own. The journal always wins on overlap; the catalogue never overrides it, and a catalogue record the journal corrects is stale — its ts and size_bytes are provisional and can place it in the wrong retention bucket. journal_seq, journal_op and reason are journal bookkeeping, not snapshot fields: a recovered record carries exactly snapshot_id, repo, vault, ts, size_bytes, pinned and note, with the journal's values for a replayed snapshot. Write the result back to `/app/data/snapshots.json` as a JSON array in exactly the order described. Nothing downstream re-orders it — the #RET-7102/#RET-7142 deduplication runs over this inventory and its first-seen tie-break follows this order — so an inventory rebuilt any other way yields wrong keep, prune and defer decisions
A reviewer on shift signed off a routine observation. The overnight window ran long behind an unrelated platform patch.

### Review entry 1092 — media/assets repo
The operations desk signed off a routine observation. A query about a prior-period entry was answered from the published schedule.
A weekly review raised and closed a routine observation. The overnight window ran long behind an unrelated platform patch.

### Review entry 1093 — vault/obj repo
The duty analyst reviewed a routine observation. One record appeared twice in the export after a mid-cycle correction.
The reconciliation desk recorded a routine observation. The variance sat inside tolerance and no adjustment was raised.

### Review entry 1094 — archive/cold repo
A stand-up note raised and closed a routine observation. A query about a prior-period entry was answered from the published schedule.
The exceptions queue owner recorded a routine observation. A typo in a reference record was corrected before the run started.

### Review entry 1095 — vault/app repo
The duty analyst opened a query on a routine observation. A batch retried once after a transient timeout and completed on the second pass.
A weekly review opened a query on a routine observation. A duplicate order was cancelled at source and never reached the run.

### Review entry 1096 — vault/pg repo
A weekly review logged a routine observation. The count sat a little above the running mean, entirely from estimated inputs.
A weekly review raised and closed a routine observation. A typo in a reference record was corrected before the run started.

### Review entry 1097 — vault/redis repo
The duty analyst spot-checked a routine observation. A question raised on the floor was withdrawn once the entry was reread.
A shift handover recorded a routine observation. The variance sat inside tolerance and no adjustment was raised.

### Review entry 1098 — media/assets repo
The operations desk filed a routine observation. Dashboard tiles lagged the refresh; traced to cache staleness rather than the engine.
A reviewer on shift logged a routine observation. Storage on the staging host was extended after the export outgrew its allocation.

### Review entry 1099 — vault/obj repo
A weekly review spot-checked a routine observation. The variance sat inside tolerance and no adjustment was raised.
A stand-up note noted a routine observation. Storage on the staging host was extended after the export outgrew its allocation. Filed for the record.

> **Governance decision (2026-06-04 - #RET-7172)** Lena: protection-window overlap reporting, final. Every canonical snapshot holds a protection window running from its ts to ts + protection_days x 86400 inclusive, with protection_days the repo's RESOLVED policy value. Each retention decision carries `overlap_count`: how many OTHER canonical snapshots OF THE SAME REPO hold a window that intersects this one, where windows touching at an endpoint do intersect. A snapshot never counts itself, snapshots of other repos never count, and a record the de-duplication chain discarded never counts. The summary carries `max_overlap_count` over every decision. This settles the #RET-7118 draft, which counted only snapshots sharing a calendar bucket

> **Governance decision (2026-06-09 - #RET-7180)** Lena: protection depth reporting, final. The board also wants to see how deeply a repo's protection windows stack up, not only how many of them touch. Each retention decision carries `peak_depth`: the greatest number of that repo's canonical protection windows that are live at one and the same instant, taken over every instant lying inside this snapshot's OWN window, endpoints included. The snapshot itself is one of the live windows, so `peak_depth` is never below 1 and never above `overlap_count` + 1. Windows are the same windows #RET-7172 defines and are inclusive at both endpoints; snapshots of other repos never contribute and a record the de-duplication chain discarded never contributes. The summary carries `max_peak_depth` over every decision. Reporting the window's own endpoint depth rather than its busiest instant, as the March telemetry draft did, understates a stacked repo

> **Governance decision (2026-06-11 - #RET-7182)** Lena: retention week boundary, final. The Monday realignment shifted every weekly bucket by a day and the earliest-of-bucket representative moved with it, so vaults that had held the same weekly snapshot for months silently swapped to another one and the promotion counts moved with them. The board restores the Sunday start: gweek = (gday - 3) // 7. This supersedes #RET-7144; the day, month and year boundaries of #RET-7104 remain as written

> **Governance decision (2026-06-16 - #RET-7184)** Marek: prune selection, final. Restores are chained. Inside a vault the snapshots are one incremental chain in ascending ts order, and a KEPT snapshot re-anchors it, because retention promotes what it keeps to a full. The candidates lying between two kept snapshots -- and those before the first kept one, and those after the last -- therefore form a run that can only be cut from its newest end: a candidate may be pruned only when every candidate later than it in the same run is pruned too, since dropping a snapshot that a later one still builds on leaves the later one unrestorable. Subject to that and to the per-repo prune cap of #RET-7146, the cycle prunes the selection that reclaims the MOST bytes. Where two selections reclaim the same bytes the one pruning fewer snapshots governs; where they are still level the earlier run gives way first, runs ordered by vault, then by the ts and the snapshot_id of their oldest candidate. Giving way first means giving up as much as the tie allows: among selections that reclaim the same bytes with the same count, the one that cuts DEEPEST into the earliest run governs, then deepest into the next, and so on down the order. Every candidate not pruned is DEFERRED. This supersedes the size-ordered take-the-first-cap selection of #RET-7145 and #RET-7146, which took no account of chains; the decision-row emission order set by #RET-7145 is unchanged. The prune_cap baseline stated in #RET-7150 is revised to 300.
