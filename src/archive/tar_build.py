"""
Create TAR archive (optionally gzip) with progress reporting via a counting file wrapper.
Uses a single tar.add(source_dir) for maximum speed (avoids per-file Python overhead).
"""
import os
import tarfile
from typing import Callable

# 8 MiB write buffer for better sequential throughput
WRITE_BUFFER_SIZE = 8 * 1024 * 1024
# Report progress every N bytes to avoid flooding the UI
PROGRESS_THROTTLE_BYTES = 2 * 1024 * 1024  # 2 MiB


class CountingFileWrapper:
    """Wraps a file object and calls on_write with (bytes_written,) after each write."""

    def __init__(self, fileobj, on_write: Callable[[int], None]):
        self._fileobj = fileobj
        self._on_write = on_write
        self._total = 0

    def write(self, data: bytes) -> int:
        n = self._fileobj.write(data)
        if n:
            self._total += n
            self._on_write(n)
        return n

    def tell(self) -> int:
        return self._total

    def flush(self) -> None:
        self._fileobj.flush()

    def close(self) -> None:
        self._fileobj.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def build_tar(
    source_dir: str,
    output_path: str,
    *,
    compressed: bool = False,
    on_progress: Callable[[int, int], None] | None = None,
    cancel_check: Callable[[], bool] | None = None,
    files_total: int = 0,
) -> None:
    """
    Create a TAR archive at output_path from source_dir.
    Uses a single tar.add(source_dir) for maximum speed.
    - compressed: use gzip (output_path should end with .tar.gz).
    - on_progress(files_done, bytes_written) called periodically (throttled by bytes).
    - cancel_check() checked before/after the archive; not during (for speed).
    - files_total: used for progress display (files_done set to files_total when done).
    """
    mode = "w:gz" if compressed else "w"
    arcname = os.path.basename(os.path.normpath(source_dir))
    if not arcname:
        arcname = "archive"

    bytes_written = [0]
    last_reported_bytes = [0]

    def on_write(n: int) -> None:
        bytes_written[0] += n
        if on_progress and (bytes_written[0] - last_reported_bytes[0]) >= PROGRESS_THROTTLE_BYTES:
            last_reported_bytes[0] = bytes_written[0]
            # files_done unknown during run; we pass 0, UI shows bytes/speed/ETA
            on_progress(0, bytes_written[0])

    if cancel_check and cancel_check():
        raise InterruptedError("Cancelled by user")

    with open(output_path, "wb", buffering=WRITE_BUFFER_SIZE) as raw_f:
        wrapper = CountingFileWrapper(raw_f, on_write)
        with tarfile.open(output_path, mode=mode, fileobj=wrapper) as tar:
            # Single add of entire tree: much faster than file-by-file (avoids Python loop overhead)
            tar.add(source_dir, arcname=arcname, recursive=True)

    if cancel_check and cancel_check():
        raise InterruptedError("Cancelled by user")
    if on_progress:
        on_progress(files_total or 0, bytes_written[0])