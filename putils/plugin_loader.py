from __future__ import annotations

import importlib
import pkgutil
from types import ModuleType

# Changed from relative import to absolute import for PyInstaller compatibility
from putils.plugin_api import UtilityPlugin


def _load_module(module_name: str) -> ModuleType:
    return importlib.import_module(module_name)


def discover_plugins() -> list[UtilityPlugin]:
    package_name = "putils.plugins"
    package = _load_module(package_name)
    plugins: list[UtilityPlugin] = []

    for module_info in pkgutil.iter_modules(package.__path__, f"{package_name}."):
        if module_info.ispkg:
            continue
        module = _load_module(module_info.name)
        factory = getattr(module, "create_plugin", None)
        if factory is None:
            continue
        plugins.append(factory())

    return plugins

