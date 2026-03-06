# Fast Archive Split Merge

Desktop application (Python 3.10+) to create TAR archives quickly, with optional gzip compression and optional split into FAT32-safe chunks (~4 GB). Merge split parts back into a single archive from the same UI. Modern look on Windows and Linux (CustomTkinter).

**Developer:** Omar Ettalbi, SWE

![Fast Archive & Split](https://github.com/ettomarett/fast-archive-split-merge/raw/main/assets/screenshot.png)

## Install

- **Python 3.10+** with Tkinter (on Ubuntu/Debian install `python3-tk` if needed; on Windows use the official installer and ensure "tcl/tk" is selected).
- **CustomTkinter** for the modern UI (rounded corners, consistent look on Windows and Linux).

```bash
# From the project root:
pip install -r requirements.txt

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

1. **Source Folder** — Choose the folder to archive.
2. **Output Folder** — Choose where to write the archive (and parts, if split).
3. **Archive Name** — Base name only (e.g. `backup_2026`). Extension is added automatically (`.tar` or `.tar.gz`).
4. **Format** — **Fast (no compression)** (Python), **Compressed (gzip)**, or **Turbo (system tar)** when available (uses the system `tar` binary for maximum speed; cancel is immediate).
5. **Split** — Enable "Split into chunks" and set chunk size (default 3900 MiB, FAT32-safe). With **Turbo**, split is done in streaming (no full archive on disk).
6. **Keep original archive after split** — If split is on, you can keep the full archive file as well as the parts.
7. Click **Start**, confirm the recap, then wait. Use **Cancel** to stop and remove partial output.
8. When done, use **Open output folder** if you want to see the files.

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

- **Merge split parts in the app**  
  Click **Merge parts**, select any part file (e.g. `name.tar.part-001`). The app discovers all parts in the same folder and writes the merged archive there. Works on Windows and Linux (no `cat` or `copy /b` needed).

- **Extract a single archive**  
  Linux/macOS: `tar -xf name.tar` or `tar -xzf name.tar.gz`  
  Windows: 7-Zip, WinRAR, or `tar -xf name.tar` (if tar is installed).

- **Rejoin split parts manually**  
  Linux/macOS: `cat name.tar.part-* > name.tar` then `tar -xf name.tar`  
  Windows: `copy /b name.tar.part-001+name.tar.part-002+... name.tar` (order matters), then extract with 7-Zip or similar.

## Packaging (optional)

- **Ubuntu**: Create an AppImage or use PyInstaller from the project root (add a spec that includes `src` and launches `src.main`).
- **Windows**: Build an exe with PyInstaller, e.g. `pyinstaller --onefile --windowed -n "FastArchive" src/main.py` (adjust so that `src` package is included and the entry point is correct).

## Repository (create and push)

To create a new **private** GitHub repo named **fast archive split merge** and push this project using SSH:

1. **Create the repo on GitHub**  
   GitHub → New repository → Name: `fast-archive-split-merge` (or `fast archive split merge`) → Private → Create (do not add README or .gitignore).

2. **Use the SSH key** (e.g. from `git_ssh.txt`)  
   Save only the key block (lines starting with `-----BEGIN OPENSSH PRIVATE KEY-----` through `-----END OPENSSH PRIVATE KEY-----`) to a file, e.g. `github_key`.  
   On Linux/macOS: `chmod 600 github_key`.

3. **Init, commit, and push** (replace `YOUR_GITHUB_USER` with your GitHub username):

   ```bash
   cd "path/to/fast archive app"
   git init
   git add .
   git commit -m "Initial commit: Fast Archive Split Merge"
   git remote add origin git@github.com:YOUR_GITHUB_USER/fast-archive-split-merge.git
   export GIT_SSH_COMMAND="ssh -i github_key -o IdentitiesOnly=yes"
   git branch -M main
   git push -u origin main
   ```

   On Windows (PowerShell):

   ```powershell
   $env:GIT_SSH_COMMAND = "ssh -i C:\path\to\github_key -o IdentitiesOnly=yes"
   git push -u origin main
   ```

## License

Open source: **GNU General Public License v3.0 (GPL-3.0)**. See [LICENSE](LICENSE).
