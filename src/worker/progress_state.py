"""
Shared progress state: phase, files_done, bytes_done, etc.
Worker sends snapshots via queue; UI uses them and computes speed/ETA from start time.
"""
from dataclasses import dataclass


@dataclass
class ProgressState:
    """Snapshot for UI updates."""

    phase: str  # "scan" | "archive" | "split" | "done" | "error" | "cancelled"
    files_done: int = 0
    files_total: int = 0
    bytes_done: int = 0
    bytes_total: int = 0
    part_index: int = 0
    message: str = ""
    output_paths: list[str] = None  # filled on "done"

    def __post_init__(self):
        if self.output_paths is None:
            self.output_paths = []
