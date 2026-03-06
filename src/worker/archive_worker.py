"""
Background worker: validate, scan, build TAR, optionally split; report progress via queue.
"""
import os
import queue
import threading
from typing import Callable

from ..archive.merge import merge_parts
from ..archive.split import split_file
from ..archive.tar_build import build_tar
from ..archive.tar_system import build_tar_system, build_tar_system_streaming
from ..utils.fs_type import get_fs_type
from ..utils.scan import scan_directory
from ..utils.validation import ValidationError, validate_inputs
from .progress_state import ProgressState


def run_archive_job(
    source_dir: str,
    output_dir: str,
    archive_name: str,
    *,
    compressed: bool = False,
    split_enabled: bool = False,
    chunk_mib: int = 3900,
    keep_original_after_split: bool = False,
    overwrite_existing: bool = False,
    turbo: bool = False,
    message_queue: queue.Queue,
    cancel_event: threading.Event,
) -> None:
    """
    Run in a separate thread. Puts (ProgressState, log_message) in message_queue.
    Keys: "state" -> ProgressState, "log" -> str. On done/error/cancelled, puts final state.
    """
    base = archive_name.strip()
    ext = ".tar.gz" if compressed else ".tar"
    archive_path = os.path.join(output_dir, base + ext)
    created_paths: list[str] = []

    def put(state: ProgressState, log: str = "") -> None:
        try:
            message_queue.put_nowait(("state", state))
            if log:
                message_queue.put_nowait(("log", log))
        except queue.Full:
            pass

    def cancel_check() -> bool:
        return cancel_event.is_set()

    def cleanup_partial() -> None:
        for p in created_paths:
            try:
                if os.path.exists(p):
                    os.remove(p)
            except OSError:
                pass

    try:
        put(ProgressState(phase="scan", message="Validating..."), "Validating inputs...")
        file_count, total_bytes = scan_directory(source_dir)
        validate_inputs(
            source_dir,
            output_dir,
            archive_name,
            estimated_bytes=total_bytes,
            require_disk_check=True,
        )

        if not overwrite_existing:
            if os.path.exists(archive_path):
                put(
                    ProgressState(phase="error", message="Output file already exists."),
                    f"Error: file already exists: {archive_path}",
                )
                return
            if split_enabled:
                for i in range(1, 1000):
                    p = os.path.join(output_dir, f"{base}{ext}.part-{i:03d}")
                    if os.path.exists(p):
                        put(
                            ProgressState(
                                phase="error", message="Output parts already exist."
                            ),
                            f"Error: part file exists: {p}",
                        )
                        return
        else:
            if os.path.exists(archive_path):
                try:
                    os.remove(archive_path)
                except OSError:
                    pass
            if split_enabled:
                for i in range(1, 1000):
                    p = os.path.join(output_dir, f"{base}{ext}.part-{i:03d}")
                    if os.path.exists(p):
                        try:
                            os.remove(p)
                        except OSError:
                            pass

        source_fs = get_fs_type(source_dir)
        output_fs = get_fs_type(output_dir)
        fs_note = ""
        if source_fs or output_fs:
            fs_note = f" [Source FS: {source_fs or '?'}, Output FS: {output_fs or '?'}]"
        put(
            ProgressState(
                phase="scan",
                files_total=file_count,
                bytes_total=total_bytes,
                message="Pre-scan complete.",
            ),
            f"Source: {file_count} files, {total_bytes // (1024*1024)} MiB.{fs_note}",
        )

        put(
            ProgressState(
                phase="archive",
                files_total=file_count,
                bytes_total=total_bytes,
                message="Creating archive..." + (" (Turbo)" if turbo else "") + "...",
            ),
            "Creating archive..." + (" (system tar)" if turbo else "") + "...",
        )

        def on_tar_progress(files_done: int, bytes_written: int) -> None:
            put(
                ProgressState(
                    phase="archive",
                    files_done=files_done,
                    files_total=file_count,
                    bytes_done=bytes_written,
                    bytes_total=total_bytes,
                    message="Archiving...",
                )
            )

        if turbo:
            # Turbo = system tar only (no compression). Cancel is immediate (kill process).
            if split_enabled:
                chunk_bytes = chunk_mib * 1024 * 1024
                parts = build_tar_system_streaming(
                    source_dir,
                    output_dir,
                    base + ".tar",
                    chunk_bytes,
                    on_progress=lambda written, part_num: put(
                        ProgressState(
                            phase="split",
                            bytes_done=written,
                            bytes_total=total_bytes,
                            part_index=part_num,
                            message="Streaming to parts...",
                        )
                    ),
                    cancel_check=cancel_check,
                )
                created_paths.extend(parts)
                put(
                    ProgressState(phase="done", message="Success.", output_paths=parts),
                    f"Success. Created (streaming): {', '.join(parts)}",
                )
            else:
                build_tar_system(
                    source_dir,
                    archive_path,
                    on_progress=on_tar_progress,
                    cancel_check=cancel_check,
                    bytes_total=total_bytes,
                    files_total=file_count,
                )
                created_paths.append(archive_path)
                put(
                    ProgressState(phase="done", message="Success.", output_paths=[archive_path]),
                    f"Success. Created: {archive_path}",
                )
        else:
            build_tar(
                source_dir,
                archive_path,
                compressed=compressed,
                on_progress=on_tar_progress,
                cancel_check=cancel_check,
                files_total=file_count,
            )
            created_paths.append(archive_path)

        if not turbo and split_enabled:
            put(
                ProgressState(phase="split", message="Splitting..."),
                "Splitting into chunks...",
            )
            chunk_bytes = chunk_mib * 1024 * 1024
            total_size = os.path.getsize(archive_path)

            def on_split_progress(written: int, part_num: int) -> None:
                put(
                    ProgressState(
                        phase="split",
                        bytes_done=written,
                        bytes_total=total_size,
                        part_index=part_num,
                        message="Splitting...",
                    )
                )

            parts = split_file(
                archive_path,
                output_dir,
                base + ext,
                chunk_bytes,
                on_progress=on_split_progress,
                cancel_check=cancel_check,
            )
            created_paths.extend(parts)
            if not keep_original_after_split:
                try:
                    os.remove(archive_path)
                except OSError:
                    pass
                output_paths = parts
            else:
                output_paths = [archive_path] + parts
            put(
                ProgressState(
                    phase="done",
                    message="Success.",
                    output_paths=output_paths,
                ),
                f"Success. Created: {', '.join(output_paths)}",
            )
        elif not turbo:
            put(
                ProgressState(
                    phase="done",
                    message="Success.",
                    output_paths=[archive_path],
                ),
                f"Success. Created: {archive_path}",
            )
    except InterruptedError as e:
        cleanup_partial()
        put(
            ProgressState(phase="cancelled", message=str(e)),
            "Cancelled by user.",
        )
    except OSError as e:
        if turbo:
            put(
                ProgressState(phase="error", message="System tar failed. Use Fast (no compression) instead."),
                f"System tar failed (incompatible?): {e}. Use format 'Fast (no compression)' as fallback.",
            )
        else:
            cleanup_partial()
            put(
                ProgressState(phase="error", message=str(e)),
                f"IO error: {e}",
            )
    except ValidationError as e:
        put(ProgressState(phase="error", message=str(e)), f"Validation error: {e}")
    except Exception as e:
        cleanup_partial()
        put(
            ProgressState(phase="error", message=str(e)),
            f"Error: {e}",
        )


def run_merge_job(
    part_paths: list[str],
    output_path: str,
    *,
    message_queue: queue.Queue,
    cancel_event: threading.Event,
) -> None:
    """
    Merge part files into a single output file. Run in a separate thread.
    Puts (ProgressState, log) in message_queue. On cancel/error, removes partial output.
    """
    created_paths: list[str] = [output_path]

    def put(state: ProgressState, log: str = "") -> None:
        try:
            message_queue.put_nowait(("state", state))
            if log:
                message_queue.put_nowait(("log", log))
        except queue.Full:
            pass

    def cancel_check() -> bool:
        return cancel_event.is_set()

    def cleanup_partial() -> None:
        for p in created_paths:
            try:
                if os.path.exists(p):
                    os.remove(p)
            except OSError:
                pass

    try:
        total_bytes = sum(os.path.getsize(p) for p in part_paths)
        put(
            ProgressState(
                phase="merge",
                bytes_total=total_bytes,
                message="Merging parts...",
            ),
            f"Merging {len(part_paths)} parts into {output_path}...",
        )

        def on_progress(bytes_done: int, part_index: int) -> None:
            put(
                ProgressState(
                    phase="merge",
                    bytes_done=bytes_done,
                    bytes_total=total_bytes,
                    part_index=part_index,
                    message="Merging...",
                )
            )

        merge_parts(
            part_paths,
            output_path,
            on_progress=on_progress,
            cancel_check=cancel_check,
        )
        put(
            ProgressState(phase="done", message="Success.", output_paths=[output_path]),
            f"Success. Merged to: {output_path}",
        )
    except InterruptedError as e:
        cleanup_partial()
        put(
            ProgressState(phase="cancelled", message=str(e)),
            "Cancelled by user.",
        )
    except OSError as e:
        cleanup_partial()
        put(
            ProgressState(phase="error", message=str(e)),
            f"IO error: {e}",
        )
    except Exception as e:
        cleanup_partial()
        put(
            ProgressState(phase="error", message=str(e)),
            f"Error: {e}",
        )
