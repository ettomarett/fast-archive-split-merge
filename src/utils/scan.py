"""
Pre-scan source directory: count files and total size for progress and ETA.
"""
import os
import stat


def scan_directory(source_dir: str, *, follow_symlinks: bool = False) -> tuple[int, int]:
    """
    Walk source directory and return (file_count, total_bytes).
    Symlinks are counted as 0 bytes unless follow_symlinks is True.
    """
    file_count = 0
    total_bytes = 0
    try:
        for entry in os.scandir(source_dir):
            try:
                if entry.is_symlink():
                    if follow_symlinks and entry.is_file(follow_symlinks=True):
                        total_bytes += entry.stat(follow_symlinks=True).st_size
                    file_count += 1
                elif entry.is_file():
                    try:
                        total_bytes += entry.stat().st_size
                    except OSError:
                        pass
                    file_count += 1
                elif entry.is_dir():
                    sub_count, sub_bytes = scan_directory(
                        entry.path, follow_symlinks=follow_symlinks
                    )
                    file_count += sub_count
                    total_bytes += sub_bytes
            except OSError:
                continue
    except OSError:
        pass
    return file_count, total_bytes
