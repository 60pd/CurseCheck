import json, os
from pathlib import Path

class ConfigManager:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self._bootstrap()
        self.data = self._load_and_repair()

    def _bootstrap(self):
        for d in ['data', 'logs', 'results']: (self.base_dir / d).mkdir(exist_ok=True)
        for f in ['data/proxies.txt', 'data/User.txt']:
            if not (self.base_dir / f).exists(): (self.base_dir / f).touch()

    def _load_and_repair(self):
        path = self.base_dir / 'data' / 'config.json'
        defaults = {
            "threads": 100, "timeout": [5, 10], "max_retries": 5,
            "webhook": "", "proxy_type": "http", "proxy_threshold": 3,
            "cooldown_base": 60
        }
        data = defaults.copy()
        if path.exists():
            try:
                with open(path, 'r') as f:
                    user_data = json.load(f)
                    for k, v in defaults.items():
                        if k in user_data and type(user_data[k]) == type(v):
                            data[k] = user_data[k]
            except: pass
        
        # Final validation
        data["threads"] = max(1, min(data["threads"], 500))
        with open(path, 'w') as f: json.dump(data, f, indent=4)
        return data
