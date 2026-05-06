from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class PluginMetadata:
    plugin_id: str
    name: str
    description: str
    version: str


@dataclass(frozen=True)
class DependencyStatus:
    plugin_id: str
    name: str
    dependency_type: str
    required: bool
    available: bool
    version: str = ""
    path: str = ""
    message: str = ""


class PluginContext(Protocol):
    def get_config(self, namespace: str, key: str, default: object = None) -> object:
        ...

    def set_config(self, namespace: str, key: str, value: object) -> None:
        ...

    def log(self, plugin_id: str, level: str, message: str, details: dict | None = None) -> None:
        ...

    def t(self, key: str, default: str | None = None, **kwargs: object) -> str:
        ...


class UtilityPlugin(Protocol):
    metadata: PluginMetadata

    def build(self, parent, context: PluginContext):
        ...

    def check_dependencies(self, context: PluginContext) -> list[DependencyStatus]:
        ...
