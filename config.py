import json, os
from pathlib import Path

class ConfigManager:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self._bootstrap()
        self.data = self._load_and_repair()

    def _bootstrap(self):
        for d in ['data', 'logs', 'results']: 
            (self.base_dir / d).mkdir(exist_ok=True)

    def _load_and_repair(self):
        path = self.base_dir / 'data' / 'config.json'
        defaults = {
            "threads": 100, 
            "timeout": [5, 10], 
            "max_retries": 3,
            "webhook": "", 
            "proxy_type": "http", 
            "proxy_threshold": 5,
            "cooldown_base": 60
        }
        
        data = defaults.copy()
        if path.exists():
            try:
                with open(path, 'r') as f:
                    u_data = json.load(f)
                    for k, v in defaults.items():
                        if k in u_data and isinstance(u_data[k], type(v)):
                            data[k] = u_data[k]
            except: pass
        
        data["threads"] = max(1, min(data["threads"], 500))
        with open(path, 'w') as f: 
            json.dump(data, f, indent=4)
            
        return data
