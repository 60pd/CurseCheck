import itertools, threading

class ProxyHandler:
    def __init__(self, proxy_list, p_type="http"):
        self.lock = threading.Lock()
        self.p_type = p_type
        self.proxies = list(set([p.strip() for p in proxy_list if p.strip()]))
        self.bad_proxies = set()
        self.cycle = itertools.cycle(self.proxies) if self.proxies else None

    def get_proxy(self):
        if not self.cycle: return None
        with self.lock:
            for _ in range(len(self.proxies)):
                p = next(self.cycle)
                if p not in self.bad_proxies:
                    prefix = f"{self.p_type}://" if "://" not in p else ""
                    return {"http": f"{prefix}{p}", "https": f"{prefix}{p}"}, p
            return None

    def report_bad(self, p_raw):
        with self.lock:
            self.bad_proxies.add(p_raw)
