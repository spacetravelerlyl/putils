from __future__ import annotations

import os
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .database import CacheStore, ConfigStore, LogStore
from .i18n import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES, Translator
from .paths import cache_db_path, config_db_path, default_user_data_dir, log_db_path, user_data_dir, write_configured_data_dir
from .plugin_api import DependencyStatus
from .plugin_loader import discover_plugins
from .tk_utils import copy_treeview_selection_to_clipboard


APP_CONFIG_NAMESPACE = "app"
DEFAULT_TIMEZONE = "Asia/Shanghai"
DEFAULT_LOG_RETENTION_LIMIT = 1_000_000
DEFAULT_LOG_LEVEL = "INFO"
LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR")
LOG_LEVEL_WEIGHTS: dict[str, int] = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40}
SUPPORTED_TIMEZONES = (
    "Asia/Shanghai",
    "UTC",
    "local",
    "America/New_York",
    "America/Los_Angeles",
    "Europe/London",
    "Europe/Berlin",
    "Asia/Tokyo",
)


class AppContext:
    def __init__(self, config_store: ConfigStore, log_store: LogStore, cache_store: CacheStore, translator: Translator, min_log_level: str = DEFAULT_LOG_LEVEL) -> None:
        self.config_store = config_store
        self.log_store = log_store
        self.cache_store = cache_store
        self.translator = translator
        self.min_log_level = min_log_level

    def get_config(self, namespace: str, key: str, default: object = None) -> object:
        return self.config_store.get(namespace, key, default)

    def set_config(self, namespace: str, key: str, value: object) -> None:
        self.config_store.set(namespace, key, value)

    def log(self, plugin_id: str, level: str, message: str, details: dict | None = None) -> None:
        if LOG_LEVEL_WEIGHTS.get(level, 0) < LOG_LEVEL_WEIGHTS.get(self.min_log_level, 20):
            return
        self.log_store.add(plugin_id, level, message, details)

    def t(self, key: str, default: str | None = None, **kwargs: object) -> str:
        return self.translator.t(key, default, **kwargs)


class PUtilsApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.geometry("980x680")
        self.minsize(860, 560)

        self.config_store = ConfigStore(config_db_path())
        language = str(self.config_store.get(APP_CONFIG_NAMESPACE, "language", DEFAULT_LANGUAGE))
        self.display_timezone = str(self.config_store.get(APP_CONFIG_NAMESPACE, "timezone", DEFAULT_TIMEZONE))
        self.log_retention_limit = self._configured_log_retention_limit()
        self.log_level = str(self.config_store.get(APP_CONFIG_NAMESPACE, "log_level", DEFAULT_LOG_LEVEL))
        self.log_store = LogStore(log_db_path(), self.log_retention_limit)
        self.log_store.rotate()
        self.cache_store = CacheStore(cache_db_path())
        self.translator = Translator(language)
        self.context = AppContext(self.config_store, self.log_store, self.cache_store, self.translator, self.log_level)
        self._log_refresh_after_id: str | None = None
        self._log_details: dict[str, dict] = {}
        self.plugins = []
        self.plugin_panels: list[object] = []
        self.empty_plugin_label = None
        self.empty_plugin_tab_index: int | None = None
        self.plugin_tab_indices: list[int] = []
        self.settings_frame = None
        self.settings_tab_index: int | None = None
        self.logs_tab_index: int | None = None
        self.language_display_to_code: dict[str, str] = {}
        self.language_code_to_display: dict[str, str] = {}
        self.current_data_dir = user_data_dir().resolve()
        self.migrated_data_dir: Path | None = None

        self._configure_style()
        self._build_layout()
        self._load_plugins()
        self._apply_language()
        self._refresh_logs()

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("TButton", padding=(10, 5))
        style.configure("TLabel", padding=(0, 2))
        style.configure(
            "Treeview",
            borderwidth=1,
            relief="solid",
            rowheight=24,
            background="#ffffff",
            fieldbackground="#ffffff",
        )
        style.configure("Treeview.Heading", borderwidth=1, relief="solid")

    def _build_layout(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        main_frame = ttk.Frame(self, padding=8)
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)

        self.plugin_notebook = ttk.Notebook(main_frame)
        self.plugin_notebook.grid(row=0, column=0, sticky="nsew")

    def _add_logs_page(self) -> None:
        log_frame = ttk.Frame(self.plugin_notebook, padding=8)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(2, weight=1)

        filter_frame = ttk.Frame(log_frame)
        filter_frame.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        self.log_time_filter_var = tk.StringVar(value="all")
        self.log_level_filter_var = tk.StringVar(value="all")
        self.log_plugin_filter_var = tk.StringVar(value="all")
        self.log_time_filter_label = ttk.Label(filter_frame)
        self.log_time_filter_label.grid(row=0, column=0, padx=(0, 4))
        self.log_time_filter_combo = ttk.Combobox(
            filter_frame, textvariable=self.log_time_filter_var, state="readonly", width=12
        )
        self.log_time_filter_combo.grid(row=0, column=1, padx=(0, 12))
        self.log_time_filter_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh_logs(schedule=False))
        self.log_level_filter_label = ttk.Label(filter_frame)
        self.log_level_filter_label.grid(row=0, column=2, padx=(0, 4))
        self.log_level_filter_combo = ttk.Combobox(
            filter_frame, textvariable=self.log_level_filter_var, state="readonly", width=10
        )
        self.log_level_filter_combo.grid(row=0, column=3, padx=(0, 12))
        self.log_level_filter_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh_logs(schedule=False))
        self.log_plugin_filter_label = ttk.Label(filter_frame)
        self.log_plugin_filter_label.grid(row=0, column=4, padx=(0, 4))
        self.log_plugin_filter_combo = ttk.Combobox(
            filter_frame, textvariable=self.log_plugin_filter_var, state="readonly", width=14
        )
        self.log_plugin_filter_combo.grid(row=0, column=5)
        self.log_plugin_filter_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh_logs(schedule=False))

        header = ttk.Frame(log_frame)
        header.grid(row=1, column=0, sticky="ew", pady=(4, 6))
        header.columnconfigure(0, weight=1)
        self.logs_title_label = ttk.Label(header)
        self.logs_title_label.grid(row=0, column=0, sticky="w")
        self.logs_refresh_button = ttk.Button(header, command=lambda: self._refresh_logs(schedule=False))
        self.logs_refresh_button.grid(
            row=0, column=1, sticky="e"
        )

        columns = ("created_at", "plugin_id", "level", "message")
        self.log_tree = ttk.Treeview(log_frame, columns=columns, show="headings", height=8)
        for column, width in (
            ("created_at", 165),
            ("plugin_id", 170),
            ("level", 80),
            ("message", 520),
        ):
            self.log_tree.heading(column, text=column)
            self.log_tree.column(column, width=width, anchor="w")
        self.log_tree.grid(row=2, column=0, sticky="nsew")
        self.log_tree.bind("<Button-3>", self._show_log_context_menu)
        self.log_tree.bind("<Double-1>", self._on_log_double_click)

        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_tree.yview)
        scrollbar.grid(row=2, column=1, sticky="ns")
        self.log_tree.configure(yscrollcommand=scrollbar.set)

        self.plugin_notebook.add(log_frame, text=self.context.t("logs.tab"))
        self.logs_tab_index = self.plugin_notebook.index("end") - 1

    def _load_plugins(self) -> None:
        self.plugins = discover_plugins()
        self._add_settings_page()
        self._add_logs_page()
        if not self.plugins:
            empty = ttk.Frame(self.plugin_notebook, padding=16)
            self.empty_plugin_label = ttk.Label(empty)
            self.empty_plugin_label.grid(row=0, column=0, sticky="w")
            self.plugin_notebook.add(empty, text=self.context.t("plugins.tab"))
            self.empty_plugin_tab_index = self.plugin_notebook.index("end") - 1
        else:
            for plugin in self.plugins:
                frame = ttk.Frame(self.plugin_notebook, padding=12)
                frame.columnconfigure(0, weight=1)
                frame.rowconfigure(0, weight=1)
                panel = plugin.build(frame, self.context)
                self.plugin_panels.append(panel)
                self.plugin_notebook.add(
                    frame,
                    text=self.context.t(f"plugin.{plugin.metadata.plugin_id}.name", plugin.metadata.name),
                )
                self.plugin_tab_indices.append(self.plugin_notebook.index("end") - 1)

    def _add_settings_page(self) -> None:
        frame = ttk.Frame(self.plugin_notebook, padding=12)
        frame.columnconfigure(1, weight=1)
        self.settings_frame = frame

        self.settings_title_label = ttk.Label(frame)
        self.settings_title_label.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 10))

        self.settings_language_label = ttk.Label(frame)
        self.settings_language_label.grid(row=1, column=0, sticky="w", pady=(0, 8))
        self.language_var = tk.StringVar()
        self.language_combo = ttk.Combobox(frame, textvariable=self.language_var, state="readonly", width=18)
        self.language_combo.grid(row=1, column=1, sticky="w", pady=(0, 8))
        self.language_combo.bind("<<ComboboxSelected>>", self._on_language_selected)

        self.settings_timezone_label = ttk.Label(frame)
        self.settings_timezone_label.grid(row=2, column=0, sticky="w", pady=(0, 8))
        self.timezone_var = tk.StringVar(value=self.display_timezone)
        self.timezone_combo = ttk.Combobox(
            frame,
            textvariable=self.timezone_var,
            values=SUPPORTED_TIMEZONES,
            state="readonly",
            width=24,
        )
        self.timezone_combo.grid(row=2, column=1, sticky="w", pady=(0, 8))
        self.timezone_combo.bind("<<ComboboxSelected>>", self._on_timezone_selected)

        self.settings_log_retention_label = ttk.Label(frame)
        self.settings_log_retention_label.grid(row=3, column=0, sticky="w", pady=(0, 8))
        self.log_retention_var = tk.StringVar(value=str(self.log_retention_limit))
        self.log_retention_spinbox = ttk.Spinbox(
            frame,
            textvariable=self.log_retention_var,
            from_=1,
            to=100_000_000,
            increment=1000,
            width=18,
        )
        self.log_retention_spinbox.grid(row=3, column=1, sticky="w", pady=(0, 8))

        self.settings_log_level_label = ttk.Label(frame)
        self.settings_log_level_label.grid(row=4, column=0, sticky="w", pady=(0, 8))
        self.log_level_var = tk.StringVar(value=self.log_level)
        self.log_level_combo = ttk.Combobox(
            frame, textvariable=self.log_level_var, values=list(LOG_LEVELS), state="readonly", width=10
        )
        self.log_level_combo.grid(row=4, column=1, sticky="w", pady=(0, 8))

        self.settings_data_dir_label = ttk.Label(frame)
        self.settings_data_dir_label.grid(row=5, column=0, sticky="w", pady=(0, 8))
        self.data_dir_var = tk.StringVar(value=str(self.current_data_dir))
        self.data_dir_entry = ttk.Entry(frame, textvariable=self.data_dir_var)
        self.data_dir_entry.grid(row=5, column=1, sticky="ew", pady=(0, 8))
        self.data_dir_browse_button = ttk.Button(frame, command=self._choose_data_dir)
        self.data_dir_browse_button.grid(row=5, column=2, sticky="e", padx=(8, 0), pady=(0, 8))
        self.data_dir_var.trace_add("write", lambda *_args: self._update_migration_button())

        self.settings_config_db_label = ttk.Label(frame)
        self.settings_config_db_label.grid(row=6, column=0, sticky="w", pady=(0, 8))
        self.config_db_var = tk.StringVar(value=str(config_db_path()))
        ttk.Entry(frame, textvariable=self.config_db_var, state="readonly").grid(
            row=6, column=1, columnspan=2, sticky="ew", pady=(0, 8)
        )

        self.settings_log_db_label = ttk.Label(frame)
        self.settings_log_db_label.grid(row=7, column=0, sticky="w", pady=(0, 8))
        self.log_db_var = tk.StringVar(value=str(log_db_path()))
        ttk.Entry(frame, textvariable=self.log_db_var, state="readonly").grid(
            row=7, column=1, columnspan=2, sticky="ew", pady=(0, 8)
        )

        self.settings_cache_db_label = ttk.Label(frame)
        self.settings_cache_db_label.grid(row=8, column=0, sticky="w", pady=(0, 8))
        self.cache_db_var = tk.StringVar(value=str(cache_db_path()))
        ttk.Entry(frame, textvariable=self.cache_db_var, state="readonly").grid(
            row=8, column=1, columnspan=2, sticky="ew", pady=(0, 8)
        )

        self.settings_hint_label = ttk.Label(frame, wraplength=720)
        self.settings_hint_label.grid(row=9, column=0, columnspan=3, sticky="w", pady=(2, 10))

        self.settings_save_button = ttk.Button(frame, command=self._save_settings)
        self.settings_save_button.grid(row=10, column=1, sticky="w")
        self.settings_migrate_button = ttk.Button(frame, command=self._migrate_databases)
        self.settings_migrate_button.grid(row=10, column=2, sticky="w", padx=(8, 0))
        self.settings_migrate_button.grid_remove()
        self.settings_restore_defaults_button = ttk.Button(frame, command=self._restore_default_settings)
        self.settings_restore_defaults_button.grid(row=11, column=1, sticky="w", pady=(8, 0))
        self.settings_dependency_button = ttk.Button(frame, command=self._show_dependency_summary)
        self.settings_dependency_button.grid(row=11, column=2, sticky="w", padx=(8, 0), pady=(8, 0))

        self.plugin_notebook.add(frame, text=self.context.t("settings.tab"))
        self.settings_tab_index = self.plugin_notebook.index("end") - 1
        self._update_migration_button()

    def _apply_language(self) -> None:
        self.title(self.context.t("app.title"))

        self.logs_title_label.configure(text=self.context.t("logs.title"))
        self.logs_refresh_button.configure(text=self.context.t("logs.refresh"))
        self.log_time_filter_label.configure(text=self.context.t("logs.filter.time"))
        self.log_time_filter_combo.configure(values=[
            self.context.t("logs.filter.time.all"),
            self.context.t("logs.filter.time.today"),
            self.context.t("logs.filter.time.7days"),
            self.context.t("logs.filter.time.30days"),
        ])
        self.log_level_filter_label.configure(text=self.context.t("logs.filter.level"))
        self.log_level_filter_combo.configure(values=[
            self.context.t("logs.filter.level.all"),
            "INFO",
            "WARNING",
            "ERROR",
        ])
        self.log_plugin_filter_label.configure(text=self.context.t("logs.filter.plugin"))
        plugin_filter_values = [self.context.t("logs.filter.plugin.all")] + [
            plugin.metadata.plugin_id for plugin in self.plugins
        ]
        self.log_plugin_filter_combo.configure(values=plugin_filter_values)
        log_headings = {
            "created_at": "logs.created_at",
            "plugin_id": "logs.plugin_id",
            "level": "logs.level",
            "message": "logs.message",
        }
        for column, key in log_headings.items():
            self.log_tree.heading(column, text=self.context.t(key))

        if self.empty_plugin_label is not None:
            self.empty_plugin_label.configure(text=self.context.t("plugins.none"))
            if self.empty_plugin_tab_index is not None:
                self.plugin_notebook.tab(self.empty_plugin_tab_index, text=self.context.t("plugins.tab"))

        for index, plugin in enumerate(self.plugins):
            if index < len(self.plugin_tab_indices):
                self.plugin_notebook.tab(
                    self.plugin_tab_indices[index],
                    text=self.context.t(f"plugin.{plugin.metadata.plugin_id}.name", plugin.metadata.name),
                )
        self._apply_settings_language()
        for panel in self.plugin_panels:
            language_setter = getattr(panel, "set_language", None)
            if language_setter is not None:
                language_setter()

    def _apply_settings_language(self) -> None:
        if self.settings_frame is None:
            return
        self.language_code_to_display = {
            code: self.context.t(f"settings.language.{code}", code) for code in SUPPORTED_LANGUAGES
        }
        self.language_display_to_code = {display: code for code, display in self.language_code_to_display.items()}
        self.language_combo.configure(values=[self.language_code_to_display[code] for code in SUPPORTED_LANGUAGES])
        self.language_var.set(self.language_code_to_display[self.translator.language])

        self.settings_title_label.configure(text=self.context.t("settings.title"))
        self.settings_language_label.configure(text=self.context.t("settings.language"))
        self.settings_timezone_label.configure(text=self.context.t("settings.timezone"))
        self.settings_log_retention_label.configure(text=self.context.t("settings.log_retention"))
        self.settings_log_level_label.configure(text=self.context.t("settings.log_level"))
        self.settings_data_dir_label.configure(text=self.context.t("settings.data_dir"))
        self.settings_config_db_label.configure(text=self.context.t("settings.config_db"))
        self.settings_log_db_label.configure(text=self.context.t("settings.log_db"))
        self.settings_cache_db_label.configure(text=self.context.t("settings.cache_db"))
        self.data_dir_browse_button.configure(text=self.context.t("settings.browse"))
        self.settings_save_button.configure(text=self.context.t("settings.save"))
        self.settings_migrate_button.configure(text=self.context.t("settings.migrate"))
        self.settings_restore_defaults_button.configure(text=self.context.t("settings.restore_defaults"))
        self.settings_dependency_button.configure(text=self.context.t("dependency.title"))
        hint = self.context.t("settings.restart_hint")
        if os.environ.get("PUTILS_DATA_DIR"):
            hint = f"{hint} {self.context.t('settings.env_override')}"
        self.settings_hint_label.configure(text=hint)
        if self.settings_tab_index is not None:
            self.plugin_notebook.tab(self.settings_tab_index, text=self.context.t("settings.tab"))
        if self.logs_tab_index is not None:
            self.plugin_notebook.tab(self.logs_tab_index, text=self.context.t("logs.tab"))

    def _on_language_selected(self, _event=None) -> None:
        selected = self.language_var.get()
        next_language = self.language_display_to_code.get(selected)
        if not next_language or next_language == self.translator.language:
            return
        self.translator.set_language(next_language)
        self.config_store.set(APP_CONFIG_NAMESPACE, "language", next_language)
        self.context.log("app", "INFO", f"Language changed to {next_language}")
        self._apply_language()

    def _on_timezone_selected(self, _event=None) -> None:
        selected = self.timezone_var.get()
        if selected not in SUPPORTED_TIMEZONES:
            selected = DEFAULT_TIMEZONE
            self.timezone_var.set(selected)
        self.display_timezone = selected
        self.config_store.set(APP_CONFIG_NAMESPACE, "timezone", selected)
        self.context.log("app", "INFO", f"Timezone changed to {selected}")
        self._refresh_logs(schedule=False)

    def _configured_log_retention_limit(self) -> int:
        value = self.config_store.get(
            APP_CONFIG_NAMESPACE,
            "log_retention_limit",
            DEFAULT_LOG_RETENTION_LIMIT,
        )
        try:
            limit = int(value)
        except (TypeError, ValueError):
            return DEFAULT_LOG_RETENTION_LIMIT
        return max(1, limit)

    def _selected_log_retention_limit(self) -> int:
        value = self.log_retention_var.get().strip().replace(",", "")
        try:
            limit = int(value)
        except ValueError as exc:
            raise ValueError(self.context.t("settings.log_retention.invalid")) from exc
        if limit < 1:
            raise ValueError(self.context.t("settings.log_retention.invalid"))
        return limit

    def _choose_data_dir(self) -> None:
        selected = filedialog.askdirectory(
            title=self.context.t("settings.select_data_dir"),
            initialdir=self.data_dir_var.get() or str(user_data_dir()),
        )
        if selected:
            self.data_dir_var.set(str(Path(selected).expanduser().resolve()))

    def _target_data_dir(self) -> Path:
        return Path(self.data_dir_var.get()).expanduser().resolve()

    def _data_dir_changed(self) -> bool:
        try:
            target = self._target_data_dir()
        except OSError:
            return True
        if target == self.current_data_dir:
            return False
        return target != self.migrated_data_dir

    def _update_migration_button(self) -> None:
        if not hasattr(self, "settings_migrate_button"):
            return
        if self._data_dir_changed():
            self.settings_migrate_button.grid()
        else:
            self.settings_migrate_button.grid_remove()

    def _save_settings(self) -> None:
        try:
            data_dir = self._target_data_dir()
            log_retention_limit = self._selected_log_retention_limit()
            log_level = self.log_level_var.get().strip()
            if log_level not in LOG_LEVELS:
                log_level = DEFAULT_LOG_LEVEL
            data_dir.mkdir(parents=True, exist_ok=True)
            write_configured_data_dir(data_dir)
            self.config_store.set(APP_CONFIG_NAMESPACE, "configured_data_dir", str(data_dir))
            self.config_store.set(APP_CONFIG_NAMESPACE, "log_retention_limit", log_retention_limit)
            self.config_store.set(APP_CONFIG_NAMESPACE, "log_level", log_level)
            self.log_retention_limit = log_retention_limit
            self.log_level = log_level
            self.context.min_log_level = log_level
            self.log_retention_var.set(str(log_retention_limit))
            self.log_store.set_retention_limit(log_retention_limit)
            self.log_store.rotate()
            self.context.log(
                "app", "INFO", "Settings saved",
                {
                    "data_dir": str(data_dir),
                    "log_retention_limit": log_retention_limit,
                    "log_level": log_level,
                },
            )
        except Exception as exc:
            messagebox.showerror(self.context.t("settings.error.title"), str(exc))
            return
        messagebox.showinfo(
            self.context.t("settings.saved.title"),
            self.context.t("settings.saved.message"),
        )
        self._update_migration_button()
        self._refresh_logs(schedule=False)

    def _restore_default_settings(self) -> None:
        for step in range(1, 4):
            confirmed = messagebox.askyesno(
                self.context.t("settings.restore_defaults.confirm.title", step=step),
                self.context.t("settings.restore_defaults.confirm.message", step=step),
                parent=self,
            )
            if not confirmed:
                return

        default_data_dir = default_user_data_dir().resolve()
        try:
            default_data_dir.mkdir(parents=True, exist_ok=True)
            write_configured_data_dir(default_data_dir)
            self.config_store.set(APP_CONFIG_NAMESPACE, "language", DEFAULT_LANGUAGE)
            self.config_store.set(APP_CONFIG_NAMESPACE, "timezone", DEFAULT_TIMEZONE)
            self.config_store.set(APP_CONFIG_NAMESPACE, "configured_data_dir", str(default_data_dir))
            self.config_store.set(APP_CONFIG_NAMESPACE, "log_retention_limit", DEFAULT_LOG_RETENTION_LIMIT)
            self.config_store.set(APP_CONFIG_NAMESPACE, "log_level", DEFAULT_LOG_LEVEL)
            self.translator.set_language(DEFAULT_LANGUAGE)
            self.display_timezone = DEFAULT_TIMEZONE
            self.log_retention_limit = DEFAULT_LOG_RETENTION_LIMIT
            self.log_level = DEFAULT_LOG_LEVEL
            self.context.min_log_level = DEFAULT_LOG_LEVEL
            self.log_store.set_retention_limit(DEFAULT_LOG_RETENTION_LIMIT)
            self.log_store.rotate()
            self.context.log("app", "INFO", "Settings restored to defaults")
        except Exception as exc:
            messagebox.showerror(self.context.t("settings.error.title"), str(exc))
            return

        self.timezone_var.set(DEFAULT_TIMEZONE)
        self.log_retention_var.set(str(DEFAULT_LOG_RETENTION_LIMIT))
        self.log_level_var.set(DEFAULT_LOG_LEVEL)
        self.data_dir_var.set(str(default_data_dir))
        self.migrated_data_dir = None
        self._apply_language()
        self._update_migration_button()
        self._refresh_logs(schedule=False)
        messagebox.showinfo(
            self.context.t("settings.restored.title"),
            self.context.t("settings.restored.message"),
        )

    def _migrate_databases(self) -> None:
        try:
            target_dir = self._target_data_dir()
            target_dir.mkdir(parents=True, exist_ok=True)
            self.config_store.set(APP_CONFIG_NAMESPACE, "configured_data_dir", str(target_dir))
            migrated = self._copy_database_files(target_dir)
            write_configured_data_dir(target_dir)
        except Exception as exc:
            messagebox.showerror(self.context.t("settings.error.title"), str(exc))
            return
        messagebox.showinfo(
            self.context.t("settings.migrated.title"),
            self.context.t("settings.migrated.message", count=migrated),
        )
        self.migrated_data_dir = target_dir
        self._update_migration_button()

    def _copy_database_files(self, target_dir: Path) -> int:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        migrated = 0
        for source in (config_db_path(), log_db_path(), cache_db_path()):
            if not source.exists():
                continue
            target = target_dir / source.name
            if source.resolve() == target.resolve():
                continue
            if target.exists():
                backup = target.with_name(f"{target.name}.bak.{timestamp}")
                shutil.copy2(target, backup)
            shutil.copy2(source, target)
            migrated += 1
        return migrated

    def _format_log_time(self, created_at: str) -> str:
        try:
            dt = datetime.fromisoformat(created_at)
        except ValueError:
            return created_at
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        target_timezone = self._selected_tzinfo()
        return dt.astimezone(target_timezone).strftime("%Y-%m-%d %H:%M:%S %Z")

    def _selected_tzinfo(self):
        if self.display_timezone == "local":
            return datetime.now().astimezone().tzinfo
        try:
            return ZoneInfo(self.display_timezone)
        except ZoneInfoNotFoundError:
            fallback_offsets = {
                "Asia/Shanghai": timezone(timedelta(hours=8), "CST"),
                "UTC": timezone.utc,
            }
            return fallback_offsets.get(self.display_timezone, timezone.utc)

    def _collect_dependency_statuses(self) -> list[DependencyStatus]:
        statuses: list[DependencyStatus] = []
        if not self.plugins:
            return statuses
        for plugin in self.plugins:
            checker = getattr(plugin, "check_dependencies", None)
            if checker is None:
                statuses.append(
                    DependencyStatus(
                        plugin_id=plugin.metadata.plugin_id,
                        name=self.context.t("dependency.no_check.name"),
                        dependency_type="plugin",
                        required=False,
                        available=True,
                        message=self.context.t("dependency.no_check.message"),
                    )
                )
                continue
            try:
                plugin_statuses = checker(self.context)
            except Exception as exc:
                plugin_statuses = [
                    DependencyStatus(
                        plugin_id=plugin.metadata.plugin_id,
                        name=self.context.t("dependency.no_check.name"),
                        dependency_type="plugin",
                        required=True,
                        available=False,
                        message=str(exc),
                    )
                ]
            if not plugin_statuses:
                plugin_statuses = [
                    DependencyStatus(
                        plugin_id=plugin.metadata.plugin_id,
                        name=self.context.t("dependency.no_external.name"),
                        dependency_type="plugin",
                        required=False,
                        available=True,
                    )
                ]
            statuses.extend(plugin_statuses)
        return statuses

    def _show_dependency_summary(self) -> None:
        window = tk.Toplevel(self)
        window.title(self.context.t("dependency.title"))
        window.geometry("860x400")
        window.columnconfigure(0, weight=1)
        window.rowconfigure(1, weight=1)

        header = ttk.Frame(window, padding=8)
        header.grid(row=0, column=0, sticky="ew")
        ttk.Label(header, text=self.context.t("dependency.title")).grid(row=0, column=0, sticky="w")
        ttk.Button(header, text=self.context.t("dependency.check"), command=lambda: self._refresh_dependency_popup(tree)).grid(
            row=0, column=1, sticky="e", padx=(8, 0)
        )

        columns = ("plugin", "dependency", "type", "required", "status", "version", "path", "message")
        tree = ttk.Treeview(window, columns=columns, show="headings", height=12)
        heading_keys = {
            "plugin": "dependency.plugin",
            "dependency": "dependency.dependency",
            "type": "dependency.type",
            "required": "dependency.required",
            "status": "dependency.status",
            "version": "dependency.version",
            "path": "dependency.path",
            "message": "dependency.message",
        }
        for column, width in (
            ("plugin", 120),
            ("dependency", 90),
            ("type", 100),
            ("required", 60),
            ("status", 80),
            ("version", 180),
            ("path", 180),
            ("message", 200),
        ):
            tree.heading(column, text=self.context.t(heading_keys[column]))
            tree.column(column, width=width, anchor="w")
        tree.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))

        scrollbar = ttk.Scrollbar(window, orient=tk.VERTICAL, command=tree.yview)
        scrollbar.grid(row=1, column=1, sticky="ns", pady=(0, 8))
        tree.configure(yscrollcommand=scrollbar.set)

        tree.bind("<Button-3>", lambda e: self._show_dependency_context_menu_popup(tree, e))

        self._refresh_dependency_popup(tree)

    def _refresh_dependency_popup(self, tree: ttk.Treeview) -> None:
        for item in tree.get_children():
            tree.delete(item)
        statuses = self._collect_dependency_statuses()
        if not statuses:
            tree.insert("", tk.END, values=("", "", "", "", self.context.t("dependency.no_plugins"), "", "", ""))
        else:
            for status in statuses:
                tree.insert(
                    "",
                    tk.END,
                    values=(
                        status.plugin_id,
                        status.name,
                        status.dependency_type,
                        self.context.t("dependency.yes") if status.required else self.context.t("dependency.no"),
                        self.context.t("dependency.available") if status.available else self.context.t("dependency.missing"),
                        status.version,
                        status.path,
                        status.message,
                    ),
                )

    def _show_dependency_context_menu_popup(self, tree: ttk.Treeview, event) -> None:
        item_id = tree.identify_row(event.y)
        if item_id:
            tree.selection_set(item_id)
            tree.focus(item_id)
        else:
            tree.selection_remove(tree.selection())
        menu = tk.Menu(tree, tearoff=0)
        menu.add_command(
            label=self.context.t("logs.context.copy"),
            command=lambda: copy_treeview_selection_to_clipboard(tree, tree),
        )
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _refresh_logs(self, schedule: bool = True) -> None:
        for item in self.log_tree.get_children():
            self.log_tree.delete(item)
        self._log_details.clear()

        time_filter = self.log_time_filter_var.get()
        level_filter = self.log_level_filter_var.get()
        plugin_filter = self.log_plugin_filter_var.get()

        since = self._compute_log_since(time_filter)
        level = None if level_filter == self.context.t("logs.filter.level.all") else level_filter
        plugin_id = None if plugin_filter == self.context.t("logs.filter.plugin.all") else plugin_filter

        for row in self.log_store.query(200, level=level, plugin_id=plugin_id, since=since):
            item_id = self.log_tree.insert(
                "",
                tk.END,
                values=(self._format_log_time(row["created_at"]), row["plugin_id"], row["level"], row["message"]),
            )
            if row["details"]:
                try:
                    import json
                    self._log_details[item_id] = json.loads(row["details"])
                except (json.JSONDecodeError, TypeError):
                    pass
        if schedule:
            if self._log_refresh_after_id is not None:
                self.after_cancel(self._log_refresh_after_id)
            self._log_refresh_after_id = self.after(5000, self._refresh_logs)

    def _compute_log_since(self, time_filter: str) -> str | None:
        now = datetime.now(timezone.utc)
        if time_filter == self.context.t("logs.filter.time.today"):
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            return start.isoformat()
        elif time_filter == self.context.t("logs.filter.time.7days"):
            start = now - timedelta(days=7)
            return start.isoformat()
        elif time_filter == self.context.t("logs.filter.time.30days"):
            start = now - timedelta(days=30)
            return start.isoformat()
        return None

    def _show_log_context_menu(self, event) -> None:
        item_id = self.log_tree.identify_row(event.y)
        if item_id:
            self.log_tree.selection_set(item_id)
            self.log_tree.focus(item_id)
        else:
            self.log_tree.selection_remove(self.log_tree.selection())
        menu = tk.Menu(self.log_tree, tearoff=0)
        menu.add_command(
            label=self.context.t("logs.context.copy"),
            command=lambda: copy_treeview_selection_to_clipboard(self.log_tree, self.log_tree),
        )
        menu.add_command(
            label=self.context.t("logs.context.copy_all"),
            command=self._copy_all_logs,
        )
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _copy_all_logs(self) -> None:
        all_items = self.log_tree.get_children()
        if not all_items:
            return
        columns = self.log_tree["columns"]
        header = "\t".join(self.log_tree.heading(col, option="text") for col in columns)
        lines = [header]
        for item_id in all_items:
            values = self.log_tree.item(item_id, "values")
            lines.append("\t".join(str(v) for v in values))
        self.log_tree.clipboard_clear()
        self.log_tree.clipboard_append("\n".join(lines))

    def _on_log_double_click(self, event) -> None:
        selection = self.log_tree.selection()
        if not selection:
            return
        item_id = selection[0]
        details = self._log_details.get(item_id)
        if not details:
            messagebox.showinfo(
                self.context.t("logs.details.title"),
                self.context.t("logs.details.no_details"),
            )
            return
        self._show_log_details_window(details)

    def _show_log_details_window(self, details: dict) -> None:
        import json
        window = tk.Toplevel(self)
        window.title(self.context.t("logs.details.title"))
        window.geometry("600x400")
        window.columnconfigure(0, weight=1)
        window.rowconfigure(0, weight=1)

        text = tk.Text(window, wrap="word", font=("TkFixedFont", 10))
        text.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(window, orient=tk.VERTICAL, command=text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        text.configure(yscrollcommand=scrollbar.set)

        text.insert("1.0", json.dumps(details, indent=2, ensure_ascii=False))
        text.configure(state=tk.DISABLED)

def main() -> None:
    app = PUtilsApp()
    app.mainloop()
