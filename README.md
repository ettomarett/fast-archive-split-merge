# Fast Archive Split Merge

Desktop app (Python 3.10+) to create TAR archives, optionally split them into size-limited chunks (e.g. for FAT32 or upload limits), and merge those parts back into a single archive. Helps move large data across disks and machines.

![Fast Archive & Split](https://github.com/ettomarett/fast-archive-split-merge/raw/main/assets/screenshot.png)

## Requirements

- **System:** Windows 10+ or Linux; Python 3.10+ with Tkinter. For **Turbo** mode: system `tar` (GNU tar on Linux; Windows 10+ includes `tar`).
- **Access:** Read access to the source folder and write access to the output folder. No API keys or online accounts. Optional: run with lower I/O priority on Linux if `ionice` is available (used automatically).

## Install

- **Python 3.10+** with Tkinter (on Ubuntu/Debian install `python3-tk`; on Windows use the official installer with tcl/tk).
- No extra packages; standard library only.

```bash
# From the project root
pip install -r requirements.txt   # if you use CustomTkinter
./run.sh                           # Linux
# or: python3 -c "import sys; sys.path.insert(0, '.'); from src.main import main; main()"
```

```batch
REM Windows
run.bat
```

## Use

### Create an archive (and optionally split it)

1. **Source Folder** — Folder to pack.
2. **Output Folder** — Where to write the archive (and parts, if split).
3. **Archive Name** — Base name only (e.g. `backup_2026`); `.tar` or `.tar.gz` is added automatically.
4. **Format** — **Fast** (no compression), **Compressed** (gzip), or **Turbo** (system tar, fastest when available).
5. **Split** — Turn on to get part files (e.g. 3900 MiB each for FAT32). With Turbo, splitting is streamed (no full archive on disk).
6. **Keep original after split** — Keep the full archive file as well as the parts.
7. Click **Start**, confirm, then wait. **Cancel** stops and removes partial output.

**When to use what:** One `.tar` to move a folder to another PC. For a **FAT32 USB** or **size limits** (cloud/email), turn on **Split**, copy the parts, then on the other side use **Merge parts** (below). Use **Compressed** to shrink the file; **Turbo** for maximum speed on big or many files.

### Merge parts (rejoin split files)

After copying part files to the destination disk or PC: click **Merge parts**, choose any part file (e.g. `name.tar.part-001`). The app finds all parts in that folder, checks they are contiguous (001, 002, 003…), and writes one archive in the same folder. Progress and Cancel work like when creating. Same on Windows and Linux. Then extract with `tar -xf` or 7-Zip.

## Output names

| Mode        | Result |
|-------------|--------|
| Fast        | `name.tar` |
| Compressed  | `name.tar.gz` |
| Turbo       | `name.tar` (or parts only when split) |
| Split       | `name.tar.part-001`, `name.tar.part-002`, … |

## Turbo and diagnostics

- **Turbo** uses the system `tar` (GNU tar on Linux, Windows 10+ tar). Fastest option; **Cancel** stops immediately.
- If Turbo is unavailable on Windows, use Fast.
- The log shows file count, total size, and filesystem type (Source / Output) for diagnostics.
- Archives use a single top-level directory (e.g. `backup_2026/...`); no absolute or `..` paths.

## Extract

- **After merging in the app** — Use `tar -xf name.tar` or `tar -xzf name.tar.gz`, or 7-Zip / WinRAR on Windows.
- **Rejoin without the app** — Linux/macOS: `cat name.tar.part-* > name.tar` then extract. Windows: `copy /b name.tar.part-001+name.tar.part-002+... name.tar` (order matters), then extract.

## Packaging (optional)

- **Ubuntu:** AppImage or PyInstaller (include `src`, entry point `src.main`).
- **Windows:** e.g. `pyinstaller --onefile --windowed -n FastArchive src/main.py` (include `src`).

## License

Open source: **GNU General Public License v3.0 (GPL-3.0)**. See [LICENSE](LICENSE).

---

**Developer:** Omar Ettalbi, SWE
