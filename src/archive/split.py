"""
Split a file into fixed-size parts (e.g. FAT32-safe 3900 MiB).
"""
import os
from typing import Callable


CHUNK_READ_SIZE = 8 * 1024 * 1024  # 8 MiB per read


def split_file(
    input_path: str,
    output_dir: str,
    base_name: str,
    chunk_size_bytes: int,
    *,
    on_progress: Callable[[int, int], None] | None = None,
    cancel_check: Callable[[], bool] | None = None,
) -> list[str]:
    """
    Split input_path into parts of chunk_size_bytes, written to output_dir.
    Naming: base_name.part-001, base_name.part-002, ...
    Returns list of created part paths.
    """
    part_paths: list[str] = []
    try:
        total_written = 0
        part_index = 1
        part_written = 0
        part_path = os.path.join(output_dir, f"{base_name}.part-{part_index:03d}")
        part_paths.append(part_path)
        part_file = open(part_path, "wb")

        with open(input_path, "rb") as src:
            while True:
                if cancel_check and cancel_check():
                    raise InterruptedError("Cancelled by user")
                chunk = src.read(min(CHUNK_READ_SIZE, chunk_size_bytes - part_written))
                if not chunk:
                    break
                part_file.write(chunk)
                part_written += len(chunk)
                total_written += len(chunk)
                if on_progress:
                    on_progress(total_written, part_index)
                if part_written >= chunk_size_bytes:
                    part_file.close()
                    part_index += 1
                    part_written = 0
                    part_path = os.path.join(
                        output_dir, f"{base_name}.part-{part_index:03d}"
                    )
                    part_paths.append(part_path)
                    part_file = open(part_path, "wb")

        part_file.close()
        # Last part might be empty if input size was exact multiple of chunk_size
        if part_written == 0 and part_paths:
            last_path = part_paths.pop()
            try:
                os.remove(last_path)
            except OSError:
                pass
        return [p for p in part_paths if os.path.exists(p)]
    except Exception:
        for p in part_paths:
            try:
                if os.path.exists(p):
                    os.remove(p)
            except OSError:
                pass
        raise