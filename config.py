import json, os, logging
from pathlib import Path

class ConfigManager:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.data = self._initialize()

    def _initialize(self):
        dirs = ['data', 'logs', 'results']
        for d in dirs: (self.base_dir / d).mkdir(exist_ok=True)
        
        path = self.base_dir / 'data' / 'config.json'
        default = {
            "threads": 50, "timeout": [5, 10], "max_retries": 3,
            "webhook": "", "proxy_type": "http", "proxy_threshold": 3
        }

        if path.exists():
            try:
                with open(path, 'r') as f:
                    loaded = json.load(f)
                    # Schema Enforcement
                    for k, v in default.items():
                        if k not in loaded or type(loaded[k]) != type(v):
                            loaded[k] = v
                    return loaded
            except (json.JSONDecodeError, PermissionError):
                return default
        
        with open(path, 'w') as f: json.dump(default, f, indent=4)
        return default

    def save(self):
        try:
            with open(self.base_dir / 'data' / 'config.json', 'w') as f:
                json.dump(self.data, f, indent=4)
        except Exception as e:
            logging.error(f"Failed to save config: {e}")
