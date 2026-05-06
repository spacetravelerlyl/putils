# PUtils Development Guide

## Goals

PUtils is a cross-platform desktop utility host for Windows and Linux. It provides:

- A GUI shell for utility plugins.
- SQLite-based application configuration storage.
- SQLite-based operation logging in a separate database.
- A bundled ffmpeg plugin that batch-adjusts video saturation.
- A plugin-provided dependency check mechanism displayed by the host UI.
- Internationalized UI text with Chinese as the default language and English as the first alternate language.

## Technology Selection

| Area | Choice | Reason |
| --- | --- | --- |
| Language | Python 3.10+ | Cross-platform, simple packaging, rich standard library. |
| GUI | Tkinter / ttk | Bundled with Python on common Windows and Linux distributions. |
| Configuration DB | sqlite3 | Standard library support, no server process, portable files. |
| Operation Log DB | sqlite3 | Separate DB isolates logs from configuration and allows independent retention later. |
| Plugin Model | Python modules with `create_plugin()` | Minimal runtime overhead and easy extension. |
| Internationalization | Translation keys in `putils/i18n.py` | Simple to extend and available to plugins through `context.t(...)`. |
| Video Processing | External `ffmpeg` executable | Mature codec support and predictable CLI behavior. |

## Directory Layout

```text
putils/
  __main__.py              # python -m putils entry
  app.py                   # Tkinter application shell
  database.py              # ConfigStore and LogStore
  i18n.py                  # Translation catalog and translator
  paths.py                 # Cross-platform data paths and database directory locator
  plugin_api.py            # Plugin contracts
  plugin_loader.py         # Bundled plugin discovery
  plugins/
    video_saturation.py    # Bundled ffmpeg saturation plugin
docs/
  development.md
  user-guide.md
```

## Design Plan

1. Keep the host application small: UI shell, plugin discovery, configuration access, and logging access.
2. Give each plugin a metadata object and a `build(parent, context)` method.
3. Let each plugin provide dependency status checks for external commands or libraries.
4. Resolve visible UI text through translation keys. Chinese is the default language.
5. Store configuration in `config.sqlite3` under a namespaced key-value table.
6. Store operation logs in `logs.sqlite3` under an append-only operation log table.
7. Let video processing run in a background thread so the GUI remains responsive.
8. Use `ffmpeg -vf eq=saturation=<ratio> -c:a copy` for saturation changes.
9. Produce output filenames as `<original>_saturation_adjusted.<ext>`.

## SQLite Files

By default, data is stored under:

- Windows: `%APPDATA%\PUtils`
- Linux: `$XDG_DATA_HOME/putils` or `~/.local/share/putils`

You can override the data directory for development:

```bash
PUTILS_DATA_DIR=/tmp/putils-dev python -m putils
```

The effective data directory is resolved in this order:

1. `PUTILS_DATA_DIR` environment variable.
2. The locator file in the platform default data directory.
3. The platform default data directory.

The locator file is a small JSON file named `data_dir.json`. It is required because the application must know where `config.sqlite3` is before it can open the SQLite configuration database.

Changing the database directory from the Settings page writes the locator file and takes effect after application restart. The application does not migrate existing database files automatically.
When the database directory field differs from the active runtime directory, the Settings page shows a migration button. Migration copies `config.sqlite3` and `logs.sqlite3` to the target directory and backs up any existing target files with a `.bak.<timestamp>` suffix before overwriting.

Configuration database:

```sql
CREATE TABLE settings (
    namespace TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (namespace, key)
);
```

Log database:

```sql
CREATE TABLE operation_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    plugin_id TEXT NOT NULL,
    level TEXT NOT NULL,
    message TEXT NOT NULL,
    details TEXT
);
```

## Plugin Contract

A plugin module should expose:

```python
def create_plugin():
    return MyPlugin()
```

The plugin object must provide:

```python
metadata = PluginMetadata(
    plugin_id="my_plugin",
    name="My Plugin",
    description="Short description.",
    version="0.1.0",
)

def build(self, parent, context):
    ...

def check_dependencies(self, context):
    return [
        DependencyStatus(
            plugin_id="my_plugin",
            name="my-command",
            dependency_type="external command",
            required=True,
            available=True,
            version="1.0.0",
            path="/usr/bin/my-command",
            message="Ready",
        )
    ]
```

The host application displays dependency status in the main window. The host does not know how to inspect plugin-specific requirements; dependency information and checks are owned by plugins.

The `context` object provides:

- `get_config(namespace, key, default=None)`
- `set_config(namespace, key, value)`
- `log(plugin_id, level, message, details=None)`
- `t(key, default=None, **kwargs)`

## Internationalization

The application uses `putils/i18n.py` as the translation catalog. Chinese (`zh`) is the default language. English (`en`) is currently available through the language switch button in the main window.

The selected language is stored in the configuration database:

```text
namespace: app
key: language
```

Language selection is managed from the Settings page. The language change is applied immediately and persisted to `config.sqlite3`.

## Log Timezone

Operation logs are stored in UTC by `LogStore`. The main window converts `created_at` values to the timezone configured in Settings when rendering the log table.

The display format matches:

```bash
date "+%Y-%m-%d %H:%M:%S %Z"
```

Example:

```text
2026-05-06 15:30:00 CST
```

The configured timezone is stored in `config.sqlite3`:

```text
namespace: app
key: timezone
```

### Adding A Language

To add another language:

1. Add the language code to `SUPPORTED_LANGUAGES` in `putils/i18n.py`.
2. Add a matching entry to `TRANSLATIONS`.
3. Provide translations for all existing keys.
4. Add any new plugin keys under a stable prefix such as `plugin_id.feature.label`.

Example:

```python
SUPPORTED_LANGUAGES = ("zh", "en", "ja")

TRANSLATIONS = {
    "ja": {
        "app.title": "PUtils",
        "...": "...",
    },
}
```

### Plugin UI Text

Plugins should not hard-code visible text. Use `context.t(...)`:

```python
ttk.Label(self, text=context.t("my_plugin.input_file")).grid(...)
```

For dynamic text:

```python
context.t("my_plugin.selected_count", count=3)
```

Translation entry:

```python
"my_plugin.selected_count": "已选择 {count} 个文件"
```

If a plugin needs to update existing widgets after language switching, implement `set_language()` on the plugin panel:

```python
class MyPluginPanel(ttk.Frame):
    def set_language(self) -> None:
        self.run_button.configure(text=self.context.t("my_plugin.run"))
```

The host calls `set_language()` automatically for plugin panels when the language changes.

## Dependency Status

Use `DependencyStatus` for plugin dependency checks:

```python
DependencyStatus(
    plugin_id="video_saturation",
    name="ffmpeg",
    dependency_type="external command",
    required=True,
    available=True,
    version="ffmpeg version ...",
    path="/usr/bin/ffmpeg",
    message="Ready",
)
```

Recommended dependency types:

- `external command`
- `python library`
- `system library`
- `service`

The bundled video saturation plugin checks `ffmpeg` with `shutil.which("ffmpeg")` and `ffmpeg -version`.

## Adding A New Plugin

Bundled plugins live in:

```text
putils/plugins/
```

Create a new Python file in that directory. The filename should be a valid Python module name, for example:

```text
putils/plugins/image_resize.py
```

The host discovers bundled plugins automatically by scanning `putils.plugins` modules. A module is loaded as a plugin only when it exposes `create_plugin()`.

### Minimal Plugin Template

```python
from __future__ import annotations

from tkinter import ttk

from putils.plugin_api import DependencyStatus, PluginMetadata


PLUGIN_ID = "my_plugin"
CONFIG_NAMESPACE = "plugin.my_plugin"


class MyPlugin:
    metadata = PluginMetadata(
        plugin_id=PLUGIN_ID,
        name="My Plugin",
        description="Short plugin description.",
        version="0.1.0",
    )

    def build(self, parent, context):
        return MyPluginPanel(parent, context)

    def check_dependencies(self, context) -> list[DependencyStatus]:
        return []


class MyPluginPanel(ttk.Frame):
    def __init__(self, parent, context) -> None:
        super().__init__(parent)
        self.context = context
        self.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)

        self.title_label = ttk.Label(self)
        self.title_label.grid(row=0, column=0, sticky="w")
        self.set_language()

    def set_language(self) -> None:
        self.title_label.configure(text=self.context.t("my_plugin.title"))


def create_plugin() -> MyPlugin:
    return MyPlugin()
```

### Plugin Metadata

Each plugin must define stable metadata:

- `plugin_id`: stable machine-readable ID. Use lowercase words separated by underscores.
- `name`: display name used by the tab title.
- `description`: short human-readable description.
- `version`: plugin version.

Do not change `plugin_id` after releasing a plugin unless you also migrate existing configuration and logs.

### UI Development

`build(parent, context)` receives a Tkinter parent frame and should return a widget.

Recommended pattern:

```python
class MyPluginPanel(ttk.Frame):
    def __init__(self, parent, context) -> None:
        super().__init__(parent)
        self.context = context
        self.grid(row=0, column=0, sticky="nsew")
```

Use `ttk` widgets where possible so the plugin matches the host application's theme.

If the plugin runs long work, run it in a background thread and update Tk widgets through `widget.after(...)`. Tkinter widgets and variables should not be read or mutated directly from worker threads.

For long-running batch tasks, expose progress in the plugin UI with a progress indicator and a textual status label. The video saturation plugin uses a custom Canvas progress bar so progress color is consistent across Windows and Linux themes.

### Configuration

Use the provided context to read and write plugin configuration:

```python
value = context.get_config(CONFIG_NAMESPACE, "my_key", "default")
context.set_config(CONFIG_NAMESPACE, "my_key", value)
```

Use a namespace based on the plugin ID:

```python
CONFIG_NAMESPACE = "plugin.my_plugin"
```

Configuration is stored in `config.sqlite3`. Values are JSON-serialized by `ConfigStore`, so use JSON-compatible values such as strings, numbers, booleans, lists, and dictionaries.

### Operation Logs

Use the provided context for operation logs:

```python
context.log(
    PLUGIN_ID,
    "INFO",
    "Operation completed",
    {"input": "/path/input.txt", "output": "/path/output.txt"},
)
```

Use levels such as:

- `INFO`
- `WARNING`
- `ERROR`

Logs are stored in `logs.sqlite3`, separate from configuration.

### Dependency Checks

Plugins own their dependency checks. The host only displays the returned status rows.

For an external command:

```python
import shutil
import subprocess


def check_dependencies(self, context) -> list[DependencyStatus]:
    tool_path = shutil.which("my-tool")
    if not tool_path:
        return [
            DependencyStatus(
                plugin_id=PLUGIN_ID,
                name="my-tool",
                dependency_type="external command",
                required=True,
                available=False,
                message="Install my-tool and make sure it is on PATH.",
            )
        ]

    result = subprocess.run(
        [tool_path, "--version"],
        check=True,
        capture_output=True,
        text=True,
        timeout=5,
    )
    version = result.stdout.splitlines()[0] if result.stdout else ""

    return [
        DependencyStatus(
            plugin_id=PLUGIN_ID,
            name="my-tool",
            dependency_type="external command",
            required=True,
            available=True,
            version=version,
            path=tool_path,
            message="Ready",
        )
    ]
```

For a Python library:

```python
import importlib.util


def check_dependencies(self, context) -> list[DependencyStatus]:
    available = importlib.util.find_spec("some_package") is not None
    return [
        DependencyStatus(
            plugin_id=PLUGIN_ID,
            name="some_package",
            dependency_type="python library",
            required=True,
            available=available,
            message="Ready" if available else "Install some_package.",
        )
    ]
```

### Error Handling

Plugin code should catch expected runtime failures and write operation logs. For example:

```python
try:
    run_work()
except Exception as exc:
    context.log(PLUGIN_ID, "ERROR", "Operation failed", {"error": str(exc)})
```

Avoid letting long-running task exceptions terminate silently in background threads.

### Development Checklist

Before considering a plugin complete:

- Add a module under `putils/plugins/`.
- Define stable `PLUGIN_ID` and `CONFIG_NAMESPACE`.
- Provide `metadata`.
- Provide `create_plugin()`.
- Implement `build(parent, context)`.
- Implement `check_dependencies(context)`.
- Use `context.t(...)` for visible text.
- Implement `set_language()` if the plugin creates widgets whose text must change after language switching.
- Store user-facing settings through `context.set_config(...)`.
- Write start, success, and failure logs through `context.log(...)`.
- Show progress for long-running operations.
- Keep long-running work off the Tkinter main thread.
- Run `python -m compileall -q putils`.

## Running From Source

```bash
python -m putils
```

For the video saturation plugin, install `ffmpeg` and make sure `ffmpeg` is on `PATH`.

## Packaging Notes

Recommended packaging tool: PyInstaller.

Example:

```bash
python -m pip install pyinstaller
pyinstaller --name PUtils --windowed --collect-submodules putils putils/__main__.py
```

Linux distributions may require a Tkinter package, for example `python3-tk` on Debian/Ubuntu.
