"""
Detect filesystem type for a path (for diagnostics in logs).
"""
import os
import subprocess
import sys


def get_fs_type(path: str) -> str:
    """
    Return filesystem type for the mount containing path, e.g. 'ext4', 'ntfs'.
    Returns empty string if detection fails or is not supported.
    """
    if not path or not os.path.exists(path):
        return ""
    path = os.path.abspath(path)
    if os.path.isfile(path):
        path = os.path.dirname(path)
    if sys.platform == "win32":
        return _get_fs_type_windows(path)
    return _get_fs_type_linux(path)


def _get_fs_type_linux(path: str) -> str:
    try:
        r = subprocess.run(
            ["df", "-T", path],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if r.returncode != 0:
            return ""
        lines = r.stdout.strip().splitlines()
        if len(lines) < 2:
            return ""
        # Second line: device type mountpoint ...
        parts = lines[1].split()
        if len(parts) >= 2:
            return parts[1].lower()
        return ""
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return ""


def _get_fs_type_windows(path: str) -> str:
    # Get drive letter
    if len(path) >= 2 and path[1] == ":":
        drive = path[:2] + "\\"
    else:
        return ""
    try:
        import ctypes
        volume = ctypes.create_unicode_buffer(256)
        fs_name = ctypes.create_unicode_buffer(256)
        if ctypes.windll.kernel32.GetVolumeInformationW(  # type: ignore[attr-defined]
            drive, volume, 256, None, None, None, fs_name, 256
        ):
            return fs_name.value.lower()
    except (AttributeError, OSError):
        pass
    return ""
