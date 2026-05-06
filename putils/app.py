from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .database import ConfigStore, LogStore
from .paths import config_db_path, log_db_path
from .plugin_api import DependencyStatus
from .plugin_loader import discover_plugins


class AppContext:
    def __init__(self, config_store: ConfigStore, log_store: LogStore) -> None:
        self.config_store = config_store
        self.log_store = log_store

    def get_config(self, namespace: str, key: str, default: object = None) -> object:
        return self.config_store.get(namespace, key, default)

    def set_config(self, namespace: str, key: str, value: object) -> None:
        self.config_store.set(namespace, key, value)

    def log(self, plugin_id: str, level: str, message: str, details: dict | None = None) -> None:
        self.log_store.add(plugin_id, level, message, details)


class PUtilsApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("PUtils")
        self.geometry("980x680")
        self.minsize(860, 560)

        self.config_store = ConfigStore(config_db_path())
        self.log_store = LogStore(log_db_path())
        self.context = AppContext(self.config_store, self.log_store)
        self._log_refresh_after_id: str | None = None
        self.plugins = []

        self._configure_style()
        self._build_layout()
        self._load_plugins()
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
        ttk.Label(dependency_header, text="Dependency Status").grid(row=0, column=0, sticky="w")
        ttk.Button(dependency_header, text="Check", command=self._refresh_dependencies).grid(
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
        ttk.Label(header, text="Operation Logs").grid(row=0, column=0, sticky="w")
        ttk.Button(header, text="Refresh", command=lambda: self._refresh_logs(schedule=False)).grid(
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
            ttk.Label(empty, text="No plugins found.").grid(row=0, column=0, sticky="w")
            self.plugin_notebook.add(empty, text="Plugins")
            return

        for plugin in self.plugins:
            frame = ttk.Frame(self.plugin_notebook, padding=12)
            frame.columnconfigure(0, weight=1)
            plugin.build(frame, self.context)
            self.plugin_notebook.add(frame, text=plugin.metadata.name)

    def _refresh_dependencies(self) -> None:
        for item in self.dependency_tree.get_children():
            self.dependency_tree.delete(item)

        if not self.plugins:
            self.dependency_tree.insert("", tk.END, values=("", "", "", "", "No plugins", "", "", ""))
            return

        for plugin in self.plugins:
            checker = getattr(plugin, "check_dependencies", None)
            if checker is None:
                self._insert_dependency_status(
                    DependencyStatus(
                        plugin_id=plugin.metadata.plugin_id,
                        name="Plugin dependency check",
                        dependency_type="plugin",
                        required=False,
                        available=True,
                        message="No dependency check provided",
                    )
                )
                continue
            try:
                statuses = checker(self.context)
            except Exception as exc:
                statuses = [
                    DependencyStatus(
                        plugin_id=plugin.metadata.plugin_id,
                        name="Plugin dependency check",
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
                        name="No external dependencies",
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
                "Yes" if status.required else "No",
                "Available" if status.available else "Missing",
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
