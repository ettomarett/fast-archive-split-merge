# Benchmark & Definition of Done (revue finale)

## DoD — Progress

- **Turbo (file)** : progress = size of the `.tar` file being written (polled).
- **Turbo (streaming)** : progress = sum of bytes written to `.part-XXX` files (no archive file exists).

## DoD — Split

- No part file exceeds the configured chunk size (default 3900 MiB, FAT32 safe).
- The last part may be smaller.
- Naming: stable padding (`.part-001`, `.part-002`, …).

## DoD — Cancel

- Cancel during streaming: all incomplete part files are removed; UI returns to idle; log shows "Cancelled by user".
- No "success" output remains when the user cancelled.

## DoD — Correctness (paths)

- Extraction yields a single top-level directory (e.g. `backup_2026/...`), **not** absolute paths like `/mnt/.../...`.
- No `..` or absolute paths in the archive.

## DoD — Windows

- If system `tar` is present but incompatible (e.g. `-C` / arcname behaviour), the app does **not** offer Turbo (probe fails) or shows a clear message and suggests "Fast (no compression)" if tar fails at run time.

---

## Benchmark template (to fill with real runs)

Use two datasets to validate that Turbo is "much faster" on many small files and still good on few large files.

| Dataset | Description | Size | File count |
|--------|-------------|------|------------|
| A      | Many small files | ~7 GB | e.g. 100k+ |
| B      | Few large files  | ~7 GB | e.g. 10–50 |

**Results (example columns; fill with times in minutes)**

| Mode              | Dataset A (many files) | Dataset B (few files) |
|-------------------|------------------------|------------------------|
| Fast (Python)      | ___ min                | ___ min                |
| Turbo (system tar) | ___ min                | ___ min                |
| Turbo + streaming split | ___ min          | ___ min                |

**Expected**: Python mode is very slow on A, acceptable on B; Turbo is much faster on A and very fast on B; streaming split is close to Turbo file (sometimes slightly slower due to Python pipe overhead).

To check if you are near the hardware limit: note the log line "Source: X files, Y MiB" and the time in Turbo; compare throughput (Y MiB / time) to your disk/USB nominal speed.
