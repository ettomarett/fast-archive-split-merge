"""
Turbo mode: use system GNU tar via subprocess for maximum speed.
Supports immediate cancel (kill process) and optional streaming split.

DoD progress: Turbo (file) = size of .tar; Turbo (streaming) = sum of bytes written to parts.
"""
import os
import subprocess
import tempfile
import time
from typing import Callable

# 8 MiB: reduces write syscalls in streaming; avoids Python as bottleneck (revue finale §2)
CHUNK_READ_SIZE = 8 * 1024 * 1024
WRITE_BUFFER_SIZE = 8 * 1024 * 1024  # same for part files
PROGRESS_POLL_INTERVAL = 0.25  # seconds when polling file size


def _tar_creation_flags():
    return subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0


def _tar_cmd_prefix() -> list[str]:
    """On Linux, use ionice for more stable I/O when system is busy (optional)."""
    if os.name != "nt":
        try:
            if subprocess.run(["ionice", "-c2", "-n0", "true"], capture_output=True, timeout=2).returncode == 0:
                return ["ionice", "-c2", "-n0"]
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            pass
    return []


# Command to run tar (set by is_system_tar_available so we use the same executable everywhere)
_tar_cmd: list[str] = ["tar"]


def _probe_tar_compatible(tar_cmd: list[str] | None = None) -> bool:
    """Run a minimal tar -cf -C parent arcname; required for Windows (BS tar) compatibility."""
    cmd = tar_cmd if tar_cmd is not None else _tar_cmd
    try:
        with tempfile.TemporaryDirectory() as td:
            parent = os.path.dirname(td)
            arcname = os.path.basename(td)
            out = os.path.join(parent, "._tar_probe_out.tar")
            try:
                r = subprocess.run(
                    _tar_cmd_prefix() + cmd + ["-cf", out, "-C", parent, arcname],
                    capture_output=True,
                    timeout=10,
                    creationflags=_tar_creation_flags(),
                )
                return r.returncode == 0
            finally:
                if os.path.exists(out):
                    try:
                        os.remove(out)
                    except OSError:
                        pass
    except Exception:
        return False


def _try_tar_available(cmd: list[str], skip_version_check: bool = False) -> bool:
    """Return True if tar at cmd runs and passes the compatibility probe."""
    try:
        if not skip_version_check:
            r = subprocess.run(
                cmd + ["--version"],
                capture_output=True,
                timeout=5,
                creationflags=_tar_creation_flags(),
            )
            if r.returncode != 0:
                return False
        return _probe_tar_compatible(cmd)
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False


def is_system_tar_available() -> bool:
    """True if system tar is available and compatible (-C / arcname). On Windows, try PATH then System32."""
    global _tar_cmd
    if _try_tar_available(["tar"]):
        _tar_cmd = ["tar"]
        return True
    if os.name == "nt":
        systemroot = os.environ.get("SystemRoot", "C:\\Windows")
        win_tar = os.path.join(systemroot, "System32", "tar.exe")
        if os.path.isfile(win_tar):
            if _try_tar_available([win_tar]):
                _tar_cmd = [win_tar]
                return True
            # BSD tar on Windows may not support --version; try probe only
            if _try_tar_available([win_tar], skip_version_check=True):
                _tar_cmd = [win_tar]
                return True
    return False


def build_tar_system(
    source_dir: str,
    output_path: str,
    *,
    on_progress: Callable[[int, int], None] | None = None,
    cancel_check: Callable[[], bool] | None = None,
    bytes_total: int = 0,
    files_total: int = 0,
) -> None:
    """
    Create a TAR archive using system tar (no compression).
    Progress is reported by polling output file size. Cancel = terminate process immediately.
    """
    source_dir = os.path.normpath(os.path.abspath(source_dir))
    parent = os.path.dirname(source_dir)
    arcname = os.path.basename(source_dir) or "archive"

    if cancel_check and cancel_check():
        raise InterruptedError("Cancelled by user")

    proc = subprocess.Popen(
        _tar_cmd_prefix() + _tar_cmd + ["-cf", output_path, "-C", parent, arcname],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        creationflags=_tar_creation_flags(),
    )

    try:
        while proc.poll() is None:
            if cancel_check and cancel_check():
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                raise InterruptedError("Cancelled by user")
            if on_progress and os.path.exists(output_path):
                try:
                    written = os.path.getsize(output_path)
                    on_progress(files_total, written)
                except OSError:
                    pass
            time.sleep(PROGRESS_POLL_INTERVAL)

        if proc.returncode != 0:
            err = (proc.stderr and proc.stderr.read()) or b""
            raise OSError(f"tar exited with code {proc.returncode}: {err.decode(errors='replace')}")

        if on_progress:
            written = os.path.getsize(output_path) if os.path.exists(output_path) else 0
            on_progress(files_total, written)
    finally:
        if proc.stderr:
            proc.stderr.close()


def _write_stream_to_parts(
    stream,
    output_dir: str,
    base_name: str,
    chunk_size_bytes: int,
    *,
    on_progress: Callable[[int, int], None] | None = None,
    cancel_check: Callable[[], bool] | None = None,
) -> list[str]:
    """Read from stream (tar stdout), write to part files. Progress = sum of bytes written to parts (DoD §1)."""
    part_paths: list[str] = []
    part_index = 1
    part_written = 0
    total_written = 0
    part_path = os.path.join(output_dir, f"{base_name}.part-{part_index:03d}")
    part_paths.append(part_path)
    part_file = open(part_path, "wb", buffering=WRITE_BUFFER_SIZE)
    try:
        while True:
            if cancel_check and cancel_check():
                raise InterruptedError("Cancelled by user")
            to_read = min(CHUNK_READ_SIZE, chunk_size_bytes - part_written)
            chunk = stream.read(to_read)
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
                part_path = os.path.join(output_dir, f"{base_name}.part-{part_index:03d}")
                part_paths.append(part_path)
                part_file = open(part_path, "wb", buffering=WRITE_BUFFER_SIZE)
        part_file.close()
        if part_written == 0 and part_paths:
            last = part_paths.pop()
            try:
                os.remove(last)
            except OSError:
                pass
        return [p for p in part_paths if os.path.exists(p)]
    except InterruptedError:
        part_file.close()
        for p in part_paths:
            try:
                if os.path.exists(p):
                    os.remove(p)
            except OSError:
                pass
        raise
    except Exception:
        part_file.close()
        for p in part_paths:
            try:
                if os.path.exists(p):
                    os.remove(p)
            except OSError:
                pass
        raise


def build_tar_system_streaming(
    source_dir: str,
    output_dir: str,
    base_name: str,
    chunk_size_bytes: int,
    *,
    on_progress: Callable[[int, int], None] | None = None,
    cancel_check: Callable[[], bool] | None = None,
) -> list[str]:
    """
    Tar to stdout, write directly to part files (no full archive on disk).
    Returns list of part paths. Cancel = terminate tar process immediately.
    """
    source_dir = os.path.normpath(os.path.abspath(source_dir))
    parent = os.path.dirname(source_dir)
    arcname = os.path.basename(source_dir) or "archive"
    part_paths: list[str] = []

    if cancel_check and cancel_check():
        raise InterruptedError("Cancelled by user")

    proc = subprocess.Popen(
        _tar_cmd_prefix() + _tar_cmd + ["-cf", "-", "-C", parent, arcname],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=CHUNK_READ_SIZE,
        creationflags=_tar_creation_flags(),
    )
    try:
        part_paths = _write_stream_to_parts(
            proc.stdout,
            output_dir,
            base_name,
            chunk_size_bytes,
            on_progress=on_progress,
            cancel_check=cancel_check,
        )
        proc.stdout.close()
        proc.wait()
        if proc.returncode != 0:
            err = (proc.stderr and proc.stderr.read()) or b""
            raise OSError(f"tar exited with code {proc.returncode}: {err.decode(errors='replace')}")
        return part_paths
    except InterruptedError:
        proc.terminate()
        if proc.stdout:
            proc.stdout.close()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        raise
    finally:
        if proc.stderr:
            proc.stderr.close()
