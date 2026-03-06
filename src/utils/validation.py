"""
Validation: paths, disk space, permissions, archive name.
"""
import os
import shutil


class ValidationError(Exception):
    """Raised when user inputs or environment fail validation."""

    pass


def _ensure_dir(path: str, must_exist: bool, must_write: bool, label: str) -> None:
    if not path or not path.strip():
        raise ValidationError(f"{label}: path is empty.")
    path = os.path.normpath(path)
    if not os.path.exists(path):
        if must_exist:
            raise ValidationError(f"{label}: path does not exist: {path}")
        return
    if not os.path.isdir(path):
        raise ValidationError(f"{label}: path is not a directory: {path}")
    if must_write:
        test_file = os.path.join(path, ".fast_archive_write_test")
        try:
            with open(test_file, "w"):
                pass
            os.remove(test_file)
        except OSError as e:
            raise ValidationError(f"{label}: cannot write to directory: {e}") from e


def _check_disk_space(output_dir: str, required_bytes: int, margin_ratio: float = 1.2) -> None:
    usage = shutil.disk_usage(output_dir)
    required_with_margin = int(required_bytes * margin_ratio)
    if usage.free < required_with_margin:
        raise ValidationError(
            f"Not enough disk space in output folder. "
            f"Free: {usage.free // (1024**3)} GiB, "
            f"required (with margin): {required_with_margin // (1024**3)} GiB."
        )


def _validate_archive_name(name: str) -> None:
    if not name or not name.strip():
        raise ValidationError("Archive name is empty.")
    base = name.strip()
    if os.path.sep in base or (os.path.altsep and os.path.altsep in base):
        raise ValidationError("Archive name must not contain path separators.")
    invalid = set('<>:"|?*')
    if any(c in base for c in invalid):
        raise ValidationError(f"Archive name contains invalid characters: {invalid}")


def validate_inputs(
    source_dir: str,
    output_dir: str,
    archive_name: str,
    *,
    estimated_bytes: int = 0,
    require_disk_check: bool = True,
) -> None:
    """
    Validate source, output, and archive name.
    If estimated_bytes > 0 and require_disk_check, checks free space in output_dir.
    """
    _ensure_dir(source_dir, must_exist=True, must_write=False, label="Source folder")
    _ensure_dir(output_dir, must_exist=True, must_write=True, label="Output folder")
    _validate_archive_name(archive_name)
    if require_disk_check and estimated_bytes > 0:
        _check_disk_space(output_dir, estimated_bytes)
