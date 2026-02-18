import random

class ProxyHandler:
    def __init__(self, proxies, p_type, threshold):
        cleaned = []
        for p in proxies:
            p = p.strip()
            if not p: continue
            if "://" in p: p = p.split("://")[1]
            cleaned.append(p)
        self.proxies = cleaned
        self.p_type = p_type
        self.threshold = threshold
        self.bad_proxies = {}

    def get_proxy(self):
        if not self.proxies: return None, None
        p_raw = random.choice(self.proxies)
        p_dict = {"http": f"{self.p_type}://{p_raw}", "https": f"{self.p_type}://{p_raw}"}
        return p_dict, p_raw

    def report_bad(self, p_raw):
        self.bad_proxies[p_raw] = self.bad_proxies.get(p_raw, 0) + 1
        if self.bad_proxies[p_raw] >= self.threshold:
            if p_raw in self.proxies: self.proxies.remove(p_raw)
