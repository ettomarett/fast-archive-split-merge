# Fast Archive & Split

Desktop application (Python 3.10+) to create TAR archives quickly without compression, with optional gzip compression and optional split into FAT32-safe chunks (~4 GB).

![Fast Archive & Split](https://github.com/ettomarett/fast-archive-split-merge/raw/main/assets/screenshot.png)

## Install

- **Python 3.10+** with Tkinter (on Ubuntu/Debian install `python3-tk` if needed; on Windows use the official installer and ensure "tcl/tk" is selected).
- No extra packages: the app uses only the standard library.

```bash
# Clone or copy the project, then from the project root:
# Ubuntu/Linux
./run.sh

# Or run directly
python3 -c "import sys; sys.path.insert(0, '.'); from src.main import main; main()"
```

```batch
REM Windows
run.bat
REM Or: python -c "import sys; sys.path.insert(0, '.'); from src.main import main; main()"
```

## Use

**When to use what:** Archive a project folder to **move it to another PC** (one `.tar` file). Need to **copy onto a FAT32 USB stick** or **stay under a cloud/email size limit?** Turn on **Split** so you get part files (e.g. 3900 MiB each), copy them over, then on the other side use **Merge parts** (see below). Use **Compressed** when the archive must be smaller (e.g. uploading); **Turbo** when you have huge or many files and want maximum speed. **Keep original after split** if you want both the full archive and the parts on the same machine (e.g. local backup + parts to take away).

1. **Source Folder** — Choose the folder to archive.
2. **Output Folder** — Choose where to write the archive (and parts, if split).
3. **Archive Name** — Base name only (e.g. `backup_2026`). Extension is added automatically (`.tar` or `.tar.gz`).
4. **Format** — **Fast (no compression)** (Python), **Compressed (gzip)**, or **Turbo (system tar)** when available (uses the system `tar` binary for maximum speed; cancel is immediate).
5. **Split** — Enable "Split into chunks" and set chunk size (default 3900 MiB, FAT32-safe). With **Turbo**, split is done in streaming (no full archive on disk).
6. **Keep original archive after split** — If split is on, you can keep the full archive file as well as the parts.
7. Click **Start**, confirm the recap, then wait. Use **Cancel** to stop and remove partial output.
8. When done, use **Open output folder** if you want to see the files.

**Merge parts (rejoin split files):** After you’ve copied part files to another disk or PC, click **Merge parts**, choose any part file (e.g. `name.tar.part-001`). The app finds all parts in that folder, checks they are contiguous (001, 002, 003…), and writes one archive (e.g. `name.tar`) in the same folder. Works the same on Windows and Linux (no `cat` or `copy /b` needed). Then extract with `tar -xf` or 7-Zip.

## Output names

| Mode        | File(s)                    |
|------------|----------------------------|
| Fast       | `name.tar`                 |
| Compressed | `name.tar.gz`              |
| Turbo      | `name.tar` (or parts only when split in streaming) |
| Split      | `name.tar.part-001`, `name.tar.part-002`, … (or `name.tar.gz.part-001`, …) |

## Turbo mode and diagnostics

- **Turbo** uses the system `tar` command (GNU tar on Linux, `tar` on Windows 10+). It is much faster than the Python engine on large or many-file sources, and **Cancel** stops the process immediately and cleans partial output.
- **Progress**: Turbo (single file) = size of the `.tar`; Turbo (streaming split) = sum of bytes written to the part files.
- **Windows**: If the system `tar` is incompatible (e.g. different `-C` behaviour), Turbo is disabled at startup or a clear error suggests using "Fast (no compression)".
- The log shows **file count**, **total size**, and **filesystem type** (Source FS / Output FS) to help diagnose slow runs (e.g. NTFS/FUSE).
- Archives use **relative paths** only (one top-level directory, e.g. `backup_2026/...`); no absolute or `..` paths.

## Rejoin / extract

- **Merge parts in the app**  
  Click **Merge parts**, select any part file (e.g. `backup_2026.tar.part-001`). The app discovers all parts in that directory (they must be named `name.part-001`, `name.part-002`, … with no gaps), concatenates them in order, and writes the full archive (e.g. `backup_2026.tar`) in the same folder. Progress and Cancel work like when creating an archive. Same behaviour on Windows and Linux. Then extract the merged file with `tar` or 7-Zip.

- **Extract a single archive**  
  Linux/macOS: `tar -xf name.tar` or `tar -xzf name.tar.gz`  
  Windows: 7-Zip, WinRAR, or `tar -xf name.tar` (if tar is installed).

- **Rejoin split parts manually (without the app)**  
  Linux/macOS: `cat name.tar.part-* > name.tar` then `tar -xf name.tar`  
  Windows: `copy /b name.tar.part-001+name.tar.part-002+... name.tar` (order matters), then extract with 7-Zip or similar.

## Packaging (optional)

- **Ubuntu**: Create an AppImage or use PyInstaller from the project root (add a spec that includes `src` and launches `src.main`).
- **Windows**: Build an exe with PyInstaller, e.g. `pyinstaller --onefile --windowed -n "FastArchive" src/main.py` (adjust so that `src` package is included and the entry point is correct).

## License

Open source: **GNU General Public License v3.0 (GPL-3.0)**. See [LICENSE](LICENSE).

---

**Developer:** Omar Ettalbi, SWE
