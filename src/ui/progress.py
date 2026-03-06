"""
Progress bar, status labels (files, bytes, speed, ETA), and log area.
"""
import time

import customtkinter as ctk


class ProgressFrame(ctk.CTkFrame):
    """Progress bar + labels + scrollable log. Updated from main thread via set_state()."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._job_start_time: float | None = None

        self._lbl_status = ctk.CTkLabel(self, text="Ready.")
        self._lbl_status.pack(anchor="w", padx=4, pady=2)

        self._lbl_files = ctk.CTkLabel(self, text="Files: — / —")
        self._lbl_files.pack(anchor="w", padx=4, pady=2)

        self._lbl_bytes = ctk.CTkLabel(self, text="Bytes: — / —")
        self._lbl_bytes.pack(anchor="w", padx=4, pady=2)

        self._lbl_speed = ctk.CTkLabel(self, text="Speed: — MB/s  ETA: —")
        self._lbl_speed.pack(anchor="w", padx=4, pady=2)

        self._progress = ctk.CTkProgressBar(self, mode="determinate", width=400)
        self._progress.set(0)
        self._progress.pack(fill="x", padx=4, pady=6)

        log_label = ctk.CTkLabel(self, text="Log", anchor="w")
        log_label.pack(anchor="w", padx=4, pady=(8, 2))
        self._log = ctk.CTkTextbox(self, height=160, wrap="word", state="disabled")
        self._log.pack(fill="both", expand=True, padx=4, pady=4)

    def start_job(self) -> None:
        self._job_start_time = time.monotonic()

    def set_state(self, phase: str, files_done: int = 0, files_total: int = 0,
                  bytes_done: int = 0, bytes_total: int = 0, message: str = "") -> None:
        self._lbl_status.configure(text=message or phase)
        if files_total > 0:
            self._lbl_files.configure(text=f"Files: {files_done} / {files_total}")
        if bytes_total > 0:
            mb_done = bytes_done / (1024 * 1024)
            mb_total = bytes_total / (1024 * 1024)
            self._lbl_bytes.configure(text=f"Bytes: {mb_done:.1f} / {mb_total:.1f} MiB")
            if self._job_start_time is not None:
                elapsed = time.monotonic() - self._job_start_time
                if elapsed > 0 and bytes_done > 0:
                    speed_mbs = (bytes_done / (1024 * 1024)) / elapsed
                    eta_s = (bytes_total - bytes_done) / (bytes_done / elapsed) if bytes_done else None
                    eta_str = f"{eta_s:.0f}s" if eta_s is not None else "—"
                    self._lbl_speed.configure(text=f"Speed: {speed_mbs:.1f} MB/s  ETA: {eta_str}")
                else:
                    self._lbl_speed.configure(text="Speed: — MB/s  ETA: —")
            pct = 100 * bytes_done / bytes_total if bytes_total else 0
            self._progress.set(min(1.0, pct / 100))
        if phase in ("done", "error", "cancelled"):
            self._progress.set(1.0 if phase == "done" else 0)

    def log(self, text: str) -> None:
        self._log.configure(state="normal")
        self._log.insert("end", text + "\n")
        self._log.see("end")
        self._log.configure(state="disabled")

    def clear_log(self) -> None:
        self._log.configure(state="normal")
        self._log.delete("1.0", "end")
        self._log.configure(state="disabled")
