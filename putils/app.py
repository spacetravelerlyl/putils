from __future__ import annotations

import os
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .database import ConfigStore, LogStore
from .i18n import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES, Translator
from .paths import config_db_path, log_db_path, user_data_dir, write_configured_data_dir
from .plugin_api import DependencyStatus
from .plugin_loader import discover_plugins


APP_CONFIG_NAMESPACE = "app"


class AppContext:
    def __init__(self, config_store: ConfigStore, log_store: LogStore, translator: Translator) -> None:
        self.config_store = config_store
        self.log_store = log_store
        self.translator = translator

    def get_config(self, namespace: str, key: str, default: object = None) -> object:
        return self.config_store.get(namespace, key, default)

    def set_config(self, namespace: str, key: str, value: object) -> None:
        self.config_store.set(namespace, key, value)

    def log(self, plugin_id: str, level: str, message: str, details: dict | None = None) -> None:
        self.log_store.add(plugin_id, level, message, details)

    def t(self, key: str, default: str | None = None, **kwargs: object) -> str:
        return self.translator.t(key, default, **kwargs)


class PUtilsApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.geometry("980x680")
        self.minsize(860, 560)

        self.config_store = ConfigStore(config_db_path())
        self.log_store = LogStore(log_db_path())
        language = str(self.config_store.get(APP_CONFIG_NAMESPACE, "language", DEFAULT_LANGUAGE))
        self.translator = Translator(language)
        self.context = AppContext(self.config_store, self.log_store, self.translator)
        self._log_refresh_after_id: str | None = None
        self.plugins = []
        self.plugin_panels: list[object] = []
        self.empty_plugin_label = None
        self.settings_frame = None
        self.settings_tab_index: int | None = None
        self.language_display_to_code: dict[str, str] = {}
        self.language_code_to_display: dict[str, str] = {}

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

    def _build_layout(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        root = ttk.PanedWindow(self, orient=tk.VERTICAL)
        root.grid(row=0, column=0, sticky="nsew")

        main_frame = ttk.Frame(root, padding=8)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        root.add(main_frame, weight=4)

        dependency_frame = ttk.Frame(main_frame)
        dependency_frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        dependency_frame.columnconfigure(0, weight=1)

        dependency_header = ttk.Frame(dependency_frame)
        dependency_header.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        dependency_header.columnconfigure(0, weight=1)
        self.dependency_title_label = ttk.Label(dependency_header)
        self.dependency_title_label.grid(row=0, column=0, sticky="w")
        self.dependency_check_button = ttk.Button(dependency_header, command=self._refresh_dependencies)
        self.dependency_check_button.grid(
            row=0, column=1, sticky="e"
        )

        dependency_columns = ("plugin", "dependency", "type", "required", "status", "version", "path", "message")
        self.dependency_tree = ttk.Treeview(
            dependency_frame,
            columns=dependency_columns,
            show="headings",
            height=4,
        )
        for column, width in (
            ("plugin", 145),
            ("dependency", 145),
            ("type", 90),
            ("required", 80),
            ("status", 90),
            ("version", 130),
            ("path", 220),
            ("message", 260),
        ):
            self.dependency_tree.heading(column, text=column)
            self.dependency_tree.column(column, width=width, anchor="w")
        self.dependency_tree.grid(row=1, column=0, sticky="ew")

        self.plugin_notebook = ttk.Notebook(main_frame)
        self.plugin_notebook.grid(row=1, column=0, sticky="nsew")

        log_frame = ttk.Frame(root, padding=8)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(1, weight=1)
        root.add(log_frame, weight=1)

        header = ttk.Frame(log_frame)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 6))
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
        self.log_tree.grid(row=1, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_tree.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.log_tree.configure(yscrollcommand=scrollbar.set)

    def _load_plugins(self) -> None:
        self.plugins = discover_plugins()
        self._refresh_dependencies()
        if not self.plugins:
            empty = ttk.Frame(self.plugin_notebook, padding=16)
            self.empty_plugin_label = ttk.Label(empty)
            self.empty_plugin_label.grid(row=0, column=0, sticky="w")
            self.plugin_notebook.add(empty, text=self.context.t("plugins.tab"))
        else:
            for plugin in self.plugins:
                frame = ttk.Frame(self.plugin_notebook, padding=12)
                frame.columnconfigure(0, weight=1)
                panel = plugin.build(frame, self.context)
                self.plugin_panels.append(panel)
                self.plugin_notebook.add(
                    frame,
                    text=self.context.t(f"plugin.{plugin.metadata.plugin_id}.name", plugin.metadata.name),
                )
        self._add_settings_page()

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

        self.settings_data_dir_label = ttk.Label(frame)
        self.settings_data_dir_label.grid(row=2, column=0, sticky="w", pady=(0, 8))
        self.data_dir_var = tk.StringVar(value=str(user_data_dir()))
        self.data_dir_entry = ttk.Entry(frame, textvariable=self.data_dir_var)
        self.data_dir_entry.grid(row=2, column=1, sticky="ew", pady=(0, 8))
        self.data_dir_browse_button = ttk.Button(frame, command=self._choose_data_dir)
        self.data_dir_browse_button.grid(row=2, column=2, sticky="e", padx=(8, 0), pady=(0, 8))

        self.settings_config_db_label = ttk.Label(frame)
        self.settings_config_db_label.grid(row=3, column=0, sticky="w", pady=(0, 8))
        self.config_db_var = tk.StringVar(value=str(config_db_path()))
        ttk.Entry(frame, textvariable=self.config_db_var, state="readonly").grid(
            row=3, column=1, columnspan=2, sticky="ew", pady=(0, 8)
        )

        self.settings_log_db_label = ttk.Label(frame)
        self.settings_log_db_label.grid(row=4, column=0, sticky="w", pady=(0, 8))
        self.log_db_var = tk.StringVar(value=str(log_db_path()))
        ttk.Entry(frame, textvariable=self.log_db_var, state="readonly").grid(
            row=4, column=1, columnspan=2, sticky="ew", pady=(0, 8)
        )

        self.settings_hint_label = ttk.Label(frame, wraplength=720)
        self.settings_hint_label.grid(row=5, column=0, columnspan=3, sticky="w", pady=(2, 10))

        self.settings_save_button = ttk.Button(frame, command=self._save_settings)
        self.settings_save_button.grid(row=6, column=1, sticky="w")

        self.plugin_notebook.add(frame, text=self.context.t("settings.tab"))
        self.settings_tab_index = self.plugin_notebook.index("end") - 1

    def _apply_language(self) -> None:
        self.title(self.context.t("app.title"))

        self.dependency_title_label.configure(text=self.context.t("dependency.title"))
        self.dependency_check_button.configure(text=self.context.t("dependency.check"))
        dependency_headings = {
            "plugin": "dependency.plugin",
            "dependency": "dependency.dependency",
            "type": "dependency.type",
            "required": "dependency.required",
            "status": "dependency.status",
            "version": "dependency.version",
            "path": "dependency.path",
            "message": "dependency.message",
        }
        for column, key in dependency_headings.items():
            self.dependency_tree.heading(column, text=self.context.t(key))

        self.logs_title_label.configure(text=self.context.t("logs.title"))
        self.logs_refresh_button.configure(text=self.context.t("logs.refresh"))
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
            self.plugin_notebook.tab(0, text=self.context.t("plugins.tab"))

        for index, plugin in enumerate(self.plugins):
            self.plugin_notebook.tab(
                index,
                text=self.context.t(f"plugin.{plugin.metadata.plugin_id}.name", plugin.metadata.name),
            )
        self._apply_settings_language()
        for panel in self.plugin_panels:
            language_setter = getattr(panel, "set_language", None)
            if language_setter is not None:
                language_setter()
        self._refresh_dependencies()

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
        self.settings_data_dir_label.configure(text=self.context.t("settings.data_dir"))
        self.settings_config_db_label.configure(text=self.context.t("settings.config_db"))
        self.settings_log_db_label.configure(text=self.context.t("settings.log_db"))
        self.data_dir_browse_button.configure(text=self.context.t("settings.browse"))
        self.settings_save_button.configure(text=self.context.t("settings.save"))
        hint = self.context.t("settings.restart_hint")
        if os.environ.get("PUTILS_DATA_DIR"):
            hint = f"{hint} {self.context.t('settings.env_override')}"
        self.settings_hint_label.configure(text=hint)
        if self.settings_tab_index is not None:
            self.plugin_notebook.tab(self.settings_tab_index, text=self.context.t("settings.tab"))

    def _on_language_selected(self, _event=None) -> None:
        selected = self.language_var.get()
        next_language = self.language_display_to_code.get(selected)
        if not next_language or next_language == self.translator.language:
            return
        self.translator.set_language(next_language)
        self.config_store.set(APP_CONFIG_NAMESPACE, "language", next_language)
        self._apply_language()

    def _choose_data_dir(self) -> None:
        selected = filedialog.askdirectory(
            title=self.context.t("settings.select_data_dir"),
            initialdir=self.data_dir_var.get() or str(user_data_dir()),
        )
        if selected:
            self.data_dir_var.set(str(Path(selected).expanduser().resolve()))

    def _save_settings(self) -> None:
        try:
            data_dir = Path(self.data_dir_var.get()).expanduser().resolve()
            data_dir.mkdir(parents=True, exist_ok=True)
            write_configured_data_dir(data_dir)
            self.config_store.set(APP_CONFIG_NAMESPACE, "configured_data_dir", str(data_dir))
        except Exception as exc:
            messagebox.showerror(self.context.t("settings.error.title"), str(exc))
            return
        messagebox.showinfo(
            self.context.t("settings.saved.title"),
            self.context.t("settings.saved.message"),
        )

    def _refresh_dependencies(self) -> None:
        for item in self.dependency_tree.get_children():
            self.dependency_tree.delete(item)

        if not self.plugins:
            self.dependency_tree.insert(
                "", tk.END, values=("", "", "", "", self.context.t("dependency.no_plugins"), "", "", "")
            )
            return

        for plugin in self.plugins:
            checker = getattr(plugin, "check_dependencies", None)
            if checker is None:
                self._insert_dependency_status(
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
                statuses = checker(self.context)
            except Exception as exc:
                statuses = [
                    DependencyStatus(
                        plugin_id=plugin.metadata.plugin_id,
                        name=self.context.t("dependency.no_check.name"),
                        dependency_type="plugin",
                        required=True,
                        available=False,
                        message=str(exc),
                    )
                ]
            if not statuses:
                statuses = [
                    DependencyStatus(
                        plugin_id=plugin.metadata.plugin_id,
                        name=self.context.t("dependency.no_external.name"),
                        dependency_type="plugin",
                        required=False,
                        available=True,
                    )
                ]
            for status in statuses:
                self._insert_dependency_status(status)

    def _insert_dependency_status(self, status: DependencyStatus) -> None:
        self.dependency_tree.insert(
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

    def _refresh_logs(self, schedule: bool = True) -> None:
        for item in self.log_tree.get_children():
            self.log_tree.delete(item)
        for row in self.log_store.recent(200):
            self.log_tree.insert(
                "",
                tk.END,
                values=(row["created_at"], row["plugin_id"], row["level"], row["message"]),
            )
        if schedule:
            if self._log_refresh_after_id is not None:
                self.after_cancel(self._log_refresh_after_id)
            self._log_refresh_after_id = self.after(5000, self._refresh_logs)


def main() -> None:
    app = PUtilsApp()
    app.mainloop()
