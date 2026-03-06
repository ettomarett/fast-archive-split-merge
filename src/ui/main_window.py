"""
Main window: source/output folders, archive name, format, split options, Start/Cancel, progress.
"""
import os
import queue
import re
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk

from .progress import ProgressFrame
from .theme import ENTRY_WIDTH_PX, PAD_X, PAD_Y
from ..archive.merge import discover_parts_from_path
from ..archive.tar_system import is_system_tar_available
from ..worker.archive_worker import run_archive_job, run_merge_job
from ..worker.progress_state import ProgressState


def open_output_folder(path: str) -> None:
    """Open the output folder in the system file manager."""
    folder = os.path.dirname(path) if os.path.isfile(path) else path
    if not os.path.isdir(folder):
        return
    if sys.platform == "win32":
        os.startfile(folder)
    else:
        import subprocess
        try:
            subprocess.run(["xdg-open", folder], check=False)
        except FileNotFoundError:
            try:
                subprocess.run(["nautilus", folder], check=False)
            except FileNotFoundError:
                pass


class MainWindow:
    def __init__(self, root: ctk.CTk):
        self.root = root
        self.root.title("Fast Archive & Split")
        self._message_queue: queue.Queue = queue.Queue()
        self._cancel_event = threading.Event()
        self._worker_thread: threading.Thread | None = None
        self._poll_id: str | None = None

        main = ctk.CTkFrame(root, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=14, pady=14)
        main.grid_columnconfigure(1, weight=1)
        grid_pad = {"padx": PAD_X, "pady": PAD_Y}

        # Source folder
        ctk.CTkLabel(main, text="Source Folder:").grid(row=0, column=0, sticky="w", **grid_pad)
        self._source_var = tk.StringVar()
        self._source_entry = ctk.CTkEntry(main, textvariable=self._source_var, state="disabled", width=ENTRY_WIDTH_PX)
        self._source_entry.grid(row=0, column=1, sticky="ew", **grid_pad)
        ctk.CTkButton(main, text="Browse…", width=100, command=self._browse_source).grid(row=0, column=2, **grid_pad)

        # Output folder
        ctk.CTkLabel(main, text="Output Folder:").grid(row=1, column=0, sticky="w", **grid_pad)
        self._output_var = tk.StringVar()
        self._output_entry = ctk.CTkEntry(main, textvariable=self._output_var, state="disabled", width=ENTRY_WIDTH_PX)
        self._output_entry.grid(row=1, column=1, sticky="ew", **grid_pad)
        ctk.CTkButton(main, text="Browse…", width=100, command=self._browse_output).grid(row=1, column=2, **grid_pad)

        # Archive name
        ctk.CTkLabel(main, text="Archive Name:").grid(row=2, column=0, sticky="w", **grid_pad)
        self._name_var = tk.StringVar(value="backup_2026")
        ctk.CTkEntry(main, textvariable=self._name_var, width=220).grid(row=2, column=1, sticky="w", **grid_pad)

        # Format
        ctk.CTkLabel(main, text="Format:").grid(row=3, column=0, sticky="w", **grid_pad)
        format_frame = ctk.CTkFrame(main, fg_color="transparent")
        format_frame.grid(row=3, column=1, columnspan=2, sticky="w", **grid_pad)
        self._format_var = tk.StringVar(value="fast")
        ctk.CTkRadioButton(format_frame, text="Fast (no compression)", variable=self._format_var, value="fast").pack(side="left", padx=(0, 12))
        ctk.CTkRadioButton(format_frame, text="Compressed (gzip)", variable=self._format_var, value="gzip").pack(side="left", padx=(0, 12))
        self._turbo_available = is_system_tar_available()
        self._radio_turbo = ctk.CTkRadioButton(
            format_frame,
            text="Turbo (system tar)",
            variable=self._format_var,
            value="turbo",
            state="normal" if self._turbo_available else "disabled",
        )
        self._radio_turbo.pack(side="left", padx=(0, 12))
        if not self._turbo_available:
            ctk.CTkLabel(format_frame, text="(tar not found)", text_color="gray").pack(side="left")

        # Split
        self._split_var = tk.BooleanVar(value=False)
        self._chunk_var = tk.StringVar(value="3900")
        self._keep_original_var = tk.BooleanVar(value=False)
        ctk.CTkLabel(main, text="Split:").grid(row=4, column=0, sticky="w", **grid_pad)
        split_frame = ctk.CTkFrame(main, fg_color="transparent")
        split_frame.grid(row=4, column=1, columnspan=2, sticky="w", **grid_pad)
        ctk.CTkCheckBox(split_frame, text="Split into chunks", variable=self._split_var).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(split_frame, text="Chunk size (MiB):").pack(side="left", padx=(0, 4))
        ctk.CTkEntry(split_frame, textvariable=self._chunk_var, width=80).pack(side="left", padx=(0, 8))
        ctk.CTkCheckBox(split_frame, text="Keep original archive after split", variable=self._keep_original_var).pack(side="left")

        # Buttons
        btn_frame = ctk.CTkFrame(main, fg_color="transparent")
        btn_frame.grid(row=5, column=0, columnspan=3, pady=10)
        self._btn_start = ctk.CTkButton(btn_frame, text="Start", command=self._on_start, width=120, fg_color=("#2563eb", "#1d4ed8"))
        self._btn_start.pack(side="left", padx=4)
        self._btn_merge = ctk.CTkButton(btn_frame, text="Merge parts", command=self._on_merge, width=120, fg_color=("#2563eb", "#1d4ed8"))
        self._btn_merge.pack(side="left", padx=4)
        self._btn_cancel = ctk.CTkButton(btn_frame, text="Cancel", command=self._on_cancel, width=100, state="disabled")
        self._btn_cancel.pack(side="left", padx=4)
        self._btn_open_folder = ctk.CTkButton(btn_frame, text="Open output folder", command=self._open_output, width=140, state="disabled")
        self._btn_open_folder.pack(side="left", padx=4)

        # Progress + log
        self._progress_frame = ProgressFrame(main)
        self._progress_frame.grid(row=6, column=0, columnspan=3, sticky="nsew", **grid_pad)
        main.rowconfigure(6, weight=1)

        self._last_output_paths: list[str] = []

    def _browse_source(self) -> None:
        path = filedialog.askdirectory(title="Select source folder")
        if path:
            self._source_var.set(path)

    def _browse_output(self) -> None:
        path = filedialog.askdirectory(title="Select output folder")
        if path:
            self._output_var.set(path)

    def _open_output(self) -> None:
        if self._last_output_paths:
            open_output_folder(self._last_output_paths[0])

    def _on_start(self) -> None:
        source = self._source_var.get().strip()
        output = self._output_var.get().strip()
        name = self._name_var.get().strip()
        if not source:
            messagebox.showerror("Error", "Please select a source folder.")
            return
        if not output:
            messagebox.showerror("Error", "Please select an output folder.")
            return
        if not name:
            messagebox.showerror("Error", "Please enter an archive name.")
            return
        try:
            chunk_mib = int(self._chunk_var.get())
            if chunk_mib < 1 or chunk_mib > 4096:
                raise ValueError("Chunk size must be between 1 and 4096 MiB")
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return

        # Recap
        fmt = self._format_var.get()
        mode = "Turbo (system tar)" if fmt == "turbo" else ("Compressed (gzip)" if fmt == "gzip" else "Fast (no compression)")
        split_yes = "Yes" if self._split_var.get() else "No"
        recap = (
            f"Source: {source}\n"
            f"Output: {output}\n"
            f"Archive name: {name}\n"
            f"Mode: {mode}\n"
            f"Split: {split_yes}"
        )
        if self._split_var.get():
            recap += f"\nChunk size: {chunk_mib} MiB"
        if not messagebox.askyesno("Confirm", recap + "\n\nStart?"):
            return

        # Check overwrite (Turbo = .tar only)
        fmt = self._format_var.get()
        ext = ".tar.gz" if fmt == "gzip" else ".tar"
        archive_path = os.path.join(output, name + ext)
        overwrite = False
        existing = []
        if os.path.exists(archive_path):
            existing.append(archive_path)
        if self._split_var.get():
            for i in range(1, 1000):
                p = os.path.join(output, f"{name}{ext}.part-{i:03d}")
                if os.path.exists(p):
                    existing.append(p)
        if existing:
            overwrite = messagebox.askyesno(
                "Overwrite",
                f"Output file(s) already exist:\n{existing[0]}{' ...' if len(existing) > 1 else ''}\nOverwrite?",
            )
            if not overwrite:
                return

        self._progress_frame.clear_log()
        self._progress_frame.start_job()
        self._progress_frame.log("Starting...")
        self._btn_start.configure(state="disabled")
        self._btn_merge.configure(state="disabled")
        self._btn_cancel.configure(state="normal")
        self._btn_open_folder.configure(state="disabled")
        self._last_output_paths = []
        self._cancel_event.clear()

        def run() -> None:
            run_archive_job(
                source_dir=source,
                output_dir=output,
                archive_name=name,
                compressed=(fmt == "gzip"),
                split_enabled=self._split_var.get(),
                chunk_mib=chunk_mib,
                keep_original_after_split=self._keep_original_var.get(),
                overwrite_existing=overwrite,
                turbo=(fmt == "turbo"),
                message_queue=self._message_queue,
                cancel_event=self._cancel_event,
            )

        self._worker_thread = threading.Thread(target=run, daemon=True)
        self._worker_thread.start()
        self._poll_queue()

    def _poll_queue(self) -> None:
        try:
            while True:
                msg = self._message_queue.get_nowait()
                if msg[0] == "state":
                    state: ProgressState = msg[1]
                    self._progress_frame.set_state(
                        state.phase,
                        files_done=state.files_done,
                        files_total=state.files_total,
                        bytes_done=state.bytes_done,
                        bytes_total=state.bytes_total,
                        message=state.message,
                    )
                    if state.output_paths:
                        self._last_output_paths = state.output_paths
                    if state.phase in ("done", "error", "cancelled"):
                        self._btn_start.configure(state="normal")
                        self._btn_merge.configure(state="normal")
                        self._btn_cancel.configure(state="disabled")
                        if state.phase == "done" and state.output_paths:
                            self._btn_open_folder.configure(state="normal")
                            if len(state.output_paths) > 1:
                                self._progress_frame.log("\nTo rejoin parts (Linux): cat name.tar.part-* > name.tar")
                                self._progress_frame.log("(Windows: use 7-Zip or copy /b part-001+part-002+... name.tar)")
                        break
                elif msg[0] == "log":
                    self._progress_frame.log(msg[1])
        except queue.Empty:
            pass
        if self._worker_thread and self._worker_thread.is_alive():
            self._poll_id = self.root.after(200, self._poll_queue)
        else:
            self._poll_id = None
            self._btn_start.configure(state="normal")
            self._btn_merge.configure(state="normal")
            self._btn_cancel.configure(state="disabled")

    def _on_merge(self) -> None:
        path = filedialog.askopenfilename(
            title="Select any part file (e.g. name.tar.part-001)",
            filetypes=(("Part files", "*.part-*"), ("All files", "*.*")),
        )
        if not path:
            return
        try:
            part_paths = discover_parts_from_path(path)
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return
        directory = os.path.dirname(part_paths[0])
        base_name = re.sub(r"\.part-\d+$", "", os.path.basename(part_paths[0]))
        output_path = os.path.join(directory, base_name)
        recap = (
            f"Parts: {len(part_paths)} file(s)\n"
            f"Output: {output_path}\n\n"
            "Merge?"
        )
        if not messagebox.askyesno("Confirm merge", recap):
            return
        overwrite = False
        if os.path.exists(output_path):
            overwrite = messagebox.askyesno(
                "Overwrite",
                f"Output file already exists:\n{output_path}\nOverwrite?",
            )
            if not overwrite:
                return
        self._progress_frame.clear_log()
        self._progress_frame.start_job()
        self._progress_frame.log("Merging parts...")
        self._btn_start.configure(state="disabled")
        self._btn_merge.configure(state="disabled")
        self._btn_cancel.configure(state="normal")
        self._btn_open_folder.configure(state="disabled")
        self._last_output_paths = []
        self._cancel_event.clear()

        def run() -> None:
            run_merge_job(
                part_paths=part_paths,
                output_path=output_path,
                message_queue=self._message_queue,
                cancel_event=self._cancel_event,
            )

        self._worker_thread = threading.Thread(target=run, daemon=True)
        self._worker_thread.start()
        self._poll_queue()

    def _on_cancel(self) -> None:
        self._cancel_event.set()
        self._btn_cancel.configure(state="disabled")
