"""
shared/utils/config_loader.py
-----------------------------
Cross-language utility for loading the global YAML configuration and the
extensions JSON registry.  Both Python modules and test suites import this
helper so that configuration is always read from a single source of truth.

Usage
-----
    from shared.utils.config_loader import load_config, load_extensions

    config     = load_config()           # dict from config/config.yaml
    extensions = load_extensions()       # list from config/extensions.json
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

try:
    import yaml  # PyYAML
    _YAML_AVAILABLE = True
except ImportError:  # pragma: no cover
    _YAML_AVAILABLE = False


# Resolve repository root relative to this file's location
_REPO_ROOT = Path(__file__).resolve().parents[2]
_CONFIG_YAML = _REPO_ROOT / "config" / "config.yaml"
_EXTENSIONS_JSON = _REPO_ROOT / "config" / "extensions.json"


def load_config(path: str | os.PathLike | None = None) -> Dict[str, Any]:
    """Load and return the global YAML configuration as a dictionary.

    Parameters
    ----------
    path:
        Optional override path to a YAML config file.  Defaults to
        ``config/config.yaml`` at the repository root.

    Returns
    -------
    dict
        Parsed configuration.

    Raises
    ------
    ImportError
        If PyYAML is not installed.
    FileNotFoundError
        If the config file does not exist.
    """
    if not _YAML_AVAILABLE:
        raise ImportError(
            "PyYAML is required to load YAML configuration. "
            "Install it with: pip install pyyaml"
        )
    config_path = Path(path) if path else _CONFIG_YAML
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with config_path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def load_extensions(path: str | os.PathLike | None = None) -> List[Dict[str, Any]]:
    """Load and return the extensions registry as a list of dicts.

    Parameters
    ----------
    path:
        Optional override path to the extensions JSON file.  Defaults to
        ``config/extensions.json`` at the repository root.

    Returns
    -------
    list
        List of extension descriptors.

    Raises
    ------
    FileNotFoundError
        If the extensions file does not exist.
    """
    ext_path = Path(path) if path else _EXTENSIONS_JSON
    if not ext_path.exists():
        raise FileNotFoundError(f"Extensions file not found: {ext_path}")
    with ext_path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    return data.get("extensions", [])


def get_enabled_extensions(path: str | os.PathLike | None = None) -> List[Dict[str, Any]]:
    """Return only extensions that have ``"enabled": true``.

    Parameters
    ----------
    path:
        Optional override path to the extensions JSON file.

    Returns
    -------
    list
        Enabled extension descriptors.
    """
    return [ext for ext in load_extensions(path) if ext.get("enabled", False)]
