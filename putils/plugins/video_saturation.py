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
    ("video_saturation.file_types.video", "*.mp4 *.mov *.mkv *.avi *.webm *.m4v"),
    ("video_saturation.file_types.all", "*.*"),
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
                    message=context.t("video_saturation.dependency.ffmpeg_missing"),
                )
            ]

        available = True
        version = ""
        message = context.t("video_saturation.dependency.ready")
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
            message = context.t("video_saturation.dependency.version_failed", error=exc)

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
        self.item_status_keys: dict[str, str] = {}
        self.output_dir = tk.StringVar(value=str(context.get_config(CONFIG_NAMESPACE, "output_dir", "")))
        self.saturation = tk.DoubleVar(value=float(context.get_config(CONFIG_NAMESPACE, "saturation", 0.7)))
        self.status = tk.StringVar(value=context.t("video_saturation.ready"))
        self.status_key = "video_saturation.ready"
        self.status_kwargs: dict[str, object] = {}
        self.progress = tk.DoubleVar(value=0)
        self.progress_text = tk.StringVar(value="0%")
        self.running = False

        self.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)
        self._build_ui()

    def _build_ui(self) -> None:
        controls = ttk.Frame(self)
        controls.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        controls.columnconfigure(1, weight=1)

        self.saturation_label = ttk.Label(controls)
        self.saturation_label.grid(row=0, column=0, sticky="w")
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

        self.output_dir_label = ttk.Label(controls)
        self.output_dir_label.grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(controls, textvariable=self.output_dir).grid(
            row=1, column=1, sticky="ew", padx=(8, 0), pady=(8, 0)
        )
        self.browse_button = ttk.Button(controls, command=self._choose_output_dir)
        self.browse_button.grid(
            row=1, column=2, sticky="e", padx=(8, 0), pady=(8, 0)
        )

        actions = ttk.Frame(self)
        actions.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        self.add_button = ttk.Button(actions, command=self._add_files)
        self.add_button.grid(row=0, column=0, padx=(0, 6))
        self.clear_button = ttk.Button(actions, command=self._clear_files)
        self.clear_button.grid(row=0, column=1, padx=(0, 6))
        self.run_button = ttk.Button(actions, command=self._run)
        self.run_button.grid(row=0, column=2)
        ttk.Label(actions, textvariable=self.status).grid(row=0, column=3, sticky="w", padx=(12, 0))

        progress_frame = ttk.Frame(self)
        progress_frame.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        progress_frame.columnconfigure(1, weight=1)
        self.progress_label = ttk.Label(progress_frame)
        self.progress_label.grid(row=0, column=0, sticky="w")
        ttk.Progressbar(progress_frame, variable=self.progress, maximum=100, mode="determinate").grid(
            row=0, column=1, sticky="ew", padx=(8, 8)
        )
        ttk.Label(progress_frame, textvariable=self.progress_text, width=8).grid(row=0, column=2, sticky="e")

        columns = ("path", "status")
        self.file_tree = ttk.Treeview(self, columns=columns, show="headings", height=12)
        self.file_tree.heading("path", text="path")
        self.file_tree.heading("status", text="status")
        self.file_tree.column("path", width=690, anchor="w")
        self.file_tree.column("status", width=160, anchor="w")
        self.file_tree.grid(row=3, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.file_tree.yview)
        scrollbar.grid(row=3, column=1, sticky="ns")
        self.file_tree.configure(yscrollcommand=scrollbar.set)
        self.set_language()

    def _on_saturation_change(self, *_args) -> None:
        value = round(float(self.saturation.get()), 2)
        self.ratio_label.configure(text=f"{value:.2f}")
        self.context.set_config(CONFIG_NAMESPACE, "saturation", value)

    def _choose_output_dir(self) -> None:
        selected = filedialog.askdirectory(title=self.context.t("video_saturation.select_output_dir"))
        if selected:
            self.output_dir.set(selected)
            self.context.set_config(CONFIG_NAMESPACE, "output_dir", selected)

    def _add_files(self) -> None:
        file_types = tuple((self.context.t(label_key), pattern) for label_key, pattern in VIDEO_FILE_TYPES)
        selected = filedialog.askopenfilenames(
            title=self.context.t("video_saturation.select_videos"),
            filetypes=file_types,
        )
        existing = {path.resolve() for path in self.files}
        for file_name in selected:
            path = Path(file_name).resolve()
            if path in existing:
                continue
            self.files.append(path)
            existing.add(path)
            self.file_tree.insert(
                "", tk.END, iid=str(path), values=(str(path), self.context.t("video_saturation.pending"))
            )
            self.item_status_keys[str(path)] = "video_saturation.pending"
        self._set_status("video_saturation.selected", count=len(self.files))

    def _clear_files(self) -> None:
        if self.running:
            return
        self.files.clear()
        self.item_status_keys.clear()
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        self.progress.set(0)
        self.progress_text.set("0%")
        self._set_status("video_saturation.ready")

    def _run(self) -> None:
        if self.running:
            return
        if not self.files:
            messagebox.showwarning(
                self.context.t("video_saturation.no_videos.title"),
                self.context.t("video_saturation.no_videos.message"),
            )
            return
        ffmpeg_path = shutil.which("ffmpeg")
        if not ffmpeg_path:
            messagebox.showerror(
                self.context.t("video_saturation.ffmpeg_missing.title"),
                self.context.t("video_saturation.ffmpeg_missing.message"),
            )
            self.context.log(PLUGIN_ID, "ERROR", "ffmpeg not found")
            return

        output_dir = self.output_dir.get().strip()
        files = list(self.files)
        self.context.set_config(CONFIG_NAMESPACE, "output_dir", output_dir)
        self.running = True
        self.run_button.configure(state=tk.DISABLED)
        self.progress.set(0)
        self.progress_text.set("0%")
        self._set_status("video_saturation.running")
        saturation = round(float(self.saturation.get()), 2)
        worker = threading.Thread(target=self._run_worker, args=(ffmpeg_path, saturation, output_dir, files), daemon=True)
        worker.start()

    def _run_worker(self, ffmpeg_path: str, saturation: float, output_dir: str, files: list[Path]) -> None:
        total = len(files)
        completed = 0
        processed = 0
        for input_path in files:
            self._set_item_status(input_path, "video_saturation.running")
            output_path = self._output_path_for(input_path, output_dir)
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
                self._set_item_status(input_path, "video_saturation.failed")
            except Exception as exc:
                self.context.log(
                    PLUGIN_ID,
                    "ERROR",
                    "Saturation adjustment failed",
                    {"input": str(input_path), "output": str(output_path), "error": str(exc)},
                )
                self._set_item_status(input_path, "video_saturation.failed")
            else:
                completed += 1
                self.context.log(
                    PLUGIN_ID,
                    "INFO",
                    "Saturation adjustment completed",
                    {"input": str(input_path), "output": str(output_path)},
                )
                self._set_item_status(input_path, "video_saturation.completed")
            processed += 1
            self.after(0, self._update_progress, processed, total)
            self.after(0, self._set_status, "video_saturation.progress_text", completed=completed, total=total)

        self.after(0, self._finish_run, completed, total)

    def _output_path_for(self, input_path: Path, output_dir: str) -> Path:
        directory = Path(output_dir).expanduser() if output_dir else input_path.parent
        return directory / f"{input_path.stem}_saturation_adjusted{input_path.suffix}"

    def _set_item_status(self, input_path: Path, status_key: str) -> None:
        def update() -> None:
            iid = str(input_path)
            self.item_status_keys[iid] = status_key
            if self.file_tree.exists(iid):
                self.file_tree.set(iid, "status", self.context.t(status_key))

        self.after(0, update)

    def _finish_run(self, completed: int, total: int) -> None:
        self.running = False
        self.run_button.configure(state=tk.NORMAL)
        self._set_status("video_saturation.finished", completed=completed, total=total)

    def _update_progress(self, processed: int, total: int) -> None:
        percent = round((processed / total) * 100, 1) if total else 0
        self.progress.set(percent)
        self.progress_text.set(f"{percent:g}%")

    def _set_status(self, key: str, **kwargs: object) -> None:
        self.status_key = key
        self.status_kwargs = kwargs
        self.status.set(self.context.t(key, **kwargs))

    def set_language(self) -> None:
        self.saturation_label.configure(text=self.context.t("video_saturation.saturation_ratio"))
        self.output_dir_label.configure(text=self.context.t("video_saturation.output_directory"))
        self.browse_button.configure(text=self.context.t("video_saturation.browse"))
        self.add_button.configure(text=self.context.t("video_saturation.add_videos"))
        self.clear_button.configure(text=self.context.t("video_saturation.clear"))
        self.run_button.configure(text=self.context.t("video_saturation.run"))
        self.progress_label.configure(text=self.context.t("video_saturation.progress"))
        self.file_tree.heading("path", text=self.context.t("video_saturation.video"))
        self.file_tree.heading("status", text=self.context.t("video_saturation.status"))
        self.status.set(self.context.t(self.status_key, **self.status_kwargs))
        for item_id, status_key in self.item_status_keys.items():
            if self.file_tree.exists(item_id):
                self.file_tree.set(item_id, "status", self.context.t(status_key))


def create_plugin() -> VideoSaturationPlugin:
    return VideoSaturationPlugin()
