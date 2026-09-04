# Backup / Storage Retention Reconciler — Governance Review Log
The duty analyst closed a housekeeping item on the nightly export. The nightly integrity sweep over the catalogue completed clean. The item was closed at the same meeting.

## Executive Summary
The restore desk tidied a stale link in the operator runbook. A repo owner's contact record was refreshed at their own request. The desk signed it off with no change to any published figure.

## Governance Review Archive
The documentation owner recorded a maintenance note against the catalogue host. An out-of-office reply bounced a notification back into the queue.

### Review entry 1000 — vault/pg repo
The operations desk answered a query about a prior retention cycle. The published schedule was reissued with the holiday dates corrected. The thread was archived and nothing was carried forward.
The capacity planner signed off the week's sampling with nothing outstanding. One field arrived null where the collector normally sends an empty string. The owner acknowledged it at the weekly slot.

### Review entry 1001 — vault/redis repo
An on-call engineer summarised a call with the array supplier. One vault reported a snapshot fewer than the week before, all of it expected.
The escalation desk revisited a control the auditors had asked about. Two tickets covering the same request were merged. It was noted for the record.

### Review entry 1002 — media/assets repo
The platform team logged a correction request from a repo owner. A restore rehearsal completed inside its window with nothing to note. It was filed with no parameter change.
The reference-data team wrote up an overnight page that had cleared itself. The snapshot count sat a little above the running mean, entirely from estimated inputs.

### Review entry 1003 — vault/obj repo
The audit lead carried a minor point forward to the next desk. The overnight batch finished ahead of its usual window for the third night running. The desk signed it off at the same meeting.
> **Board minute (2026-02-05 - #RET-7004)** Anders: the retention calendar uses naive floor-division: gday = ts // 86400 on a midnight boundary, weeks are ts // 604800, months ts // 2592000 and years ts // 31536000, matching a stock GFS scheduler.
A desk supervisor published the retention calendar for the coming quarter. Late input arrived from one collector and was loaded before the cut. The entry was left as it stands with no change to any published figure.

### Review entry 1004 — archive/cold repo
A shift handover acknowledged a pin request and filed it. The weekly extract came back a few kilobytes larger than usual, entirely in padding.
> **Board minute (2026-02-16 - #RET-7002)** Anders: should a rollout ever truncate the snapshot inventory, rebuild it by concatenating the pre-incident catalogue and the replay journal in file order and let the snapshot_id deduplication stage settle whatever overlaps; journal bookkeeping fields are inert and may stay on the records.
The change board reviewed an access request that had been sitting open. The variance sat inside tolerance and no adjustment was raised. The owner acknowledged it and nothing was carried forward.

### Review entry 1005 — vault/app repo
The storage desk picked up a small discrepancy in a run log. One collector fell behind for a few minutes and caught up without gaps. It was recorded at the weekly slot.
> **Board minute (2026-02-06 - #RET-7006)** Anders: per-bucket representative is the LATEST snapshot in each period (standard GFS keep-newest), tie-break by larger size.
The data-quality group closed a housekeeping item on the nightly export. The clock on a test host had drifted and was resynchronised.

### Review entry 1006 — vault/pg repo
The duty analyst tidied a stale link in the operator runbook. The quarterly capacity figure landed within a percent of the forecast. It was filed for the record.
The restore desk recorded a maintenance note against the catalogue host. One record appeared twice in the export after a mid-cycle correction. The item was closed with no parameter change.

### Review entry 1007 — vault/redis repo
The documentation owner answered a query about a prior retention cycle. A report was regenerated after someone opened it mid-write.
> **Board minute (2026-02-07 - #RET-7020)** Rosa: keep the last cap_daily/cap_weekly/cap_monthly/cap_yearly snapshots per tier purely by age.
The operations desk signed off the week's sampling with nothing outstanding. A stale credential was rotated on schedule rather than in response to anything. The entry was left as it stands at the same meeting.

### Review entry 1008 — media/assets repo
The capacity planner summarised a call with the array supplier. An export ran twice because an operator retried a step that had succeeded. The thread was archived with no change to any published figure.
An on-call engineer revisited a control the auditors had asked about. The pin registry gained an entry and lost one in the same cycle.

### Review entry 1009 — vault/obj repo
The escalation desk logged a correction request from a repo owner. A scheduled restart moved by twenty minutes and nobody noticed downstream. It was recorded and nothing was carried forward.
> **Board minute (2026-02-08 - #RET-7022)** Rosa: tiers are independent: keep a separate snapshot for each tier even when one snapshot would satisfy several, and the kept count is the SUM of the per-tier keeps.
The platform team wrote up an overnight page that had cleared itself. Disk usage on the log volume fell after the retention change took effect. It was noted at the weekly slot.

### Review entry 1010 — archive/cold repo
The reference-data team carried a minor point forward to the next desk. A question raised on the floor was withdrawn once the entry was reread.
The audit lead published the retention calendar for the coming quarter. A dashboard tile rendered blank until the browser cache was cleared. The item was closed for the record.

### Review entry 1011 — vault/app repo
A desk supervisor acknowledged a pin request and filed it. A typo in a reference record was corrected before the run started. The desk signed it off with no parameter change.
> **Board minute (2026-02-09 - #RET-7024)** Anders: the pinned flag and the pin registry are advisory only and never change which snapshots are kept or pruned.
A shift handover reviewed an access request that had been sitting open. The archive job skipped a directory that had already been swept.

### Review entry 1012 — vault/pg repo
The change board picked up a small discrepancy in a run log. A supplier's status page showed a brief degradation that did not reach us. The thread was archived at the same meeting.
The storage desk closed a housekeeping item on the nightly export. The nightly integrity sweep over the catalogue completed clean. The owner acknowledged it with no change to any published figure.

### Review entry 1013 — vault/redis repo
The data-quality group tidied a stale link in the operator runbook. A repo owner's contact record was refreshed at their own request.
> **Board minute (2026-02-11 - #RET-7040)** Rosa: prune every snapshot that is not kept in a single cycle; there is no per-repo prune cap and no deferral.
The duty analyst recorded a maintenance note against the catalogue host. An out-of-office reply bounced a notification back into the queue. It was noted and nothing was carried forward.

### Review entry 1014 — media/assets repo
The restore desk answered a query about a prior retention cycle. The published schedule was reissued with the holiday dates corrected. It was filed at the weekly slot.
The documentation owner signed off the week's sampling with nothing outstanding. One field arrived null where the collector normally sends an empty string.

### Review entry 1015 — vault/obj repo
The operations desk summarised a call with the array supplier. One vault reported a snapshot fewer than the week before, all of it expected. The desk signed it off for the record.
> **Board minute (2026-03-05 - #RET-7109)** Rosa: deduplicate by snapshot_id keeping the FIRST-seen row in input order; ts and size do not override that.
The capacity planner revisited a control the auditors had asked about. Two tickets covering the same request were merged. The entry was left as it stands with no parameter change.

### Review entry 1016 — archive/cold repo
An on-call engineer logged a correction request from a repo owner. A restore rehearsal completed inside its window with nothing to note.
> **Board minute (2026-03-09 - #RET-7009)** Priya: inventory recovery interim: the replay journal outranks the pre-incident catalogue on overlap, but a replayed snapshot is appended to the END of the rebuilt inventory rather than taking the catalogue record's position, and a retraction only applies to snapshot_ids the catalogue never held.
The escalation desk wrote up an overnight page that had cleared itself. The snapshot count sat a little above the running mean, entirely from estimated inputs. The owner acknowledged it at the same meeting.

### Review entry 1017 — vault/app repo
The platform team carried a minor point forward to the next desk. The overnight batch finished ahead of its usual window for the third night running. It was recorded with no change to any published figure.
> **Board minute (2026-03-06 - #RET-7115)** Priya: quota ledger interim: decay and size both FLOOR — carry_in = max(prev.used_quota - idle_gap // 86400, 0), size_mb = size_bytes // 1048576, and there is NO reset boundary.
The reference-data team published the retention calendar for the coming quarter. Late input arrived from one collector and was loaded before the cut.

### Review entry 1018 — vault/pg repo
The audit lead acknowledged a pin request and filed it. The weekly extract came back a few kilobytes larger than usual, entirely in padding. It was filed and nothing was carried forward.
A desk supervisor reviewed an access request that had been sitting open. The variance sat inside tolerance and no adjustment was raised. The item was closed at the weekly slot.

### Review entry 1019 — vault/redis repo
A shift handover picked up a small discrepancy in a run log. One collector fell behind for a few minutes and caught up without gaps.
> **Board minute (2026-03-08 - #RET-7048)** Yusuf: max_quota_used is taken over the FINAL pruned rows only.
The change board closed a housekeeping item on the nightly export. The clock on a test host had drifted and was resynchronised. The entry was left as it stands for the record.

### Review entry 1020 — media/assets repo
The storage desk tidied a stale link in the operator runbook. The quarterly capacity figure landed within a percent of the forecast. The thread was archived with no parameter change.
The data-quality group recorded a maintenance note against the catalogue host. One record appeared twice in the export after a mid-cycle correction.

### Review entry 1021 — vault/obj repo
The duty analyst answered a query about a prior retention cycle. A report was regenerated after someone opened it mid-write. It was recorded at the same meeting.
> **Board minute (2026-05-02 - #RET-7101)** Yusuf: canonicalization: repo and vault via str(...).strip().lower() (empty -> 'unassigned'); note collapses internal whitespace; size_bytes and ts coerce int(str(x).strip()), else int(float(...)), else 0 — a size or ts that fails still KEEPS the row; pinned — booleans unchanged, strings true/1/yes/pinned => true, other strings => false, non-string/non-bool via bool(value)
The restore desk signed off the week's sampling with nothing outstanding. A stale credential was rotated on schedule rather than in response to anything. It was noted with no change to any published figure.

### Review entry 1022 — archive/cold repo
The documentation owner summarised a call with the array supplier. An export ran twice because an operator retried a step that had succeeded.
The operations desk revisited a control the auditors had asked about. The pin registry gained an entry and lost one in the same cycle. The item was closed and nothing was carried forward.

### Review entry 1023 — vault/app repo
The capacity planner logged a correction request from a repo owner. A scheduled restart moved by twenty minutes and nobody noticed downstream. The desk signed it off at the weekly slot.
> **Board minute (2026-05-03 - #RET-7102)** Yusuf: deduplicate by snapshot_id, final: keep the row with the HIGHEST ts; tie-break by size_bytes (direction set by #RET-7142), then longer normalized note, then lexicographically larger normalized repo, then first-seen input order.
An on-call engineer wrote up an overnight page that had cleared itself. Disk usage on the log volume fell after the retention change took effect.

### Review entry 1024 — vault/pg repo
The escalation desk carried a minor point forward to the next desk. A question raised on the floor was withdrawn once the entry was reread. The thread was archived for the record.
The platform team published the retention calendar for the coming quarter. A dashboard tile rendered blank until the browser cache was cleared. The owner acknowledged it with no parameter change.

### Review entry 1025 — vault/redis repo
The reference-data team acknowledged a pin request and filed it. A typo in a reference record was corrected before the run started.
> **Board minute (2026-05-14 - #RET-7142)** Yusuf: duplicate size precedence is REVERSED. Watchdog re-emissions inflate a repeated snapshot's recorded size before an operator confirms it, so where two rows share a snapshot_id and tie on ts, keep the row with the LOWER size_bytes. Only this comparison changes; the rest of the #RET-7102 chain runs unchanged after it.
The audit lead reviewed an access request that had been sitting open. The archive job skipped a directory that had already been swept. It was noted at the same meeting.

### Review entry 1026 — media/assets repo
A desk supervisor picked up a small discrepancy in a run log. A supplier's status page showed a brief degradation that did not reach us. It was filed with no change to any published figure.
A shift handover closed a housekeeping item on the nightly export. The nightly integrity sweep over the catalogue completed clean.

### Review entry 1027 — vault/obj repo
The change board tidied a stale link in the operator runbook. A repo owner's contact record was refreshed at their own request. The desk signed it off and nothing was carried forward.
> **Board minute (2026-05-04 - #RET-7104)** Lena: governance retention calendar, final (integer epoch-seconds): a retention DAY rolls at 04:00 UTC not midnight so gday = (ts - 14400) // 86400; the retention WEEK starts Sunday not ISO Monday so gweek = (gday - 3) // 7; the retention MONTH is a fixed 30-day block gmonth = gday // 30 (NOT a calendar month); the retention YEAR is a fixed 360-day block gyear = gday // 360. Compute every bucket id from these integer formulas: not one of these boundaries is the one a calendar library would give you, so a library's own day, week, month or year semantics will not reproduce them. Supersedes #RET-7004.
The storage desk recorded a maintenance note against the catalogue host. An out-of-office reply bounced a notification back into the queue. The entry was left as it stands at the weekly slot.

### Review entry 1028 — archive/cold repo
The data-quality group answered a query about a prior retention cycle. The published schedule was reissued with the holiday dates corrected.
The duty analyst signed off the week's sampling with nothing outstanding. One field arrived null where the collector normally sends an empty string. The owner acknowledged it for the record.

### Review entry 1029 — vault/app repo
The restore desk summarised a call with the array supplier. One vault reported a snapshot fewer than the week before, all of it expected. It was recorded with no parameter change.
> **Board minute (2026-05-04 - #RET-7106)** Lena: per-bucket representative, final: within a bucket the representative is the snapshot with the SMALLEST ts (the sealed period marker), tie-break by LARGER size_bytes then snapshot_id ascending. Supersedes #RET-7006.
The documentation owner revisited a control the auditors had asked about. Two tickets covering the same request were merged.

### Review entry 1030 — vault/pg repo
The operations desk logged a correction request from a repo owner. A restore rehearsal completed inside its window with nothing to note. It was filed at the same meeting.
The capacity planner wrote up an overnight page that had cleared itself. The snapshot count sat a little above the running mean, entirely from estimated inputs. The item was closed with no change to any published figure.

### Review entry 1031 — vault/redis repo
An on-call engineer carried a minor point forward to the next desk. The overnight batch finished ahead of its usual window for the third night running.
> **Board minute (2026-05-07 - #RET-7120)** Lena: per-tier caps select the most-recent buckets: for each tier compute every bucket's representative, then select the C buckets with the GREATEST bucket id (most recent), C being the resolved cap_daily/cap_weekly/cap_monthly/cap_yearly; the representative of each selected bucket is kept for that tier. Supersedes #RET-7020.
The escalation desk published the retention calendar for the coming quarter. Late input arrived from one collector and was loaded before the cut. The entry was left as it stands and nothing was carried forward.

### Review entry 1032 — media/assets repo
The platform team acknowledged a pin request and filed it. The weekly extract came back a few kilobytes larger than usual, entirely in padding. The thread was archived at the weekly slot.
The reference-data team reviewed an access request that had been sitting open. The variance sat inside tolerance and no adjustment was raised.

### Review entry 1033 — vault/obj repo
The audit lead picked up a small discrepancy in a run log. One collector fell behind for a few minutes and caught up without gaps. It was recorded for the record.
> **Board minute (2026-05-08 - #RET-7124)** Priya: pinned-hold exemption, final: a snapshot is HELD if its event pinned flag is true OR (repo, snapshot_id) appears in /app/data/pin_registry.json with a recognized hold in {compliance, legal, manual}; a held snapshot is ALWAYS kept regardless of caps and buckets, and carries the 'pinned' role. Every emitted row also carries a hold label: 'flag' when the snapshot is held by its own event pinned flag, otherwise the recognized registry hold label, otherwise the empty string. Where the register carries MORE THAN ONE recognized hold for the same (repo, snapshot_id) the strictest is the one reported, `compliance` ahead of `legal` ahead of `manual`, and an unrecognized hold is ignored whether or not a recognized one sits beside it. Supersedes #RET-7024.
A desk supervisor closed a housekeeping item on the nightly export. The clock on a test host had drifted and was resynchronised. It was noted with no parameter change.

### Review entry 1034 — archive/cold repo
A shift handover tidied a stale link in the operator runbook. The quarterly capacity figure landed within a percent of the forecast.
The change board recorded a maintenance note against the catalogue host. One record appeared twice in the export after a mid-cycle correction. The item was closed at the same meeting.

### Review entry 1035 — vault/app repo
The storage desk answered a query about a prior retention cycle. A report was regenerated after someone opened it mid-write. The desk signed it off with no change to any published figure.
> **Board minute (2026-05-08 - #RET-7122)** Priya: cross-tier promotion, final: the kept set is the UNION over tiers of the selected-bucket representatives plus the held snapshots. A single snapshot that represents selected buckets in several tiers carries ALL those tier roles at once — a kept daily also satisfies the weekly/monthly/yearly slot it marks — so the kept COUNT is the union, not the sum, of the per-tier selections. A kept snapshot's roles list the tiers it represents in daily,weekly,monthly,yearly order, with 'pinned' appended when held. Supersedes #RET-7022.
The data-quality group signed off the week's sampling with nothing outstanding. A stale credential was rotated on schedule rather than in response to anything.

### Review entry 1036 — vault/pg repo
The duty analyst summarised a call with the array supplier. An export ran twice because an operator retried a step that had succeeded. The thread was archived and nothing was carried forward.
The restore desk revisited a control the auditors had asked about. The pin registry gained an entry and lost one in the same cycle. The owner acknowledged it at the weekly slot.

### Review entry 1037 — vault/redis repo
The documentation owner logged a correction request from a repo owner. A scheduled restart moved by twenty minutes and nobody noticed downstream.
> **Board minute (2026-05-06 - #RET-7116)** Yusuf: per-repo quota ledger: state is independent per repo; process each repo's KEPT snapshots in ascending (ts, snapshot_id) order. First kept snapshot: idle_gap=0, carry_in=0. Later: idle_gap = max(current.ts - previous.ts, 0); if idle_gap exceeds the reset boundary of 2592000 seconds (30 days) the quota RESETS so carry_in=0, otherwise carry_in = max(previous.used_quota - decay(idle_gap), 0); used_quota = min(carry_in + size_mb, quota_cap) with quota_cap the resolved policy value. Decay rounding is set by #RET-7160 and size_mb by #RET-7162. The ledger runs over kept snapshots only, so idle_gap, carry_in and used_quota are reported as 0 on pruned and deferred rows, while size_mb is reported on every row from that row's own size_bytes.
The operations desk wrote up an overnight page that had cleared itself. Disk usage on the log volume fell after the retention change took effect. It was noted for the record.

### Review entry 1038 — media/assets repo
The capacity planner carried a minor point forward to the next desk. A question raised on the floor was withdrawn once the entry was reread. It was filed with no parameter change.
An on-call engineer published the retention calendar for the coming quarter. A dashboard tile rendered blank until the browser cache was cleared.

### Review entry 1039 — vault/obj repo
The escalation desk acknowledged a pin request and filed it. A typo in a reference record was corrected before the run started. The desk signed it off at the same meeting.
> **Board minute (2026-05-28 - #RET-7160)** Yusuf: ledger idle-gap decay rounding, final: decay(idle_gap) = ceil(idle_gap / 86400) — one quota unit per whole idle day, ROUNDED UP. In integer arithmetic ceil(x/n) is -(-x // n)
The platform team reviewed an access request that had been sitting open. The archive job skipped a directory that had already been swept. The entry was left as it stands with no change to any published figure.

### Review entry 1040 — archive/cold repo
The reference-data team picked up a small discrepancy in a run log. A supplier's status page showed a brief degradation that did not reach us.
The audit lead closed a housekeeping item on the nightly export. The nightly integrity sweep over the catalogue completed clean. The owner acknowledged it and nothing was carried forward.

### Review entry 1041 — vault/app repo
A desk supervisor tidied a stale link in the operator runbook. A repo owner's contact record was refreshed at their own request. It was recorded at the weekly slot.
> **Board minute (2026-05-29 - #RET-7162)** Yusuf: ledger size quantum, final: size_mb = ceil(size_bytes / 1048576) (bytes per MiB, ROUNDED UP) — a partially filled MiB still consumes a whole quota unit; used_quota accumulates size_mb.
A shift handover recorded a maintenance note against the catalogue host. An out-of-office reply bounced a notification back into the queue.

### Review entry 1042 — vault/pg repo
The change board answered a query about a prior retention cycle. The published schedule was reissued with the holiday dates corrected. It was filed for the record.
The storage desk signed off the week's sampling with nothing outstanding. One field arrived null where the collector normally sends an empty string. The item was closed with no parameter change.

### Review entry 1043 — vault/redis repo
The data-quality group summarised a call with the array supplier. One vault reported a snapshot fewer than the week before, all of it expected.
> **Board minute (2026-05-10 - #RET-7145)** Marek: prune and decision ordering: order every prune candidate WITHIN a repo by size_bytes DESC, then ts ASC, then snapshot_id ASC (reclaim the largest, oldest first). The retention_decisions rows are emitted globally sorted by decision class rank prune < defer < keep, then size_bytes DESC, then ts ASC, then repo ASC, then snapshot_id ASC.
The duty analyst revisited a control the auditors had asked about. Two tickets covering the same request were merged. The entry was left as it stands at the same meeting.

### Review entry 1044 — media/assets repo
The restore desk logged a correction request from a repo owner. A restore rehearsal completed inside its window with nothing to note. The thread was archived with no change to any published figure.
The documentation owner wrote up an overnight page that had cleared itself. The snapshot count sat a little above the running mean, entirely from estimated inputs.

### Review entry 1045 — vault/obj repo
The operations desk carried a minor point forward to the next desk. The overnight batch finished ahead of its usual window for the third night running. It was recorded and nothing was carried forward.
> **Board minute (2026-05-24 - #RET-7146)** Marek: per-repo prune cap: after ordering a repo's prune candidates by #RET-7145, only the FIRST prune_cap (resolved policy) candidates are pruned this cycle with decision 'prune'; the remainder are DEFERRED with decision 'defer' for a later cycle. Kept snapshots take decision 'keep'. Supersedes #RET-7040.
The capacity planner published the retention calendar for the coming quarter. Late input arrived from one collector and was loaded before the cut. It was noted at the weekly slot.

### Review entry 1046 — archive/cold repo
An on-call engineer acknowledged a pin request and filed it. The weekly extract came back a few kilobytes larger than usual, entirely in padding.
The escalation desk reviewed an access request that had been sitting open. The variance sat inside tolerance and no adjustment was raised. The item was closed for the record.

### Review entry 1047 — vault/app repo
The platform team picked up a small discrepancy in a run log. One collector fell behind for a few minutes and caught up without gaps. The desk signed it off with no parameter change.
> **Board minute (2026-05-10 - #RET-7148)** Yusuf: summary aggregation, final: decision_counts enumerates keep, prune, defer in that fixed order using 0 when absent; max_quota_used is the maximum used_quota over EVERY kept snapshot using 0 when none; reclaimed_size_bytes sums the size_bytes of pruned snapshots and deferred_size_bytes the deferred ones.
The reference-data team closed a housekeeping item on the nightly export. The clock on a test host had drifted and was resynchronised.

### Review entry 1048 — vault/pg repo
The audit lead tidied a stale link in the operator runbook. The quarterly capacity figure landed within a percent of the forecast. The thread was archived at the same meeting.
A desk supervisor recorded a maintenance note against the catalogue host. One record appeared twice in the export after a mid-cycle correction. The owner acknowledged it with no change to any published figure.

### Review entry 1049 — vault/redis repo
A shift handover answered a query about a prior retention cycle. A report was regenerated after someone opened it mid-write.
> **Board minute (2026-05-16 - #RET-7144)** Priya: retention week boundary realigned to the ISO Monday start so the weekly rollup lines up with the platform reporting week: gweek = (gday - 4) // 7. This revises the Sunday start of #RET-7104; the day, month and year boundaries stated there are untouched.

> **Board minute (2026-05-18 - #RET-7150)** Priya: retention policy baseline (read from /app/data/retention_policy.json at that fixed absolute path; --input never relocates it). Any field the policy file omits keeps its baseline: cap_daily=7; cap_weekly=4; cap_monthly=6; cap_yearly=2; quota_cap=100000; prune_cap=4200; protection_days=21.
The change board signed off the week's sampling with nothing outstanding. A stale credential was rotated on schedule rather than in response to anything. It was noted and nothing was carried forward.

### Review entry 1050 — media/assets repo
The storage desk summarised a call with the array supplier. An export ran twice because an operator retried a step that had succeeded. It was filed at the weekly slot.
The data-quality group revisited a control the auditors had asked about. The pin registry gained an entry and lost one in the same cycle.

### Review entry 1051 — vault/obj repo
The duty analyst logged a correction request from a repo owner. A scheduled restart moved by twenty minutes and nobody noticed downstream. The desk signed it off for the record.
> **Board minute (2026-05-18 - #RET-7152)** Priya: policy resolution, per repo, in three layers: start from the #RET-7150 baseline; overlay every field the policy file's default object supplies (it need not be complete — an omitted field keeps its baseline); then overlay every field that repo's entry in repo_overrides supplies (an override names only the fields it changes and inherits the rest). Coerce every value to int.
The restore desk wrote up an overnight page that had cleared itself. Disk usage on the log volume fell after the retention change took effect. The entry was left as it stands with no parameter change.

### Review entry 1052 — archive/cold repo
The documentation owner carried a minor point forward to the next desk. A question raised on the floor was withdrawn once the entry was reread.
The operations desk published the retention calendar for the coming quarter. A dashboard tile rendered blank until the browser cache was cleared. The owner acknowledged it at the same meeting.

### Review entry 1053 — vault/app repo
The capacity planner acknowledged a pin request and filed it. A typo in a reference record was corrected before the run started. It was recorded with no change to any published figure.
An on-call engineer reviewed an access request that had been sitting open. The archive job skipped a directory that had already been swept.

### Review entry 1054 — vault/pg repo
The escalation desk picked up a small discrepancy in a run log. A supplier's status page showed a brief degradation that did not reach us. It was filed and nothing was carried forward.
The platform team closed a housekeeping item on the nightly export. The nightly integrity sweep over the catalogue completed clean. The item was closed at the weekly slot.

### Review entry 1055 — vault/redis repo
The reference-data team tidied a stale link in the operator runbook. A repo owner's contact record was refreshed at their own request.
The audit lead recorded a maintenance note against the catalogue host. An out-of-office reply bounced a notification back into the queue. The entry was left as it stands for the record.

### Review entry 1056 — media/assets repo
A desk supervisor answered a query about a prior retention cycle. The published schedule was reissued with the holiday dates corrected. The thread was archived with no parameter change.
A shift handover signed off the week's sampling with nothing outstanding. One field arrived null where the collector normally sends an empty string.

### Review entry 1057 — vault/obj repo
The change board summarised a call with the array supplier. One vault reported a snapshot fewer than the week before, all of it expected. It was recorded at the same meeting.
The storage desk revisited a control the auditors had asked about. Two tickets covering the same request were merged. It was noted with no change to any published figure.

### Review entry 1058 — archive/cold repo
The data-quality group logged a correction request from a repo owner. A restore rehearsal completed inside its window with nothing to note.
The duty analyst wrote up an overnight page that had cleared itself. The snapshot count sat a little above the running mean, entirely from estimated inputs. The item was closed and nothing was carried forward.

### Review entry 1059 — vault/app repo
The restore desk carried a minor point forward to the next desk. The overnight batch finished ahead of its usual window for the third night running. The desk signed it off at the weekly slot.
The documentation owner published the retention calendar for the coming quarter. Late input arrived from one collector and was loaded before the cut.

### Review entry 1060 — vault/pg repo
The operations desk acknowledged a pin request and filed it. The weekly extract came back a few kilobytes larger than usual, entirely in padding. The thread was archived for the record.
The capacity planner reviewed an access request that had been sitting open. The variance sat inside tolerance and no adjustment was raised. The owner acknowledged it with no parameter change.

### Review entry 1061 — vault/redis repo
An on-call engineer picked up a small discrepancy in a run log. One collector fell behind for a few minutes and caught up without gaps.
The escalation desk closed a housekeeping item on the nightly export. The clock on a test host had drifted and was resynchronised. It was noted at the same meeting.

### Review entry 1062 — media/assets repo
The platform team tidied a stale link in the operator runbook. The quarterly capacity figure landed within a percent of the forecast. It was filed with no change to any published figure.
The reference-data team recorded a maintenance note against the catalogue host. One record appeared twice in the export after a mid-cycle correction.

### Review entry 1063 — vault/obj repo
The audit lead answered a query about a prior retention cycle. A report was regenerated after someone opened it mid-write. The desk signed it off and nothing was carried forward.
A desk supervisor signed off the week's sampling with nothing outstanding. A stale credential was rotated on schedule rather than in response to anything. The entry was left as it stands at the weekly slot.

### Review entry 1064 — archive/cold repo
A shift handover summarised a call with the array supplier. An export ran twice because an operator retried a step that had succeeded.
The change board revisited a control the auditors had asked about. The pin registry gained an entry and lost one in the same cycle. The owner acknowledged it for the record.

### Review entry 1065 — vault/app repo
The storage desk logged a correction request from a repo owner. A scheduled restart moved by twenty minutes and nobody noticed downstream. It was recorded with no parameter change.
The data-quality group wrote up an overnight page that had cleared itself. Disk usage on the log volume fell after the retention change took effect.

### Review entry 1066 — vault/pg repo
The duty analyst carried a minor point forward to the next desk. A question raised on the floor was withdrawn once the entry was reread. It was filed at the same meeting.
The restore desk published the retention calendar for the coming quarter. A dashboard tile rendered blank until the browser cache was cleared. The item was closed with no change to any published figure.

### Review entry 1067 — vault/redis repo
The documentation owner acknowledged a pin request and filed it. A typo in a reference record was corrected before the run started.
The operations desk reviewed an access request that had been sitting open. The archive job skipped a directory that had already been swept. The entry was left as it stands and nothing was carried forward.

### Review entry 1068 — media/assets repo
The capacity planner picked up a small discrepancy in a run log. A supplier's status page showed a brief degradation that did not reach us. The thread was archived at the weekly slot.
An on-call engineer closed a housekeeping item on the nightly export. The nightly integrity sweep over the catalogue completed clean.

### Review entry 1069 — vault/obj repo
The escalation desk tidied a stale link in the operator runbook. A repo owner's contact record was refreshed at their own request. It was recorded for the record.
The platform team recorded a maintenance note against the catalogue host. An out-of-office reply bounced a notification back into the queue. It was noted with no parameter change.

### Review entry 1070 — archive/cold repo
The reference-data team answered a query about a prior retention cycle. The published schedule was reissued with the holiday dates corrected.
The audit lead signed off the week's sampling with nothing outstanding. One field arrived null where the collector normally sends an empty string. The item was closed at the same meeting.

### Review entry 1071 — vault/app repo
A desk supervisor summarised a call with the array supplier. One vault reported a snapshot fewer than the week before, all of it expected. The desk signed it off with no change to any published figure.
A shift handover revisited a control the auditors had asked about. Two tickets covering the same request were merged.

### Review entry 1072 — vault/pg repo
The change board logged a correction request from a repo owner. A restore rehearsal completed inside its window with nothing to note. The thread was archived and nothing was carried forward.
The storage desk wrote up an overnight page that had cleared itself. The snapshot count sat a little above the running mean, entirely from estimated inputs. The owner acknowledged it at the weekly slot.

### Review entry 1073 — vault/redis repo
The data-quality group carried a minor point forward to the next desk. The overnight batch finished ahead of its usual window for the third night running.
The duty analyst published the retention calendar for the coming quarter. Late input arrived from one collector and was loaded before the cut. It was noted for the record.

### Review entry 1074 — media/assets repo
The restore desk acknowledged a pin request and filed it. The weekly extract came back a few kilobytes larger than usual, entirely in padding. It was filed with no parameter change.
The documentation owner reviewed an access request that had been sitting open. The variance sat inside tolerance and no adjustment was raised.

### Review entry 1075 — vault/obj repo
The operations desk picked up a small discrepancy in a run log. One collector fell behind for a few minutes and caught up without gaps. The desk signed it off at the same meeting.
The capacity planner closed a housekeeping item on the nightly export. The clock on a test host had drifted and was resynchronised. The entry was left as it stands with no change to any published figure.

### Review entry 1076 — archive/cold repo
An on-call engineer tidied a stale link in the operator runbook. The quarterly capacity figure landed within a percent of the forecast.
The escalation desk recorded a maintenance note against the catalogue host. One record appeared twice in the export after a mid-cycle correction. The owner acknowledged it and nothing was carried forward.

### Review entry 1077 — vault/app repo
The platform team answered a query about a prior retention cycle. A report was regenerated after someone opened it mid-write. It was recorded at the weekly slot.
The reference-data team signed off the week's sampling with nothing outstanding. A stale credential was rotated on schedule rather than in response to anything.

### Review entry 1078 — vault/pg repo
The audit lead summarised a call with the array supplier. An export ran twice because an operator retried a step that had succeeded. It was filed for the record.
A desk supervisor revisited a control the auditors had asked about. The pin registry gained an entry and lost one in the same cycle. The item was closed with no parameter change.

### Review entry 1079 — vault/redis repo
A shift handover logged a correction request from a repo owner. A scheduled restart moved by twenty minutes and nobody noticed downstream.
The change board wrote up an overnight page that had cleared itself. Disk usage on the log volume fell after the retention change took effect. The entry was left as it stands at the same meeting.

### Review entry 1080 — media/assets repo
The storage desk carried a minor point forward to the next desk. A question raised on the floor was withdrawn once the entry was reread. The thread was archived with no change to any published figure.
The data-quality group published the retention calendar for the coming quarter. A dashboard tile rendered blank until the browser cache was cleared.

### Review entry 1081 — vault/obj repo
The duty analyst acknowledged a pin request and filed it. A typo in a reference record was corrected before the run started. It was recorded and nothing was carried forward.
The restore desk reviewed an access request that had been sitting open. The archive job skipped a directory that had already been swept. It was noted at the weekly slot.

### Review entry 1082 — archive/cold repo
The documentation owner picked up a small discrepancy in a run log. A supplier's status page showed a brief degradation that did not reach us.
The operations desk closed a housekeeping item on the nightly export. The nightly integrity sweep over the catalogue completed clean. The item was closed for the record.

### Review entry 1083 — vault/app repo
The capacity planner tidied a stale link in the operator runbook. A repo owner's contact record was refreshed at their own request. The desk signed it off with no parameter change.
An on-call engineer recorded a maintenance note against the catalogue host. An out-of-office reply bounced a notification back into the queue.

### Review entry 1084 — vault/pg repo
The escalation desk answered a query about a prior retention cycle. The published schedule was reissued with the holiday dates corrected. The thread was archived at the same meeting.
The platform team signed off the week's sampling with nothing outstanding. One field arrived null where the collector normally sends an empty string. The owner acknowledged it with no change to any published figure.

### Review entry 1085 — vault/redis repo
The reference-data team summarised a call with the array supplier. One vault reported a snapshot fewer than the week before, all of it expected.
The audit lead revisited a control the auditors had asked about. Two tickets covering the same request were merged. It was noted and nothing was carried forward.

### Review entry 1086 — media/assets repo
A desk supervisor logged a correction request from a repo owner. A restore rehearsal completed inside its window with nothing to note. It was filed at the weekly slot.
A shift handover wrote up an overnight page that had cleared itself. The snapshot count sat a little above the running mean, entirely from estimated inputs.

### Review entry 1087 — vault/obj repo
The change board carried a minor point forward to the next desk. The overnight batch finished ahead of its usual window for the third night running. The desk signed it off for the record.
The storage desk published the retention calendar for the coming quarter. Late input arrived from one collector and was loaded before the cut. The entry was left as it stands with no parameter change.

### Review entry 1088 — archive/cold repo
The data-quality group acknowledged a pin request and filed it. The weekly extract came back a few kilobytes larger than usual, entirely in padding.
The duty analyst reviewed an access request that had been sitting open. The variance sat inside tolerance and no adjustment was raised. The owner acknowledged it at the same meeting.

### Review entry 1089 — vault/app repo
The restore desk picked up a small discrepancy in a run log. One collector fell behind for a few minutes and caught up without gaps. It was recorded with no change to any published figure.
The documentation owner closed a housekeeping item on the nightly export. The clock on a test host had drifted and was resynchronised.

### Review entry 1090 — vault/pg repo
The operations desk tidied a stale link in the operator runbook. The quarterly capacity figure landed within a percent of the forecast. It was filed and nothing was carried forward.
The capacity planner recorded a maintenance note against the catalogue host. One record appeared twice in the export after a mid-cycle correction. The item was closed at the weekly slot.

### Review entry 1091 — vault/redis repo
An on-call engineer answered a query about a prior retention cycle. A report was regenerated after someone opened it mid-write.
> **Board minute (2026-06-02 - #RET-7170)** Lena: authoritative snapshot-inventory recovery, final — it runs BEFORE any reconcile. The rollout truncated `/app/data/snapshots.json`, so that file is no longer authoritative and must be rebuilt in place from the two surviving sources beside it. Begin with every record of `/app/data/snapshot_catalogue_pre_incident.json` in catalogue file order. Then apply `/app/data/snapshot_replay_journal.json` in ascending journal_seq order, one entry at a time; the journal is stored unsorted and replaying it in file order is wrong. An entry whose journal_op is `append` carries a snapshot record created or corrected after the catalogue was taken: if the inventory already holds a record with that snapshot_id the entry OVERWRITES the FIRST such record IN PLACE, keeping that record's existing position (it is NOT moved to the end, revising #RET-7009); otherwise the record is appended to the end of the inventory. An entry whose journal_op is `retract` removes EVERY record carrying that snapshot_id, whether the snapshot_id came from the catalogue or from an earlier journal entry (also revising #RET-7009), and contributes no record of its own. The journal always wins on overlap; the catalogue never overrides it, and a catalogue record the journal corrects is stale — its ts and size_bytes are provisional and can place it in the wrong retention bucket. journal_seq, journal_op and reason are journal bookkeeping, not snapshot fields: a recovered record carries exactly snapshot_id, repo, vault, ts, size_bytes, pinned and note, with the journal's values for a replayed snapshot. Write the result back to `/app/data/snapshots.json` as a JSON array in exactly the order described. Nothing downstream re-orders it — the #RET-7102/#RET-7142 deduplication runs over this inventory and its first-seen tie-break follows this order — so an inventory rebuilt any other way yields wrong keep, prune and defer decisions.
The escalation desk signed off the week's sampling with nothing outstanding. A stale credential was rotated on schedule rather than in response to anything. The entry was left as it stands for the record.

### Review entry 1092 — media/assets repo
The platform team summarised a call with the array supplier. An export ran twice because an operator retried a step that had succeeded. The thread was archived with no parameter change.
The reference-data team revisited a control the auditors had asked about. The pin registry gained an entry and lost one in the same cycle.

### Review entry 1093 — vault/obj repo
The audit lead logged a correction request from a repo owner. A scheduled restart moved by twenty minutes and nobody noticed downstream. It was recorded at the same meeting.
A desk supervisor wrote up an overnight page that had cleared itself. Disk usage on the log volume fell after the retention change took effect. It was noted with no change to any published figure.

### Review entry 1094 — archive/cold repo
A shift handover carried a minor point forward to the next desk. A question raised on the floor was withdrawn once the entry was reread.
The change board published the retention calendar for the coming quarter. A dashboard tile rendered blank until the browser cache was cleared. The item was closed and nothing was carried forward.

### Review entry 1095 — vault/app repo
The storage desk acknowledged a pin request and filed it. A typo in a reference record was corrected before the run started. The desk signed it off at the weekly slot.
The data-quality group reviewed an access request that had been sitting open. The archive job skipped a directory that had already been swept.

### Review entry 1096 — vault/pg repo
The duty analyst picked up a small discrepancy in a run log. A supplier's status page showed a brief degradation that did not reach us. The thread was archived for the record.
The restore desk closed a housekeeping item on the nightly export. The nightly integrity sweep over the catalogue completed clean. The owner acknowledged it with no parameter change.

### Review entry 1097 — vault/redis repo
The documentation owner tidied a stale link in the operator runbook. A repo owner's contact record was refreshed at their own request.
The operations desk recorded a maintenance note against the catalogue host. An out-of-office reply bounced a notification back into the queue. It was noted at the same meeting.

### Review entry 1098 — media/assets repo
The capacity planner answered a query about a prior retention cycle. The published schedule was reissued with the holiday dates corrected. It was filed with no change to any published figure.
An on-call engineer signed off the week's sampling with nothing outstanding. One field arrived null where the collector normally sends an empty string.

### Review entry 1099 — vault/obj repo
The escalation desk summarised a call with the array supplier. One vault reported a snapshot fewer than the week before, all of it expected. The desk signed it off and nothing was carried forward.
The platform team revisited a control the auditors had asked about. Two tickets covering the same request were merged. The entry was left as it stands at the weekly slot.

> **Board minute (2026-06-04 - #RET-7172)** Lena: protection-window overlap reporting, final. Every canonical snapshot holds a protection window running from its ts to ts + protection_days x 86400 inclusive, with protection_days the repo's RESOLVED policy value. Each retention decision carries `overlap_count`: how many OTHER canonical snapshots OF THE SAME REPO hold a window that intersects this one, where windows touching at an endpoint do intersect. A snapshot never counts itself, snapshots of other repos never count, and a record the de-duplication chain discarded never counts. The summary carries `max_overlap_count` over every decision. This settles the #RET-7118 draft, which counted only snapshots sharing a calendar bucket.

> **Board minute (2026-06-09 - #RET-7180)** Lena: protection depth reporting, final. The board also wants to see how deeply a repo's protection windows stack up, not only how many of them touch. Each retention decision carries `peak_depth`: the greatest number of that repo's canonical protection windows that are live at one and the same instant, taken over every instant lying inside this snapshot's OWN window, endpoints included. The snapshot itself is one of the live windows, so `peak_depth` is never below 1 and never above `overlap_count` + 1. Windows are the same windows #RET-7172 defines and are inclusive at both endpoints; snapshots of other repos never contribute and a record the de-duplication chain discarded never contributes. The summary carries `max_peak_depth` over every decision. Reporting the window's own endpoint depth rather than its busiest instant, as the March telemetry draft did, understates a stacked repo.

> **Board minute (2026-06-11 - #RET-7182)** Lena: retention week boundary, final. The Monday realignment shifted every weekly bucket by a day and the earliest-of-bucket representative moved with it, so vaults that had held the same weekly snapshot for months silently swapped to another one and the promotion counts moved with them. The board restores the Sunday start: gweek = (gday - 3) // 7. This supersedes #RET-7144; the day, month and year boundaries of #RET-7104 remain as written.

> **Board minute (2026-06-16 - #RET-7184)** Marek: prune selection, final. Restores are chained. Inside a vault the snapshots are one incremental chain in ascending ts order, and a KEPT snapshot re-anchors it, because retention promotes what it keeps to a full. The candidates lying between two kept snapshots -- and those before the first kept one, and those after the last -- therefore form a run that can only be cut from its newest end: a candidate may be pruned only when every candidate later than it in the same run is pruned too, since dropping a snapshot that a later one still builds on leaves the later one unrestorable. Subject to that and to the per-repo prune cap of #RET-7146, the cycle prunes the selection that reclaims the MOST bytes. Where two selections reclaim the same bytes the one pruning fewer snapshots governs; where they are still level the earlier run gives way first, runs ordered by vault, then by the ts and the snapshot_id of their oldest candidate. Giving way first means giving up as much as the tie allows: among selections that reclaim the same bytes with the same count, the one that cuts DEEPEST into the earliest run governs, then deepest into the next, and so on down the order. Every candidate not pruned is DEFERRED. This supersedes the size-ordered take-the-first-cap selection of #RET-7145 and #RET-7146, which took no account of chains; the decision-row emission order set by #RET-7145 is unchanged. The prune_cap baseline stated in #RET-7150 is revised to 300.
