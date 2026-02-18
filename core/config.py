import json, os
from pathlib import Path

class ConfigManager:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.dirs = ['data', 'logs', 'results']
        self.config_path = self.base_dir / 'data/config.json'
        self.setup()
        self.data = self.load()

    def setup(self):
        for d in self.dirs: (self.base_dir / d).mkdir(exist_ok=True)
        for f in ['proxies.txt', 'User.txt']: (self.base_dir / 'data' / f).touch()

    def load(self):
        default = {"threads": 50, "timeout": (5, 15), "max_retries": 3, "webhook": "", "proxy_type": "http"}
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f: return {**default, **json.load(f)}
            except: return default
        return default

    def save(self, data):
        with open(self.config_path, 'w') as f: json.dump(data, f, indent=4)
