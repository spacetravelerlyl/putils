from __future__ import annotations

import json
import os
import shutil
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from putils.plugin_api import DependencyStatus, PluginMetadata
from putils.tk_utils import copy_treeview_selection_to_clipboard, open_in_file_manager


PLUGIN_ID = "video_saturation"
CONFIG_NAMESPACE = "plugin.video_saturation"
CACHE_SCHEMA = """
CREATE TABLE IF NOT EXISTS {table_name} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL UNIQUE,
    selected INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'pending',
    output_path TEXT,
    source_directory TEXT,
    error_message TEXT,
    error_details TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""
DEFAULT_PARALLELISM = max(1, min(4, os.cpu_count() or 1))
VIDEO_FILE_TYPES = (
    ("video_saturation.file_types.video", "*.mp4 *.mov *.mkv *.avi *.webm *.m4v"),
    ("video_saturation.file_types.all", "*.*"),
)
VIDEO_SUFFIXES = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}


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

        statuses: list[DependencyStatus] = []
        ffmpeg_available = True
        ffmpeg_version = ""
        ffmpeg_message = context.t("video_saturation.dependency.ready")
        try:
            result = subprocess.run(
                [ffmpeg_path, "-version"],
                check=True,
                capture_output=True,
                text=True,
                timeout=5,
            )
            ffmpeg_version = result.stdout.splitlines()[0] if result.stdout else ""
        except Exception as exc:
            ffmpeg_available = False
            ffmpeg_message = context.t("video_saturation.dependency.version_failed", error=exc)

        statuses.append(
            DependencyStatus(
                plugin_id=PLUGIN_ID,
                name="ffmpeg",
                dependency_type="external command",
                required=True,
                available=ffmpeg_available,
                version=ffmpeg_version,
                path=ffmpeg_path,
                message=ffmpeg_message,
            )
        )

        for command, message_key in (
            ("ffplay", "video_saturation.dependency.ffplay_missing"),
            ("ffprobe", "video_saturation.dependency.ffprobe_missing"),
        ):
            path = shutil.which(command)
            statuses.append(
                DependencyStatus(
                    plugin_id=PLUGIN_ID,
                    name=command,
                    dependency_type="external command",
                    required=False,
                    available=path is not None,
                    path=path or "",
                    message=context.t("video_saturation.dependency.ready")
                    if path
                    else context.t(message_key),
                )
            )

        return statuses


class VideoSaturationPanel(ttk.Frame):
    def __init__(self, parent, context) -> None:
        super().__init__(parent)
        self.context = context
        self.files: list[Path] = []
        self.selected_items: dict[str, bool] = {}
        self.item_status_keys: dict[str, str] = {}
        self.output_paths: dict[str, Path] = {}
        self.source_directories: dict[str, Path] = {}
        self.error_details: dict[str, str] = {}
        self.status_filter_var = tk.StringVar(value="all")
        self.detached_items: set[str] = set()
        self.output_dir = tk.StringVar(value=str(context.get_config(CONFIG_NAMESPACE, "output_dir", "")))
        self.saturation = tk.DoubleVar(value=float(context.get_config(CONFIG_NAMESPACE, "saturation", 0.7)))
        self.parallelism = tk.IntVar(value=self._configured_parallelism())
        self.status = tk.StringVar(value=context.t("video_saturation.ready"))
        self.status_key = "video_saturation.ready"
        self.status_kwargs: dict[str, object] = {}
        self.progress = tk.DoubleVar(value=0)
        self.progress_text = tk.StringVar(value="0%")
        self.running = False
        self.worker_thread: threading.Thread | None = None
        self.cancel_event = threading.Event()
        self.process_lock = threading.Lock()
        self.active_processes: set[subprocess.Popen] = set()
        self.run_generation = 0
        self.progress_fill = None
        self.progress_label_window = None
        self.progress_color = "#9ca3af"
        self.preview_process: subprocess.Popen | None = None
        self.preview_control_window: tk.Toplevel | None = None
        self.gpu_info = self._detect_gpu_info()
        self.gpu_available = bool(self.gpu_info["available"])
        self.gpu_modes: list[str] = ["off", *list(self.gpu_info.get("hwaccels", []))]
        saved_gpu_mode = str(context.get_config(CONFIG_NAMESPACE, "gpu_mode", "off"))
        if saved_gpu_mode not in self.gpu_modes:
            saved_gpu_mode = self.gpu_modes[1] if self.gpu_available and len(self.gpu_modes) > 1 else "off"
        self.gpu_mode = tk.StringVar(value=saved_gpu_mode)
        self.gpu_devices: list[dict[str, str]] = list(self.gpu_info.get("devices", []))
        self.gpu_device_labels = [device["label"] for device in self.gpu_devices] or [self.context.t("video_saturation.gpu.device.none")]
        saved_gpu_device = str(context.get_config(CONFIG_NAMESPACE, "gpu_device", ""))
        default_device = self.gpu_device_labels[0]
        if saved_gpu_device and saved_gpu_device in self.gpu_device_labels:
            default_device = saved_gpu_device
        self.gpu_device = tk.StringVar(value=default_device)
        self.gpu_status_text = tk.StringVar()

        self._init_cache()
        self.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(4, weight=1)
        self._build_ui()
        self._restore_from_cache()

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

        self.parallelism_label = ttk.Label(controls)
        self.parallelism_label.grid(row=2, column=0, sticky="w", pady=(8, 0))
        self.parallelism_spinbox = ttk.Spinbox(
            controls,
            textvariable=self.parallelism,
            from_=1,
            to=max(1, os.cpu_count() or 1),
            width=8,
        )
        self.parallelism_spinbox.grid(row=2, column=1, sticky="w", padx=(8, 0), pady=(8, 0))

        self.gpu_label = ttk.Label(controls)
        self.gpu_label.grid(row=3, column=0, sticky="nw", pady=(8, 0))
        self.gpu_status_label = ttk.Label(controls, textvariable=self.gpu_status_text, wraplength=520, justify="left")
        self.gpu_status_label.grid(row=3, column=1, sticky="w", padx=(8, 0), pady=(8, 0))
        self.gpu_mode_label = ttk.Label(controls)
        self.gpu_mode_label.grid(row=4, column=0, sticky="w", pady=(8, 0))
        self.gpu_mode_combo = ttk.Combobox(controls, textvariable=self.gpu_mode, state="readonly", width=18)
        self.gpu_mode_combo.grid(row=4, column=1, sticky="w", padx=(8, 0), pady=(8, 0))

        self.gpu_device_label = ttk.Label(controls)
        self.gpu_device_label.grid(row=5, column=0, sticky="w", pady=(8, 0))
        self.gpu_device_combo = ttk.Combobox(controls, textvariable=self.gpu_device, state="readonly", width=40)
        self.gpu_device_combo.grid(row=5, column=1, sticky="w", padx=(8, 0), pady=(8, 0))

        filter_frame = ttk.Frame(self)
        filter_frame.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        self.status_filter_label = ttk.Label(filter_frame)
        self.status_filter_label.grid(row=0, column=0, padx=(0, 4))
        self.status_filter_combo = ttk.Combobox(
            filter_frame, textvariable=self.status_filter_var, state="readonly", width=12
        )
        self.status_filter_combo.grid(row=0, column=1)
        self.status_filter_combo.bind("<<ComboboxSelected>>", self._apply_status_filter)

        actions = ttk.Frame(self)
        actions.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        self.add_button = ttk.Button(actions, command=self._add_files)
        self.add_button.grid(row=0, column=0, padx=(0, 6))
        self.add_directory_button = ttk.Button(actions, command=self._add_directory)
        self.add_directory_button.grid(row=0, column=1, padx=(0, 6))
        self.clear_button = ttk.Button(actions, command=self._clear_files)
        self.clear_button.grid(row=0, column=2, padx=(0, 6))
        self.select_all_button = ttk.Button(actions, command=self._select_all)
        self.select_all_button.grid(row=0, column=3, padx=(0, 6))
        self.deselect_all_button = ttk.Button(actions, command=self._deselect_all)
        self.deselect_all_button.grid(row=0, column=4, padx=(0, 6))
        self.run_button = ttk.Button(actions, command=self._run)
        self.run_button.grid(row=0, column=5)
        self.stop_button = ttk.Button(actions, command=self._stop_run)
        self.stop_button.grid(row=0, column=6, padx=(6, 0))
        self.stop_button.configure(state=tk.DISABLED)
        ttk.Label(actions, textvariable=self.status).grid(row=0, column=7, sticky="w", padx=(12, 0))

        progress_frame = ttk.Frame(self)
        progress_frame.grid(row=3, column=0, sticky="ew", pady=(0, 8))
        progress_frame.columnconfigure(1, weight=1)
        self.progress_label = ttk.Label(progress_frame)
        self.progress_label.grid(row=0, column=0, sticky="w")
        self.progress_canvas = tk.Canvas(
            progress_frame,
            height=18,
            highlightthickness=0,
            background="#e5e7eb",
        )
        self.progress_canvas.grid(row=0, column=1, sticky="ew", padx=(8, 8))
        self.progress_fill = self.progress_canvas.create_rectangle(0, 0, 0, 18, fill="#9ca3af", outline="")
        self.progress_label_window = self.progress_canvas.create_text(
            0,
            9,
            text="0%",
            fill="#111827",
            anchor="center",
        )
        self.progress_canvas.bind("<Configure>", lambda _event: self._redraw_progress())

        columns = ("selected", "path", "status")
        self.file_tree = ttk.Treeview(self, columns=columns, show="headings", height=12)
        self.file_tree.heading("selected", text="", command=self._toggle_select_all)
        self.file_tree.heading("path", text="path")
        self.file_tree.heading("status", text="status")
        self.file_tree.column("selected", width=40, anchor="center", stretch=False)
        self.file_tree.column("path", width=650, anchor="w")
        self.file_tree.column("status", width=150, anchor="w")
        self.file_tree.grid(row=4, column=0, sticky="nsew")
        self.file_tree.bind("<Button-3>", self._show_file_context_menu)
        self.file_tree.bind("<ButtonRelease-1>", self._on_tree_click)

        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.file_tree.yview)
        scrollbar.grid(row=4, column=1, sticky="ns")
        self.file_tree.configure(yscrollcommand=scrollbar.set)
        self.set_language()

    def _on_saturation_change(self, *_args) -> None:
        value = round(float(self.saturation.get()), 2)
        self.ratio_label.configure(text=f"{value:.2f}")
        self.context.set_config(CONFIG_NAMESPACE, "saturation", value)

    def _configured_parallelism(self) -> int:
        value = self.context.get_config(CONFIG_NAMESPACE, "parallelism", DEFAULT_PARALLELISM)
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return DEFAULT_PARALLELISM
        return max(1, parsed)

    def _selected_parallelism(self) -> int:
        try:
            value = int(str(self.parallelism.get()).strip())
        except (tk.TclError, TypeError, ValueError) as exc:
            raise ValueError(self.context.t("video_saturation.parallelism.invalid")) from exc
        if value < 1:
            raise ValueError(self.context.t("video_saturation.parallelism.invalid"))
        return value

    def _detect_gpu_info(self) -> dict[str, object]:
        ffmpeg_path = shutil.which("ffmpeg")
        raw_hwaccels: list[str] = []
        if ffmpeg_path:
            try:
                result = subprocess.run(
                    [ffmpeg_path, "-hide_banner", "-hwaccels"],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                raw_hwaccels = [
                    line.strip()
                    for line in result.stdout.splitlines()
                    if line.strip() and not line.lower().startswith("hardware acceleration")
                ]
            except Exception:
                raw_hwaccels = []

        gpu_devices = self._detect_gpu_devices()
        nvidia_detected = any("nvidia" in d.get("label", "").lower() for d in gpu_devices)

        validated_hwaccels: list[str] = []
        if ffmpeg_path:
            for hw in raw_hwaccels:
                if hw == "cuda" and not nvidia_detected:
                    continue
                if self._validate_hwaccel(ffmpeg_path, hw):
                    validated_hwaccels.append(hw)

        if gpu_devices:
            summary = "; ".join(d["label"] for d in gpu_devices)
        elif validated_hwaccels:
            summary = self.context.t(
                "video_saturation.gpu.detected_hwaccels",
                values=", ".join(validated_hwaccels),
            )
        else:
            summary = self.context.t("video_saturation.gpu.not_found")

        return {
            "available": len(validated_hwaccels) > 0,
            "summary": summary,
            "hwaccel": validated_hwaccels[0] if validated_hwaccels else None,
            "hwaccels": validated_hwaccels,
            "devices": gpu_devices,
        }

    def _detect_gpu_devices(self) -> list[dict[str, str]]:
        import platform as _platform
        if shutil.which("nvidia-smi"):
            try:
                result = subprocess.run(
                    [
                        "nvidia-smi",
                        "--query-gpu=name,driver_version,memory.total",
                        "--format=csv,noheader",
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                gpus = [line.strip() for line in result.stdout.splitlines() if line.strip()]
                if gpus:
                    return [
                        {"label": f"GPU {index}: {line}", "value": str(index)}
                        for index, line in enumerate(gpus)
                    ]
            except Exception:
                pass

        if _platform.system() == "Windows":
            try:
                result = subprocess.run(
                    ["wmic", "path", "win32_VideoController", "get", "name", "/format:csv"],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                devices: list[dict[str, str]] = []
                for line in result.stdout.splitlines():
                    line = line.strip()
                    if not line or line.lower().startswith("node,name") or line.lower().startswith("name"):
                        continue
                    parts = line.split(",", 1)
                    name = parts[-1].strip()
                    if name and not name.lower().startswith("microsoft basic"):
                        devices.append({"label": name, "value": str(len(devices))})
                if devices:
                    return devices
            except Exception:
                pass

        if shutil.which("lspci"):
            try:
                result = subprocess.run(
                    ["lspci"],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                matches = [
                    line.strip()
                    for line in result.stdout.splitlines()
                    if any(
                        token in line.lower()
                        for token in ("vga", "3d controller", "display controller")
                    )
                ]
                if matches:
                    return [
                        {"label": line, "value": str(i)}
                        for i, line in enumerate(matches)
                    ]
            except Exception:
                pass

        return []

    def _validate_hwaccel(self, ffmpeg_path: str, hwaccel: str) -> bool:
        try:
            subprocess.run(
                [
                    ffmpeg_path,
                    "-hide_banner",
                    "-loglevel", "error",
                    "-hwaccel", hwaccel,
                    "-f", "lavfi",
                    "-i", "color=black:size=2x2:rate=1",
                    "-frames:v", "1",
                    "-f", "null", "-",
                ],
                check=True,
                capture_output=True,
                timeout=10,
            )
            return True
        except Exception:
            return False

    @staticmethod
    def _format_elapsed(seconds: float) -> str:
        total_ms = round(seconds * 1000)
        minutes, rem_ms = divmod(total_ms, 60000)
        secs, ms = divmod(rem_ms, 1000)
        parts = []
        if minutes:
            parts.append(f"{minutes}min")
        if secs or minutes:
            parts.append(f"{secs}s")
        parts.append(f"{ms}ms")
        return ",".join(parts)

    @staticmethod
    def _is_gpu_error(stderr: str) -> bool:
        markers = (
            "Cannot load",
            "Could not dynamically load",
            "No device available for decoder",
            "Hardware device setup failed",
            "Device creation failed",
            "Failed to create hardware",
            "No hardware device found",
            "Cannot open",
            "No VA display found",
            "Cannot initialize hardware decoder",
            "Failed to initialise VAAPI connection",
            "DRM",
        )
        stderr_lower = stderr.lower()
        return any(m.lower() in stderr_lower for m in markers)

    def _gpu_status_display_text(self) -> str:
        summary = str(self.gpu_info.get("summary", "")).strip()
        hwaccels = self.gpu_info.get("hwaccels", [])
        if hwaccels:
            accel_text = self.context.t("video_saturation.gpu.hwaccels", values=", ".join(hwaccels))
            return f"{summary}\n{accel_text}" if summary else accel_text
        return summary

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
        self._add_paths((Path(file_name).resolve() for file_name in selected))

    def _add_directory(self) -> None:
        selected = filedialog.askdirectory(title=self.context.t("video_saturation.select_directory"))
        if not selected:
            return
        directory = Path(selected).resolve()
        videos = sorted(
            path for path in directory.rglob("*") if path.is_file() and path.suffix.lower() in VIDEO_SUFFIXES
        )
        if not videos:
            messagebox.showinfo(
                self.context.t("video_saturation.no_directory_videos.title"),
                self.context.t("video_saturation.no_directory_videos.message", directory=directory),
            )
            return
        self._add_paths(videos, source_directory=directory)

    def _add_paths(self, paths, source_directory: Path | None = None) -> None:
        existing = {path.resolve() for path in self.files}
        for path in paths:
            resolved = path.resolve()
            if resolved in existing:
                continue
            self.files.append(resolved)
            existing.add(resolved)
            item_id = str(resolved)
            self.selected_items[item_id] = True
            self.output_paths.pop(item_id, None)
            self.error_details.pop(item_id, None)
            if source_directory is not None:
                self.source_directories[item_id] = source_directory
            else:
                self.source_directories.pop(item_id, None)
            self.file_tree.insert(
                "",
                tk.END,
                iid=item_id,
                values=("☑", str(resolved), self.context.t("video_saturation.pending")),
            )
            self.item_status_keys[item_id] = "video_saturation.pending"
        self._save_to_cache()
        self._apply_status_filter()
        self._set_status("video_saturation.selected", count=len(self.files))

    def _clear_files(self) -> None:
        if self.running and self.worker_thread is not None and self.worker_thread.is_alive():
            return
        self.run_generation += 1
        self.running = False
        self.files.clear()
        self.selected_items.clear()
        self.item_status_keys.clear()
        self.output_paths.clear()
        self.source_directories.clear()
        self.error_details.clear()
        self.detached_items.clear()
        self.context.cache_store.clear(PLUGIN_ID)
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        self.progress.set(0)
        self.progress_text.set("0%")
        self._redraw_progress("#9ca3af")
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
        selected_files = [f for f in self.files if self.selected_items.get(str(f), True)]
        if not selected_files:
            messagebox.showwarning(
                self.context.t("video_saturation.no_selected.title"),
                self.context.t("video_saturation.no_selected.message"),
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
        files = selected_files
        try:
            parallelism = self._selected_parallelism()
        except ValueError as exc:
            messagebox.showerror(self.context.t("video_saturation.invalid_settings.title"), str(exc))
            return
        gpu_mode = self._selected_gpu_mode()
        gpu_device = self._selected_gpu_device()
        if gpu_mode != "off" and not self._validate_hwaccel(ffmpeg_path, gpu_mode):
            switch = messagebox.askyesno(
                self.context.t("video_saturation.gpu.validation_failed.title"),
                self.context.t("video_saturation.gpu.validation_failed.message", mode=gpu_mode),
            )
            if not switch:
                return
            gpu_mode = "off"
            self.gpu_mode.set("off")
        self.run_generation += 1
        generation = self.run_generation
        self.cancel_event.clear()
        self.context.set_config(CONFIG_NAMESPACE, "output_dir", output_dir)
        self.context.set_config(CONFIG_NAMESPACE, "parallelism", parallelism)
        self.context.set_config(CONFIG_NAMESPACE, "gpu_mode", gpu_mode)
        self.context.set_config(CONFIG_NAMESPACE, "gpu_device", gpu_device)
        self.running = True
        self.run_button.configure(state=tk.DISABLED)
        self.stop_button.configure(state=tk.NORMAL)
        self.progress.set(0)
        self.progress_text.set("0%")
        self._redraw_progress("#2563eb")
        self._set_status("video_saturation.running")
        saturation = round(float(self.saturation.get()), 2)
        self.worker_thread = threading.Thread(
            target=self._run_worker,
            args=(ffmpeg_path, saturation, output_dir, files, generation, parallelism, gpu_mode, gpu_device),
            daemon=True,
        )
        self.worker_thread.start()

    def _run_worker(
        self,
        ffmpeg_path: str,
        saturation: float,
        output_dir: str,
        files: list[Path],
        generation: int,
        parallelism: int,
        gpu_mode: str,
        gpu_device: str,
    ) -> None:
        total = len(files)
        completed = 0
        processed = 0
        gpu_error_seen = False
        with ThreadPoolExecutor(max_workers=parallelism) as executor:
            futures = {}
            for input_path in files:
                self._set_item_status(input_path, "video_saturation.running", generation)
                output_path = self._output_path_for(input_path, output_dir)
                futures[
                    executor.submit(
                        self._process_video,
                        ffmpeg_path,
                        input_path,
                        output_path,
                        saturation,
                        gpu_mode,
                        gpu_device,
                        parallelism,
                    )
                ] = (input_path, output_path)

            for future in as_completed(futures):
                if self.cancel_event.is_set():
                    for pending in futures:
                        pending.cancel()
                input_path, output_path = futures[future]
                try:
                    future.result()
                except subprocess.CalledProcessError as exc:
                    if self.cancel_event.is_set():
                        self._set_item_status(input_path, "video_saturation.failed", generation)
                        continue
                    stderr = (exc.stderr or "").strip()[-2000:]
                    timing = getattr(exc, "_timing", {})
                    error_info = {
                        "input": str(input_path),
                        "output": str(output_path),
                        "stderr": stderr,
                        **timing,
                    }
                    if gpu_mode != "off" and not gpu_error_seen and self._is_gpu_error(stderr):
                        gpu_error_seen = True
                        error_info["gpu_hint"] = self.context.t("video_saturation.gpu.error_hint", mode=gpu_mode)
                    self.error_details[str(input_path)] = json.dumps(error_info)
                    self._set_item_status(input_path, "video_saturation.failed", generation)
                except Exception as exc:
                    if self.cancel_event.is_set() and str(exc) == "cancelled":
                        self._set_item_status(input_path, "video_saturation.failed", generation)
                        continue
                    error_info = {"input": str(input_path), "output": str(output_path), "error": str(exc)}
                    self.error_details[str(input_path)] = json.dumps(error_info)
                    self.context.log(
                        PLUGIN_ID,
                        "ERROR",
                        "Saturation adjustment failed",
                        error_info,
                    )
                    self._set_item_status(input_path, "video_saturation.failed", generation)
                else:
                    completed += 1
                    self.context.log(
                        PLUGIN_ID,
                        "INFO",
                        "Saturation adjustment completed",
                        {"input": str(input_path), "output": str(output_path), "gpu_mode": gpu_mode},
                    )
                    self._set_item_completed(input_path, output_path, generation)
                processed += 1
                self.after(0, self._update_progress, processed, total, "#2563eb", generation)
                self.after(
                    0,
                    partial(
                        self._set_status,
                        "video_saturation.progress_text",
                        generation,
                        completed=completed,
                        total=total,
                    ),
                )

        if gpu_error_seen:
            self.after(0, lambda: messagebox.showwarning(
                self.context.t("video_saturation.gpu.error_detected.title"),
                self.context.t("video_saturation.gpu.error_detected.message", mode=gpu_mode),
            ))
        self.after(0, self._finish_run, completed, total, generation, self.cancel_event.is_set())

    def _process_video(
        self,
        ffmpeg_path: str,
        input_path: Path,
        output_path: Path,
        saturation: float,
        gpu_mode: str,
        gpu_device: str,
        parallelism: int,
    ) -> None:
        if self.cancel_event.is_set():
            raise RuntimeError("cancelled")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cmd = [ffmpeg_path, "-y"]
        if gpu_mode != "off":
            cmd.extend(["-hwaccel", gpu_mode])
        if parallelism > 1:
            cmd.extend(["-threads", "1"])
        cmd.extend(
            [
                "-i",
                str(input_path),
                "-vf",
                f"eq=saturation={saturation:.2f}",
                "-c:a",
                "copy",
                str(output_path),
            ]
        )
        from datetime import datetime as _datetime
        from datetime import timezone as _timezone
        start_time = _datetime.now(_timezone.utc)
        start_monotonic = time.monotonic()
        env = os.environ.copy()
        if gpu_device and gpu_device != self.context.t("video_saturation.gpu.device.none"):
            env["CUDA_VISIBLE_DEVICES"] = gpu_device
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
        with self.process_lock:
            self.active_processes.add(process)
        try:
            stdout, stderr = process.communicate()
        finally:
            with self.process_lock:
                self.active_processes.discard(process)
        elapsed = time.monotonic() - start_monotonic
        end_time = _datetime.now(_timezone.utc)
        cmd_str = " ".join(cmd)
        timing = {
            "cmd": cmd_str,
            "start_time": start_time.isoformat(timespec="milliseconds"),
            "end_time": end_time.isoformat(timespec="milliseconds"),
            "duration": self._format_elapsed(elapsed),
        }
        if self.cancel_event.is_set():
            raise RuntimeError("cancelled")
        if process.returncode != 0:
            stderr_tail = (stderr or "").strip()[-2000:]
            self.context.log(
                PLUGIN_ID,
                "ERROR",
                "Saturation adjustment failed",
                {
                    "input": str(input_path),
                    "output": str(output_path),
                    "saturation": saturation,
                    "gpu_mode": gpu_mode,
                    "gpu_device": gpu_device,
                    "stderr": stderr_tail,
                    **timing,
                },
            )
            exc = subprocess.CalledProcessError(process.returncode, cmd, output=stdout, stderr=stderr)
            exc._timing = timing
            raise exc
        self.context.log(
            PLUGIN_ID,
            "INFO",
            "Saturation adjustment completed",
            {
                "input": str(input_path),
                "output": str(output_path),
                "saturation": saturation,
                "gpu_mode": gpu_mode,
                "gpu_device": gpu_device,
                **timing,
            },
        )

    def _selected_gpu_mode(self) -> str:
        mode = self.gpu_mode.get().strip()
        if not self.gpu_available:
            return "off"
        return mode if mode in self.gpu_modes else "off"

    def _selected_gpu_device(self) -> str:
        selected = self.gpu_device.get().strip()
        for device in self.gpu_devices:
            if device["label"] == selected:
                return device["value"]
        return ""

    def _stop_run(self) -> None:
        if not self.running:
            return
        self.cancel_event.set()
        with self.process_lock:
            processes = list(self.active_processes)
        for process in processes:
            if process.poll() is None:
                process.terminate()
        self.stop_button.configure(state=tk.DISABLED)
        self._set_status("video_saturation.stopping")

    def _output_path_for(self, input_path: Path, output_dir: str) -> Path:
        source_directory = self.source_directories.get(str(input_path))
        if source_directory is not None:
            target_root = (
                Path(output_dir).expanduser().resolve()
                if output_dir
                else source_directory.parent
            )
            directory = target_root / f"{source_directory.name}_saturation_adjusted"
            relative_parent = input_path.parent.relative_to(source_directory)
            directory = directory / relative_parent
        else:
            directory = Path(output_dir).expanduser().resolve() if output_dir else input_path.parent
        return directory / f"{input_path.stem}_saturation_adjusted{input_path.suffix}"

    def _set_item_status(self, input_path: Path, status_key: str, generation: int | None = None) -> None:
        def update() -> None:
            if generation is not None and generation != self.run_generation:
                return
            iid = str(input_path)
            self.item_status_keys[iid] = status_key
            if status_key != "video_saturation.completed":
                self.output_paths.pop(iid, None)
            if self.file_tree.exists(iid):
                self.file_tree.set(iid, "status", self.context.t(status_key))

        self.after(0, update)

    def _set_item_completed(self, input_path: Path, output_path: Path, generation: int) -> None:
        def update() -> None:
            if generation != self.run_generation:
                return
            iid = str(input_path)
            self.item_status_keys[iid] = "video_saturation.completed"
            self.output_paths[iid] = output_path
            if self.file_tree.exists(iid):
                self.file_tree.set(iid, "status", self.context.t("video_saturation.completed"))

        self.after(0, update)

    def _show_file_context_menu(self, event) -> None:
        item_id = self.file_tree.identify_row(event.y)
        if item_id:
            self.file_tree.selection_set(item_id)
            self.file_tree.focus(item_id)
        else:
            self.file_tree.selection_remove(self.file_tree.selection())
        menu = tk.Menu(self.file_tree, tearoff=0)
        menu.add_command(
            label=self.context.t("video_saturation.context.process_selected"),
            command=self._process_selected,
        )
        menu.add_command(
            label=self.context.t("video_saturation.context.copy_path"),
            command=lambda: copy_treeview_selection_to_clipboard(self.file_tree, self.file_tree),
        )
        if item_id:
            source_dir = self.source_directories.get(item_id)
            if source_dir and source_dir.exists():
                menu.add_command(
                    label=self.context.t("video_saturation.context.open_source_dir"),
                    command=lambda d=source_dir: open_in_file_manager(str(d)),
                )
            output_path = self.output_paths.get(item_id)
            if output_path and output_path.exists():
                menu.add_command(
                    label=self.context.t("video_saturation.context.open_target_dir"),
                    command=lambda p=output_path: open_in_file_manager(str(p)),
                )
        menu.add_separator()
        state = tk.NORMAL if self._selected_completed_pair() is not None else tk.DISABLED
        menu.add_command(
            label=self.context.t("video_saturation.context.compare_preview"),
            command=self._compare_preview,
            state=state,
        )
        menu.add_command(
            label=self.context.t("video_saturation.context.compare_info"),
            command=self._compare_video_info,
            state=state,
        )
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _selected_completed_pair(self) -> tuple[Path, Path] | None:
        selection = self.file_tree.selection()
        if not selection:
            return None
        input_path = Path(selection[0])
        output_path = self.output_paths.get(selection[0])
        if (
            output_path is None
            or self.item_status_keys.get(selection[0]) != "video_saturation.completed"
            or not output_path.exists()
        ):
            return None
        return input_path, output_path

    def _compare_preview(self) -> None:
        pair = self._selected_completed_pair()
        if pair is None:
            messagebox.showinfo(
                self.context.t("video_saturation.preview_unavailable.title"),
                self.context.t("video_saturation.preview_unavailable.message"),
            )
            return
        ffplay_path = shutil.which("ffplay")
        if not ffplay_path:
            messagebox.showerror(
                self.context.t("video_saturation.ffplay_missing.title"),
                self.context.t("video_saturation.ffplay_missing.message"),
            )
            return
        input_path, output_path = pair
        self._close_preview()
        filter_complex = (
            f"movie='{self._escape_ffmpeg_filter_path(input_path)}',setpts=PTS-STARTPTS,"
            "scale=-2:540,pad=iw+8:ih+8:4:4:color=white[left];"
            f"movie='{self._escape_ffmpeg_filter_path(output_path)}',setpts=PTS-STARTPTS,"
            "scale=-2:540,pad=iw+8:ih+8:4:4:color=white[right];"
            "[left][right]hstack=inputs=2:shortest=1"
        )
        self.preview_process = subprocess.Popen(
            [
                ffplay_path,
                "-autoexit",
                "-an",
                "-window_title",
                self.context.t("video_saturation.preview.window_title"),
                "-f",
                "lavfi",
                "-i",
                filter_complex,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self._open_preview_control_window(input_path, output_path)

    def _compare_video_info(self) -> None:
        pair = self._selected_completed_pair()
        if pair is None:
            messagebox.showinfo(
                self.context.t("video_saturation.preview_unavailable.title"),
                self.context.t("video_saturation.preview_unavailable.message"),
            )
            return
        ffprobe_path = shutil.which("ffprobe")
        if not ffprobe_path:
            messagebox.showerror(
                self.context.t("video_saturation.ffprobe_missing.title"),
                self.context.t("video_saturation.ffprobe_missing.message"),
            )
            return
        input_path, output_path = pair
        try:
            original = self._probe_video(ffprobe_path, input_path)
            converted = self._probe_video(ffprobe_path, output_path)
        except Exception as exc:
            messagebox.showerror(self.context.t("video_saturation.probe_failed.title"), str(exc))
            return
        self._show_video_info_window(input_path, output_path, original, converted)

    def _probe_video(self, ffprobe_path: str, path: Path) -> dict[str, str]:
        format_info = self._ffprobe_key_values(
            ffprobe_path,
            path,
            ["-show_entries", "format=duration,bit_rate"],
        )
        video_info = self._ffprobe_key_values(
            ffprobe_path,
            path,
            ["-select_streams", "v:0", "-show_entries", "stream=codec_name,width,height,avg_frame_rate,r_frame_rate"],
        )
        audio_codecs = self._ffprobe_values(
            ffprobe_path,
            path,
            ["-select_streams", "a", "-show_entries", "stream=codec_name"],
            "codec_name",
        )
        video_rate = video_info.get("avg_frame_rate") or video_info.get("r_frame_rate") or ""
        return {
            "file": path.name,
            "size": self._format_bytes(path.stat().st_size),
            "duration": self._format_duration(format_info.get("duration", "")),
            "bitrate": self._format_bitrate(format_info.get("bit_rate", "")),
            "video_codec": video_info.get("codec_name", "") or "-",
            "resolution": self._format_resolution(video_info),
            "frame_rate": self._format_frame_rate(str(video_rate)),
            "audio": ", ".join(audio_codecs) or "-",
        }

    def _ffprobe_key_values(self, ffprobe_path: str, path: Path, extra_args: list[str]) -> dict[str, str]:
        result = subprocess.run(
            [
                ffprobe_path,
                "-v",
                "error",
                *extra_args,
                "-of",
                "default=noprint_wrappers=1:nokey=0",
                str(path),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=15,
        )
        values: dict[str, str] = {}
        for line in result.stdout.splitlines():
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
        return values

    def _ffprobe_values(self, ffprobe_path: str, path: Path, extra_args: list[str], key_name: str) -> list[str]:
        result = subprocess.run(
            [
                ffprobe_path,
                "-v",
                "error",
                *extra_args,
                "-of",
                "default=noprint_wrappers=1:nokey=0",
                str(path),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=15,
        )
        values: list[str] = []
        for line in result.stdout.splitlines():
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key.strip() == key_name and value.strip():
                values.append(value.strip())
        return values

    def _show_video_info_window(
        self,
        input_path: Path,
        output_path: Path,
        original: dict[str, str],
        converted: dict[str, str],
    ) -> None:
        window = tk.Toplevel(self)
        window.title(self.context.t("video_saturation.info_window.title"))
        window.geometry("760x420")
        window.columnconfigure(0, weight=1)
        window.rowconfigure(0, weight=1)

        text = tk.Text(window, wrap="none", font=("TkFixedFont", 10))
        text.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(window, orient=tk.VERTICAL, command=text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        text.configure(yscrollcommand=scrollbar.set)

        lines = [
            f"{self.context.t('video_saturation.info.original')}: {input_path}",
            f"{self.context.t('video_saturation.info.converted')}: {output_path}",
            "",
            f"{self.context.t('video_saturation.info.field'):<18}"
            f"{self.context.t('video_saturation.info.original'):<28}"
            f"{self.context.t('video_saturation.info.converted')}",
            "-" * 74,
        ]
        fields = (
            ("file", "video_saturation.info.file"),
            ("size", "video_saturation.info.size"),
            ("duration", "video_saturation.info.duration"),
            ("bitrate", "video_saturation.info.bitrate"),
            ("video_codec", "video_saturation.info.video_codec"),
            ("resolution", "video_saturation.info.resolution"),
            ("frame_rate", "video_saturation.info.frame_rate"),
            ("audio", "video_saturation.info.audio"),
        )
        for key, label_key in fields:
            lines.append(f"{self.context.t(label_key):<18}{original[key]:<28}{converted[key]}")
        text.insert("1.0", "\n".join(lines))
        text.configure(state=tk.DISABLED)

    def _open_preview_control_window(self, input_path: Path, output_path: Path) -> None:
        window = tk.Toplevel(self)
        window.title(self.context.t("video_saturation.preview.control_title"))
        window.geometry("520x160")
        window.resizable(False, False)
        window.columnconfigure(0, weight=1)
        window.protocol("WM_DELETE_WINDOW", self._close_preview)

        frame = ttk.Frame(window, padding=12)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)

        ttk.Label(frame, text=self.context.t("video_saturation.preview.window_title")).grid(
            row=0, column=0, sticky="w", pady=(0, 10)
        )
        ttk.Label(
            frame,
            text=f"{self.context.t('video_saturation.preview.original')}: {input_path.name}",
        ).grid(row=1, column=0, sticky="w", pady=(0, 6))
        ttk.Label(
            frame,
            text=f"{self.context.t('video_saturation.preview.converted')}: {output_path.name}",
        ).grid(row=2, column=0, sticky="w", pady=(0, 12))
        ttk.Button(
            frame,
            text=self.context.t("video_saturation.preview.close"),
            command=self._close_preview,
        ).grid(row=3, column=0, sticky="w")

        self.preview_control_window = window
        self._poll_preview_process()

    def _poll_preview_process(self) -> None:
        if self.preview_process is None:
            return
        if self.preview_process.poll() is not None:
            self._close_preview(destroy_process=False)
            return
        if self.preview_control_window is not None and self.preview_control_window.winfo_exists():
            self.after(500, self._poll_preview_process)

    def _close_preview(self, destroy_process: bool = True) -> None:
        if destroy_process and self.preview_process is not None and self.preview_process.poll() is None:
            self.preview_process.terminate()
        self.preview_process = None
        if self.preview_control_window is not None and self.preview_control_window.winfo_exists():
            self.preview_control_window.destroy()
        self.preview_control_window = None

    def _format_bytes(self, size: int) -> str:
        value = float(size)
        for unit in ("B", "KB", "MB", "GB"):
            if value < 1024 or unit == "GB":
                return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} {unit}"
            value /= 1024
        return f"{value:.1f} GB"

    def _format_duration(self, duration: str) -> str:
        try:
            total_seconds = int(round(float(duration)))
        except (TypeError, ValueError):
            return "-"
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def _format_bitrate(self, bitrate: str) -> str:
        try:
            return f"{int(bitrate) / 1000:.0f} kbps"
        except (TypeError, ValueError):
            return "-"

    def _format_resolution(self, stream: dict) -> str:
        width = stream.get("width")
        height = stream.get("height")
        return f"{width}x{height}" if width and height else "-"

    def _format_frame_rate(self, frame_rate: str) -> str:
        if "/" not in frame_rate:
            return frame_rate or "-"
        numerator, denominator = frame_rate.split("/", 1)
        try:
            denominator_value = float(denominator)
            if denominator_value == 0:
                return "-"
            return f"{float(numerator) / denominator_value:.2f} fps"
        except ValueError:
            return "-"

    def _escape_ffmpeg_filter_path(self, path: Path) -> str:
        value = str(path)
        for source, target in (
            ("\\", "\\\\"),
            (":", "\\:"),
            ("'", "\\'"),
            ("[", "\\["),
            ("]", "\\]"),
            (",", "\\,"),
            (";", "\\;"),
        ):
            value = value.replace(source, target)
        return value

    def _finish_run(self, completed: int, total: int, generation: int, cancelled: bool = False) -> None:
        if generation != self.run_generation:
            return
        self.running = False
        self.run_button.configure(state=tk.NORMAL)
        self.stop_button.configure(state=tk.DISABLED)
        self._update_progress(total if not cancelled else completed, total, "#16a34a" if completed == total and not cancelled else "#dc2626", generation)
        if cancelled:
            self._set_status("video_saturation.cancelled", generation, completed=completed, total=total)
        else:
            self._set_status("video_saturation.finished", generation, completed=completed, total=total)
        self._save_to_cache()

    def _update_progress(
        self,
        processed: int,
        total: int,
        color: str = "#2563eb",
        generation: int | None = None,
    ) -> None:
        if generation is not None and generation != self.run_generation:
            return
        percent = round((processed / total) * 100, 1) if total else 0
        self.progress.set(percent)
        self.progress_text.set(f"{percent:g}%")
        self._redraw_progress(color)

    def _redraw_progress(self, color: str | None = None) -> None:
        if color is not None:
            self.progress_color = color
        self._draw_progress()

    def _draw_progress(self) -> None:
        width = max(self.progress_canvas.winfo_width(), 1)
        height = max(self.progress_canvas.winfo_height(), 18)
        fill_width = width * float(self.progress.get()) / 100
        if self.progress_fill is not None:
            self.progress_canvas.coords(self.progress_fill, 0, 0, fill_width, height)
            self.progress_canvas.itemconfigure(self.progress_fill, fill=self.progress_color)
        if self.progress_label_window is not None:
            self.progress_canvas.coords(self.progress_label_window, width / 2, height / 2)
            self.progress_canvas.itemconfigure(self.progress_label_window, text=self.progress_text.get())

    def _set_status(self, key: str, generation: int | None = None, **kwargs: object) -> None:
        if generation is not None and generation != self.run_generation:
            return
        self.status_key = key
        self.status_kwargs = kwargs
        self.status.set(self.context.t(key, **kwargs))

    def set_language(self) -> None:
        self.saturation_label.configure(text=self.context.t("video_saturation.saturation_ratio"))
        self.output_dir_label.configure(text=self.context.t("video_saturation.output_directory"))
        self.parallelism_label.configure(text=self.context.t("video_saturation.parallelism"))
        self.gpu_label.configure(text=self.context.t("video_saturation.gpu.info"))
        self.gpu_mode_label.configure(text=self.context.t("video_saturation.gpu.mode"))
        self.gpu_device_label.configure(text=self.context.t("video_saturation.gpu.device"))
        self.gpu_status_text.set(self._gpu_status_display_text())
        self.gpu_mode_combo.configure(values=self.gpu_modes, state="readonly")
        self.gpu_mode.set(self._selected_gpu_mode())
        self.gpu_device_combo.configure(values=self.gpu_device_labels, state="readonly" if self.gpu_devices else tk.DISABLED)
        self.browse_button.configure(text=self.context.t("video_saturation.browse"))
        self.add_button.configure(text=self.context.t("video_saturation.add_videos"))
        self.add_directory_button.configure(text=self.context.t("video_saturation.add_directory"))
        self.clear_button.configure(text=self.context.t("video_saturation.clear"))
        self.select_all_button.configure(text=self.context.t("video_saturation.select_all"))
        self.deselect_all_button.configure(text=self.context.t("video_saturation.deselect_all"))
        self.run_button.configure(text=self.context.t("video_saturation.run"))
        self.stop_button.configure(text=self.context.t("video_saturation.stop"))
        self.progress_label.configure(text=self.context.t("video_saturation.progress"))
        self.status_filter_label.configure(text=self.context.t("video_saturation.filter.status"))
        self.status_filter_combo.configure(values=[
            self.context.t("video_saturation.filter.all"),
            self.context.t("video_saturation.pending"),
            self.context.t("video_saturation.running"),
            self.context.t("video_saturation.completed"),
            self.context.t("video_saturation.failed"),
        ])
        self.status_filter_var.set(self.context.t("video_saturation.filter.all"))
        self.file_tree.heading("path", text=self.context.t("video_saturation.video"))
        self.file_tree.heading("status", text=self.context.t("video_saturation.status"))
        self.status.set(self.context.t(self.status_key, **self.status_kwargs))
        self._refresh_selection_display()
        for item_id, status_key in self.item_status_keys.items():
            if self.file_tree.exists(item_id):
                self.file_tree.set(item_id, "status", self.context.t(status_key))

    def _init_cache(self) -> None:
        self.context.cache_store.ensure_plugin_table(PLUGIN_ID, CACHE_SCHEMA)

    def _restore_from_cache(self) -> None:
        rows = self.context.cache_store.get_all(PLUGIN_ID)
        for row in rows:
            file_path = Path(row["file_path"])
            if not file_path.exists():
                continue
            iid = str(file_path)
            self.files.append(file_path)
            self.selected_items[iid] = bool(row["selected"])
            self.item_status_keys[iid] = row["status"]
            if row["output_path"]:
                self.output_paths[iid] = Path(row["output_path"])
            if row["source_directory"]:
                self.source_directories[iid] = Path(row["source_directory"])
            if row["error_details"]:
                self.error_details[iid] = row["error_details"]
            selected_text = "☑" if self.selected_items[iid] else "☐"
            status_key = row["status"]
            self.file_tree.insert(
                "",
                tk.END,
                iid=iid,
                values=(selected_text, str(file_path), self.context.t(status_key)),
            )
        if self.files:
            self._set_status("video_saturation.selected", count=len(self.files))

    def _save_to_cache(self) -> None:
        from datetime import datetime, timezone
        for file_path in self.files:
            iid = str(file_path)
            self.context.cache_store.upsert(
                PLUGIN_ID,
                str(file_path),
                selected=1 if self.selected_items.get(iid, True) else 0,
                status=self.item_status_keys.get(iid, "video_saturation.pending"),
                output_path=str(self.output_paths.get(iid, "")),
                source_directory=str(self.source_directories.get(iid, "")),
                error_message="",
                error_details=self.error_details.get(iid, ""),
                created_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            )

    def _process_selected(self) -> None:
        self._run()

    def _on_tree_click(self, event) -> None:
        region = self.file_tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        column = self.file_tree.identify_column(event.x)
        if column != "#1":
            return
        item_id = self.file_tree.identify_row(event.y)
        if not item_id:
            return
        self.selected_items[item_id] = not self.selected_items.get(item_id, True)
        self._refresh_selection_display()

    def _select_all(self) -> None:
        for item_id in self.file_tree.get_children():
            self.selected_items[item_id] = True
        self._refresh_selection_display()

    def _deselect_all(self) -> None:
        for item_id in self.file_tree.get_children():
            self.selected_items[item_id] = False
        self._refresh_selection_display()

    def _toggle_select_all(self) -> None:
        children = self.file_tree.get_children()
        if not children:
            return
        selected_count = sum(1 for item_id in children if self.selected_items.get(item_id, True))
        if selected_count > len(children) // 2:
            self._deselect_all()
        else:
            self._select_all()

    def _refresh_selection_display(self) -> None:
        for item_id in self.file_tree.get_children():
            selected = self.selected_items.get(item_id, True)
            selected_text = "☑" if selected else "☐"
            self.file_tree.set(item_id, "selected", selected_text)

    def _apply_status_filter(self, event=None) -> None:
        filter_value = self.status_filter_var.get()
        status_map = {
            self.context.t("video_saturation.filter.all"): None,
            self.context.t("video_saturation.pending"): "video_saturation.pending",
            self.context.t("video_saturation.running"): "video_saturation.running",
            self.context.t("video_saturation.completed"): "video_saturation.completed",
            self.context.t("video_saturation.failed"): "video_saturation.failed",
        }
        target_status = status_map.get(filter_value)
        for item_id in list(self.detached_items):
            self.file_tree.move(item_id, "", tk.END)
            self.detached_items.discard(item_id)
        if target_status is None:
            return
        for item_id in self.file_tree.get_children():
            item_status = self.item_status_keys.get(item_id)
            if item_status != target_status:
                self.file_tree.detach(item_id)
                self.detached_items.add(item_id)


def create_plugin() -> VideoSaturationPlugin:
    return VideoSaturationPlugin()
