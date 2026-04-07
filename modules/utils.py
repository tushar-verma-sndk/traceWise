import yaml
from pathlib import Path


def load_config():
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)


def ensure_root_structure(base_path):
    Path(base_path).mkdir(parents=True, exist_ok=True)