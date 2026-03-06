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

## How to use

In the app, click **How to use** for the same instructions in a popup; in that window, **Check if tar is installed** verifies whether Turbo mode is available.

### Create an archive

- **Source Folder** — Folder to pack (use **Browse** to select).
- **Output Folder** — Where the `.tar` or `.tar.gz` will be saved.
- **Archive Name** — Base name only (e.g. `backup_2026` → `backup_2026.tar`).
- **Format** — **Fast** (no compression, good for local copy), **Compressed** (gzip, smaller), or **Turbo** (system tar, fastest when installed).
- **Split** — Turn on to split into chunks (e.g. 3900 MiB for FAT32). Optionally **Keep original archive after split** to keep the full file as well as the parts.
- **Start** — Run the job. **Cancel** stops it. When done, **Open output folder** opens the result folder.

**When to use what:** One `.tar` to move a folder to another PC. For **FAT32 USB** or **size limits** (cloud/email), turn on **Split**, copy the parts, then use **Merge parts** (below) on the other side. Use **Compressed** to shrink; **Turbo** for maximum speed.

### Merge parts (rejoin split files)

- Use this to rejoin split parts (e.g. `name.part-001`, `name.part-002`) into one file.
- **Folder…** — Select the folder that contains the `.part-001`, `.part-002`, … files.
- **File…** — Select any part file (e.g. `name.part-001`); the app finds the rest.
- **Merge** — Writes the full archive in the same folder (e.g. `name.tar`).
- If the folder has more than one set of parts, pick a specific part file with **File…** instead of the folder.

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
