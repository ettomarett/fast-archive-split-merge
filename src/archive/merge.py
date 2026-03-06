"""
Merge split archive parts back into a single file (e.g. .part-001, .part-002 -> .tar).
"""
import os
import re
from typing import Callable


CHUNK_READ_SIZE = 8 * 1024 * 1024  # 8 MiB

# Matches "anything.part-001", "name.tar.part-042"
PART_PATTERN = re.compile(r"^(.+)\.part-(\d{3})$")


def discover_parts_from_path(path: str) -> list[tuple[str, list[str]]]:
    """
    Discover part files from a path (file or directory).
    - If path is a file: treat as one of the parts; find all siblings matching same base.
    - If path is a directory: find all .part-NNN files and group by base name.
    Returns list of (base_name, sorted list of part paths). base_name is the stem before .part-NNN.
    """
    if not path or not os.path.exists(path):
        return []
    if os.path.isfile(path):
        directory = os.path.dirname(path)
        name = os.path.basename(path)
        m = PART_PATTERN.match(name)
        if not m:
            return []
        base = m.group(1)
        return _collect_parts_in_dir(directory, base)
    if os.path.isdir(path):
        # Group all .part-NNN in directory by base name
        by_base: dict[str, list[tuple[int, str]]] = {}
        for entry in os.listdir(path):
            m = PART_PATTERN.match(entry)
            if not m:
                continue
            base, num_str = m.group(1), m.group(2)
            full = os.path.join(path, entry)
            if not os.path.isfile(full):
                continue
            num = int(num_str, 10)
            by_base.setdefault(base, []).append((num, full))
        out: list[tuple[str, list[str]]] = []
        for base, pairs in by_base.items():
            pairs.sort(key=lambda x: x[0])
            part_paths = [p[1] for p in pairs]
            out.append((base, part_paths))
        out.sort(key=lambda x: x[0])
        return out
    return []


def _collect_parts_in_dir(directory: str, base: str) -> list[tuple[str, list[str]]]:
    """Find all base.part-NNN in directory and return [(base, [paths])]."""
    by_num: list[tuple[int, str]] = []
    for entry in os.listdir(directory):
        m = PART_PATTERN.match(entry)
        if not m or m.group(1) != base:
            continue
        full = os.path.join(directory, entry)
        if not os.path.isfile(full):
            continue
        by_num.append((int(m.group(2), 10), full))
    if not by_num:
        return []
    by_num.sort(key=lambda x: x[0])
    return [(base, [p[1] for p in by_num])]


def merge_parts(
    part_paths: list[str],
    output_path: str,
    *,
    on_progress: Callable[[int, int], None] | None = None,
    cancel_check: Callable[[], bool] | None = None,
) -> str:
    """
    Concatenate part_paths in order into output_path.
    Returns output_path. Raises InterruptedError if cancel_check returns True.
    """
    total_size = sum(os.path.getsize(p) for p in part_paths)
    written = 0
    with open(output_path, "wb") as out:
        for i, part_path in enumerate(part_paths):
            if cancel_check and cancel_check():
                raise InterruptedError("Cancelled by user")
            with open(part_path, "rb") as f:
                while True:
                    chunk = f.read(CHUNK_READ_SIZE)
                    if not chunk:
                        break
                    if cancel_check and cancel_check():
                        raise InterruptedError("Cancelled by user")
                    out.write(chunk)
                    written += len(chunk)
                    if on_progress:
                        on_progress(written, total_size)
    return output_path
