import json
import os
from pathlib import Path

DEFAULT_CONFIG = {
    "name": "新腳本",
    "loop_count": 1,
    "start_delay": 3,
    "steps": [],
}


def load(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {**DEFAULT_CONFIG, **data}


def save(filepath, config):
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def new_config():
    import copy
    return copy.deepcopy(DEFAULT_CONFIG)
