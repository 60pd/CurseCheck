import os

class ConfigManager:
    def __init__(self):
        self.WEBHOOK = ""
        self.THREADS = 150
        self.PROXY_TYPE = "http"
        self.PROXY_THRESHOLD = 5

        if not os.path.exists('hits.txt'):
            with open('hits.txt', 'w') as f: pass
