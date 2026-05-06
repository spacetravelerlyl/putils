from __future__ import annotations

import shutil
import subprocess
import threading
import json
from functools import partial
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
        self.item_status_keys: dict[str, str] = {}
        self.output_paths: dict[str, Path] = {}
        self.output_dir = tk.StringVar(value=str(context.get_config(CONFIG_NAMESPACE, "output_dir", "")))
        self.saturation = tk.DoubleVar(value=float(context.get_config(CONFIG_NAMESPACE, "saturation", 0.7)))
        self.status = tk.StringVar(value=context.t("video_saturation.ready"))
        self.status_key = "video_saturation.ready"
        self.status_kwargs: dict[str, object] = {}
        self.progress = tk.DoubleVar(value=0)
        self.progress_text = tk.StringVar(value="0%")
        self.running = False
        self.worker_thread: threading.Thread | None = None
        self.run_generation = 0
        self.progress_fill = None
        self.progress_label_window = None
        self.progress_color = "#9ca3af"

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

        columns = ("path", "status")
        self.file_tree = ttk.Treeview(self, columns=columns, show="headings", height=12)
        self.file_tree.heading("path", text="path")
        self.file_tree.heading("status", text="status")
        self.file_tree.column("path", width=690, anchor="w")
        self.file_tree.column("status", width=160, anchor="w")
        self.file_tree.grid(row=3, column=0, sticky="nsew")
        self.file_tree.bind("<Button-3>", self._show_file_context_menu)

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
            self.output_paths.pop(str(path), None)
            self.file_tree.insert(
                "", tk.END, iid=str(path), values=(str(path), self.context.t("video_saturation.pending"))
            )
            self.item_status_keys[str(path)] = "video_saturation.pending"
        self._set_status("video_saturation.selected", count=len(self.files))

    def _clear_files(self) -> None:
        if self.running and self.worker_thread is not None and self.worker_thread.is_alive():
            return
        self.run_generation += 1
        self.running = False
        self.files.clear()
        self.item_status_keys.clear()
        self.output_paths.clear()
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
        self.run_generation += 1
        generation = self.run_generation
        self.context.set_config(CONFIG_NAMESPACE, "output_dir", output_dir)
        self.running = True
        self.run_button.configure(state=tk.DISABLED)
        self.progress.set(0)
        self.progress_text.set("0%")
        self._redraw_progress("#2563eb")
        self._set_status("video_saturation.running")
        saturation = round(float(self.saturation.get()), 2)
        self.worker_thread = threading.Thread(
            target=self._run_worker,
            args=(ffmpeg_path, saturation, output_dir, files, generation),
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
    ) -> None:
        total = len(files)
        completed = 0
        processed = 0
        for input_path in files:
            self._set_item_status(input_path, "video_saturation.running", generation)
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
                self._set_item_status(input_path, "video_saturation.failed", generation)
            except Exception as exc:
                self.context.log(
                    PLUGIN_ID,
                    "ERROR",
                    "Saturation adjustment failed",
                    {"input": str(input_path), "output": str(output_path), "error": str(exc)},
                )
                self._set_item_status(input_path, "video_saturation.failed", generation)
            else:
                completed += 1
                self.context.log(
                    PLUGIN_ID,
                    "INFO",
                    "Saturation adjustment completed",
                    {"input": str(input_path), "output": str(output_path)},
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

        self.after(0, self._finish_run, completed, total, generation)

    def _output_path_for(self, input_path: Path, output_dir: str) -> Path:
        directory = Path(output_dir).expanduser() if output_dir else input_path.parent
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
        for title_key, path in (
            ("video_saturation.preview.original", input_path),
            ("video_saturation.preview.converted", output_path),
        ):
            subprocess.Popen(
                [
                    ffplay_path,
                    "-autoexit",
                    "-window_title",
                    f"{self.context.t(title_key)} - {path.name}",
                    str(path),
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

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
        result = subprocess.run(
            [
                ffprobe_path,
                "-v",
                "error",
                "-print_format",
                "json",
                "-show_entries",
                (
                    "format=duration,bit_rate:"
                    "stream=codec_type,codec_name,width,height,avg_frame_rate,r_frame_rate"
                ),
                "-show_format",
                "-show_streams",
                str(path),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=15,
        )
        data = json.loads(result.stdout)
        video_stream = next((stream for stream in data.get("streams", []) if stream.get("codec_type") == "video"), {})
        audio_streams = [stream for stream in data.get("streams", []) if stream.get("codec_type") == "audio"]
        video_rate = video_stream.get("avg_frame_rate") or video_stream.get("r_frame_rate") or ""
        return {
            "file": path.name,
            "size": self._format_bytes(path.stat().st_size),
            "duration": self._format_duration(data.get("format", {}).get("duration", "")),
            "bitrate": self._format_bitrate(data.get("format", {}).get("bit_rate", "")),
            "video_codec": str(video_stream.get("codec_name", "")),
            "resolution": self._format_resolution(video_stream),
            "frame_rate": self._format_frame_rate(str(video_rate)),
            "audio": ", ".join(str(stream.get("codec_name", "")) for stream in audio_streams) or "-",
        }

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

    def _finish_run(self, completed: int, total: int, generation: int) -> None:
        if generation != self.run_generation:
            return
        self.running = False
        self.run_button.configure(state=tk.NORMAL)
        self._update_progress(total, total, "#16a34a" if completed == total else "#dc2626", generation)
        self._set_status("video_saturation.finished", generation, completed=completed, total=total)

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
