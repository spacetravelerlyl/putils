from __future__ import annotations

import shutil
import subprocess
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from putils.plugin_api import DependencyStatus, PluginMetadata


PLUGIN_ID = "video_saturation"
CONFIG_NAMESPACE = "plugin.video_saturation"
VIDEO_FILE_TYPES = (
    ("Video files", "*.mp4 *.mov *.mkv *.avi *.webm *.m4v"),
    ("All files", "*.*"),
)


class VideoSaturationPlugin:
    metadata = PluginMetadata(
        plugin_id=PLUGIN_ID,
        name="Video Saturation",
        description="Batch-adjust video saturation with ffmpeg.",
        version="0.1.0",
    )

    def build(self, parent, context):
        return VideoSaturationPanel(parent, context)

    def check_dependencies(self, context) -> list[DependencyStatus]:
        ffmpeg_path = shutil.which("ffmpeg")
        if not ffmpeg_path:
            return [
                DependencyStatus(
                    plugin_id=PLUGIN_ID,
                    name="ffmpeg",
                    dependency_type="external command",
                    required=True,
                    available=False,
                    message="Install ffmpeg and make sure it is on PATH.",
                )
            ]

        available = True
        version = ""
        message = "Ready"
        try:
            result = subprocess.run(
                [ffmpeg_path, "-version"],
                check=True,
                capture_output=True,
                text=True,
                timeout=5,
            )
            version = result.stdout.splitlines()[0] if result.stdout else ""
        except Exception as exc:
            available = False
            message = f"Found command but version check failed: {exc}"

        return [
            DependencyStatus(
                plugin_id=PLUGIN_ID,
                name="ffmpeg",
                dependency_type="external command",
                required=True,
                available=available,
                version=version,
                path=ffmpeg_path,
                message=message,
            )
        ]


class VideoSaturationPanel(ttk.Frame):
    def __init__(self, parent, context) -> None:
        super().__init__(parent)
        self.context = context
        self.files: list[Path] = []
        self.output_dir = tk.StringVar(value=str(context.get_config(CONFIG_NAMESPACE, "output_dir", "")))
        self.saturation = tk.DoubleVar(value=float(context.get_config(CONFIG_NAMESPACE, "saturation", 0.7)))
        self.status = tk.StringVar(value="Ready")
        self.running = False

        self.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        self._build_ui()

    def _build_ui(self) -> None:
        controls = ttk.Frame(self)
        controls.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        controls.columnconfigure(1, weight=1)

        ttk.Label(controls, text="Saturation ratio").grid(row=0, column=0, sticky="w")
        ratio_frame = ttk.Frame(controls)
        ratio_frame.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        ratio_frame.columnconfigure(0, weight=1)
        ttk.Scale(
            ratio_frame,
            variable=self.saturation,
            from_=0.0,
            to=2.0,
            command=self._on_saturation_change,
        ).grid(row=0, column=0, sticky="ew")
        self.ratio_label = ttk.Label(ratio_frame, width=6)
        self.ratio_label.grid(row=0, column=1, padx=(8, 0))
        self._on_saturation_change()

        ttk.Label(controls, text="Output directory").grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(controls, textvariable=self.output_dir).grid(
            row=1, column=1, sticky="ew", padx=(8, 0), pady=(8, 0)
        )
        ttk.Button(controls, text="Browse", command=self._choose_output_dir).grid(
            row=1, column=2, sticky="e", padx=(8, 0), pady=(8, 0)
        )

        actions = ttk.Frame(self)
        actions.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        ttk.Button(actions, text="Add Videos", command=self._add_files).grid(row=0, column=0, padx=(0, 6))
        ttk.Button(actions, text="Clear", command=self._clear_files).grid(row=0, column=1, padx=(0, 6))
        self.run_button = ttk.Button(actions, text="Run", command=self._run)
        self.run_button.grid(row=0, column=2)
        ttk.Label(actions, textvariable=self.status).grid(row=0, column=3, sticky="w", padx=(12, 0))

        columns = ("path", "status")
        self.file_tree = ttk.Treeview(self, columns=columns, show="headings", height=12)
        self.file_tree.heading("path", text="Video")
        self.file_tree.heading("status", text="Status")
        self.file_tree.column("path", width=690, anchor="w")
        self.file_tree.column("status", width=160, anchor="w")
        self.file_tree.grid(row=2, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.file_tree.yview)
        scrollbar.grid(row=2, column=1, sticky="ns")
        self.file_tree.configure(yscrollcommand=scrollbar.set)

    def _on_saturation_change(self, *_args) -> None:
        value = round(float(self.saturation.get()), 2)
        self.ratio_label.configure(text=f"{value:.2f}")
        self.context.set_config(CONFIG_NAMESPACE, "saturation", value)

    def _choose_output_dir(self) -> None:
        selected = filedialog.askdirectory(title="Select output directory")
        if selected:
            self.output_dir.set(selected)
            self.context.set_config(CONFIG_NAMESPACE, "output_dir", selected)

    def _add_files(self) -> None:
        selected = filedialog.askopenfilenames(title="Select videos", filetypes=VIDEO_FILE_TYPES)
        existing = {path.resolve() for path in self.files}
        for file_name in selected:
            path = Path(file_name).resolve()
            if path in existing:
                continue
            self.files.append(path)
            existing.add(path)
            self.file_tree.insert("", tk.END, iid=str(path), values=(str(path), "Pending"))
        self.status.set(f"{len(self.files)} file(s) selected")

    def _clear_files(self) -> None:
        if self.running:
            return
        self.files.clear()
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        self.status.set("Ready")

    def _run(self) -> None:
        if self.running:
            return
        if not self.files:
            messagebox.showwarning("No videos", "Please add at least one video file.")
            return
        ffmpeg_path = shutil.which("ffmpeg")
        if not ffmpeg_path:
            messagebox.showerror("ffmpeg not found", "Please install ffmpeg and make sure it is on PATH.")
            self.context.log(PLUGIN_ID, "ERROR", "ffmpeg not found")
            return

        self.context.set_config(CONFIG_NAMESPACE, "output_dir", self.output_dir.get().strip())
        self.running = True
        self.run_button.configure(state=tk.DISABLED)
        self.status.set("Running")
        saturation = round(float(self.saturation.get()), 2)
        worker = threading.Thread(target=self._run_worker, args=(ffmpeg_path, saturation), daemon=True)
        worker.start()

    def _run_worker(self, ffmpeg_path: str, saturation: float) -> None:
        total = len(self.files)
        completed = 0
        for input_path in list(self.files):
            self._set_item_status(input_path, "Running")
            output_path = self._output_path_for(input_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            cmd = [
                ffmpeg_path,
                "-y",
                "-i",
                str(input_path),
                "-vf",
                f"eq=saturation={saturation:.2f}",
                "-c:a",
                "copy",
                str(output_path),
            ]
            self.context.log(
                PLUGIN_ID,
                "INFO",
                "Started saturation adjustment",
                {"input": str(input_path), "output": str(output_path), "saturation": saturation},
            )
            try:
                subprocess.run(cmd, check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as exc:
                stderr = (exc.stderr or "").strip()[-2000:]
                self.context.log(
                    PLUGIN_ID,
                    "ERROR",
                    "Saturation adjustment failed",
                    {"input": str(input_path), "output": str(output_path), "stderr": stderr},
                )
                self._set_item_status(input_path, "Failed")
            except Exception as exc:
                self.context.log(
                    PLUGIN_ID,
                    "ERROR",
                    "Saturation adjustment failed",
                    {"input": str(input_path), "output": str(output_path), "error": str(exc)},
                )
                self._set_item_status(input_path, "Failed")
            else:
                completed += 1
                self.context.log(
                    PLUGIN_ID,
                    "INFO",
                    "Saturation adjustment completed",
                    {"input": str(input_path), "output": str(output_path)},
                )
                self._set_item_status(input_path, "Completed")
            self.after(0, self.status.set, f"{completed}/{total} completed")

        self.after(0, self._finish_run, completed, total)

    def _output_path_for(self, input_path: Path) -> Path:
        output_dir = self.output_dir.get().strip()
        directory = Path(output_dir).expanduser() if output_dir else input_path.parent
        return directory / f"{input_path.stem}_saturation_adjusted{input_path.suffix}"

    def _set_item_status(self, input_path: Path, status: str) -> None:
        def update() -> None:
            iid = str(input_path)
            if self.file_tree.exists(iid):
                self.file_tree.set(iid, "status", status)

        self.after(0, update)

    def _finish_run(self, completed: int, total: int) -> None:
        self.running = False
        self.run_button.configure(state=tk.NORMAL)
        self.status.set(f"Finished: {completed}/{total} completed")


def create_plugin() -> VideoSaturationPlugin:
    return VideoSaturationPlugin()
