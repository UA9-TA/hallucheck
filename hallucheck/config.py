import sys

if sys.version_info >= (3, 11):
    import tomllib as tomli
else:
    import tomli

from pathlib import Path
from typing import Any, Dict

import tomli_w

CONFIG_FILE = ".hallucheck.toml"


def load_config(path: str = ".") -> Dict[str, Any]:
    config_path = Path(path) / CONFIG_FILE
    if config_path.exists():
        with open(config_path, "rb") as f:
            return tomli.load(f)
    return {}


def save_config(config: Dict[str, Any], path: str = "."):
    config_path = Path(path) / CONFIG_FILE
    with open(config_path, "wb") as f:
        tomli_w.dump(config, f)
