import json
import os
from pathlib import Path

CONFIG_PATH = Path.home() / ".hallucheck.json"


def get_config():
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}


def save_config(config_data):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config_data, f, indent=4)


def get_api_key():
    return os.environ.get("ANTHROPIC_API_KEY") or get_config().get("api_key")
