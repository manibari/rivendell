---
date: 2026-07-22
type: disk-capacity
percent: 92
status: warn
---

# Disk Capacity Report — 2026-07-22

Daily check by `bin/sk-disk-monitor-cron` (03:30). Monitors the macOS data
volume backing `$HOME`. Thresholds: WARN ≥90%, CRIT ≥95%.

## Summary

```
=== Disk Capacity Check ===
volume: /System/Volumes/Data (/dev/disk3s5)
used:   377G / 460G    avail: 37.2G
usage:  92% (warn ≥90%, crit ≥95%) → warn
```

## Raw JSON

```json
{"volume":"/dev/disk3s5","mount":"/System/Volumes/Data","size_gb":460,"used_gb":377,"avail_gb":37.2,"percent":92,"status":"warn","warn_threshold":90,"crit_threshold":95}
```

## How to fix

Free space without touching personal data (largest safe wins first):

- **Docker** — `docker system df`, then `docker builder prune -f` and
  `docker image prune -a -f`. NOTE: `image prune -a` won't remove images
  pinned by *stopped* containers — `docker rm <stale-container>` first.
  Docker.raw is a sparse image; it shrinks back via APFS TRIM after prune.
- **Xcode** — `rm -rf ~/Library/Developer/Xcode/DerivedData/*` (regenerates);
  `xcrun simctl delete unavailable`.
- **Caches / logs** — `~/Library/Caches` (disposable), `~/Library/Logs`
  (preserve `sk-agent/` observability logs).
- **Dev artifacts** — stale `node_modules` / `.next` in inactive repos.

See `docs/plans/2026-05-23-disk-space-cleanup.md` for the full playbook.

## Next reports

Re-runs daily at 03:30. Report regenerates each day usage stays ≥90%.
