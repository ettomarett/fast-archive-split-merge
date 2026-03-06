"""
Merge split part files (e.g. name.tar.part-001, .part-002, ...) back into a single file.
Cross-platform: uses only Python binary I/O (no cat/copy).
"""
import os
import re
from typing import Callable

from .split import CHUNK_READ_SIZE

PART_SUFFIX_RE = re.compile(r"\.part-(\d+)$")


def discover_parts_from_path(one_part_path: str) -> list[str]:
    """
    From one part file path (e.g. .../backup_2026.tar.part-001), discover all parts
    in the same directory with the same base name. Returns paths in order (001, 002, ...).
    Raises ValueError if the path is not a valid part file, no other parts found,
    or part numbers are not contiguous (e.g. 001, 003, missing 002).
    """
    one_part_path = os.path.abspath(one_part_path)
    if not os.path.isfile(one_part_path):
        raise ValueError(f"Not a file: {one_part_path}")

    directory = os.path.dirname(one_part_path)
    basename = os.path.basename(one_part_path)
    match = PART_SUFFIX_RE.search(basename)
    if not match:
        raise ValueError(
            f"File name does not match part pattern (.part-NNN): {basename}"
        )
    base = basename[: match.start()]
    prefix = base + ".part-"

    # Collect all part files in the same directory
    indexed: list[tuple[int, str]] = []
    for name in os.listdir(directory):
        if not name.startswith(prefix):
            continue
        suffix = name[len(prefix) :]
        if not suffix.isdigit():
            continue
        num = int(suffix)
        full = os.path.join(directory, name)
        if os.path.isfile(full):
            indexed.append((num, full))

    if not indexed:
        raise ValueError(f"No part files found in {directory} for base {base!r}")

    indexed.sort(key=lambda x: x[0])
    part_paths = [p for _, p in indexed]
    nums = [n for n, _ in indexed]

    # Require contiguous 1..N
    expected = list(range(1, len(nums) + 1))
    if nums != expected:
        missing = set(expected) - set(nums)
        if missing:
            raise ValueError(
                f"Missing part number(s): {sorted(missing)}. Found: {nums}"
            )
        extra = set(nums) - set(expected)
        if extra:
            raise ValueError(f"Unexpected part number(s): {sorted(extra)}. Expected 1..{len(nums)}.")

    return part_paths


def merge_parts(
    part_paths: list[str],
    output_path: str,
    *,
    on_progress: Callable[[int, int], None] | None = None,
    cancel_check: Callable[[], bool] | None = None,
) -> str:
    """
    Concatenate part files in order into output_path. Uses chunked read/write.
    on_progress(total_bytes_written, current_part_index) and cancel_check() are
    called during the copy. On cancel, raises InterruptedError.
    Returns output_path.
    """
    total_written = 0
    with open(output_path, "wb") as out:
        for part_index, part_path in enumerate(part_paths, start=1):
            if cancel_check and cancel_check():
                raise InterruptedError("Cancelled by user")
            with open(part_path, "rb") as f:
                while True:
                    if cancel_check and cancel_check():
                        raise InterruptedError("Cancelled by user")
                    chunk = f.read(CHUNK_READ_SIZE)
                    if not chunk:
                        break
                    out.write(chunk)
                    total_written += len(chunk)
                    if on_progress:
                        on_progress(total_written, part_index)
    return output_path
