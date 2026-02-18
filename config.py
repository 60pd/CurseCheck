import json, os
from pathlib import Path

class ConfigManager:
    def __init__(self):
        self.dirs = ['data', 'logs', 'results']
        self.config_path = 'data/config.json'
        self.setup()
        self.data = self.load()

    def setup(self):
        for d in self.dirs: os.makedirs(d, exist_ok=True)
        for f in ['data/proxies.txt', 'data/User.txt']:
            if not os.path.exists(f): Path(f).touch()

    def load(self):
        default = {
            "threads": 50, 
            "timeout": [5, 15], 
            "max_retries": 3, 
            "webhook": "", 
            "proxy_type": "http"
        }
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f: return {**default, **json.load(f)}
            except: return default
        return default

    def save(self, data):
        with open(self.config_path, 'w', encoding='utf-8') as f: 
            json.dump(data, f, indent=4)
