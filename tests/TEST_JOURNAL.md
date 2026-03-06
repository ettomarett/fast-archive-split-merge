# Test journal — Fast Archive & Split (v1)

Manual test cases for the main scenarios. Fill in **Result** and **Date** when run.

## Environment

- OS: _________________
- Python: _________________
- Tkinter: _________________

---

## TC1 — Fast mode (no compression)

| Step | Action | Expected | Result | Date |
|------|--------|----------|--------|------|
| 1 | Select source folder (small, e.g. a few files) | Path appears | | |
| 2 | Select output folder | Path appears | | |
| 3 | Enter archive name, leave "Fast (no compression)" | — | | |
| 4 | Click Start, confirm | Progress runs, archive created | | |
| 5 | Check output | One file `name.tar` | | |
| 6 | Extract elsewhere: `tar -xf name.tar` | Contents match source, relative paths | | |

---

## TC2 — Split FAT32

| Step | Action | Expected | Result | Date |
|------|--------|----------|--------|------|
| 1 | Use a source large enough to exceed one chunk (e.g. > 3900 MiB) or smaller to get one part | — | | |
| 2 | Enable "Split into chunks", chunk size 3900 MiB | — | | |
| 3 | Start and confirm | Progress, then part files created | | |
| 4 | Check output | `name.tar.part-001`, `.part-002`, … each ≤ chunk size | | |
| 5 | Rejoin: `cat name.tar.part-* > name.tar` then extract | Archive valid, contents match | | |

---

## TC3 — Compression (gzip)

| Step | Action | Expected | Result | Date |
|------|--------|----------|--------|------|
| 1 | Select "Compressed (gzip)" | — | | |
| 2 | Start with same source as TC1 | Slower than fast, `name.tar.gz` created | | |
| 3 | Extract: `tar -xzf name.tar.gz` | Contents match source | | |

---

## TC4 — Cancel

| Step | Action | Expected | Result | Date |
|------|--------|----------|--------|------|
| 1 | Start a large job (or slow disk) | Progress visible | | |
| 2 | Click Cancel | Job stops, log shows "Cancelled by user" | | |
| 3 | Check output folder | No partial archive or parts left (or only removed) | | |
| 4 | Start/Cancel buttons | Start enabled, Cancel disabled | | |

---

## TC5 — Errors

| Step | Action | Expected | Result | Date |
|------|--------|----------|--------|------|
| 1 | Start without source folder | Error message, no crash | | |
| 2 | Output folder with no write permission | Clear error in log | | |
| 3 | Archive name with invalid characters | Validation error | | |
| 4 | Output file already exists | Overwrite prompt; if No, abort | | |
| 5 | Very low disk space (if feasible) | Error before or during job, message clear | | |

---

## TC6 — UX

| Step | Action | Expected | Result | Date |
|------|--------|----------|--------|------|
| 1 | Start job | Progress bar and labels (files, bytes, speed, ETA) update | | |
| 2 | During job | Window stays responsive | | |
| 3 | On success | "Open output folder" enabled; log shows success and rejoin hint if split | | |
| 4 | Recap dialog | Shows source, output, mode, split, chunk size before Start | | |

---

## Summary

| Test | Pass/Fail | Notes |
|------|-----------|-------|
| TC1 Fast | | |
| TC2 Split | | |
| TC3 Compressed | | |
| TC4 Cancel | | |
| TC5 Errors | | |
| TC6 UX | | |
