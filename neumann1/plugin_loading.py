from __future__ import annotations

import importlib
import re
from typing import Callable, Any

from .plugin_manifest import PluginActivator, PluginManifest, ActivationPolicy

_ENTRY_POINT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.]*:[A-Za-z_][A-Za-z0-9_]*$")


def resolve_python_entry_point(entry_point: str) -> Callable[..., Any]:
    """Resolve a validated Python module.path:attribute entry point.

    Import occurs only when this function is called. Discovery/catalog code does
    not call this function.
    """
    if not _ENTRY_POINT_RE.fullmatch(entry_point):
        raise ValueError("entry_point must use module.path:attribute syntax")
    module_name, attribute = entry_point.split(":", 1)
    module = importlib.import_module(module_name)
    target = getattr(module, attribute, None)
    if target is None:
        raise AttributeError(
            f"entry point attribute {attribute!r} not found in module {module_name!r}"
        )
    return target


def activate_python_plugin(
    manifest: PluginManifest,
    policy: ActivationPolicy | None = None,
):
    """Explicitly activate one Python plugin manifest."""
    return PluginActivator(resolve_python_entry_point, policy=policy).activate(manifest)
