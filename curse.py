import threading, queue, sys, time, string, itertools, ctypes, os, requests, random
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from config import ConfigManager
from Proxy import ProxyHandler

WEBHOOK_URL = "YOUR_WEBHOOK_HERE"
THUMB_URL = "https://i.postimg.cc/T2z9x3ZS/A8DC0327-930F-47C3-AC8C-3F25670A294B.gif"

class Curse:
    def __init__(self):
        self.cm = ConfigManager()
        self.stats = {"hits": 0, "taken": 0, "errors": 0, "total": 0, "rps": 0}
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.webhook_queue = queue.Queue()
        self.thread_local = threading.local()
        self.start_time = time.time()

    def _get_session(self):
        if not hasattr(self.thread_local, "session"):
            s = requests.Session()
            retries = Retry(total=0)
            s.mount('http://', HTTPAdapter(pool_connections=1, pool_maxsize=1, max_retries=retries))
            s.headers.update({"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"})
            self.thread_local.session = s
        return self.thread_local.session

    def webhook_dispatcher(self):
        url = WEBHOOK_URL if WEBHOOK_URL != "YOUR_WEBHOOK_HERE" else self.cm.data.get("webhook")
        while not self.stop_event.is_set() or not self.webhook_queue.empty():
            try:
                if not url: break
                username = self.webhook_queue.get(timeout=2)
                payload = {
                    "content": "@everyone",
                    "embeds": [{
                        "description": f"[+] user : @{username}\nurl : https://tellonym.me/{username}",
                        "color": 0xFFFFFF,
                        "thumbnail": {"url": THUMB_URL}
                    }]
                }
                res = requests.post(url, json=payload, timeout=10)
                if res.status_code == 429:
                    time.sleep(res.json().get('retry_after', 5))
                    self.webhook_queue.put(username)
                self.webhook_queue.task_done()
            except queue.Empty: continue
            except: pass

    def username_gen(self, length):
        chars = string.ascii_lowercase + string.digits + "_."
        for combo in itertools.product(chars, repeat=length):
            if self.stop_event.is_set(): break
            yield "".join(combo)

    def worker(self, q, ph):
        session = self._get_session()
        while not self.stop_event.is_set():
            try:
                user, retries = q.get(timeout=1)
            except queue.Empty: break

            if retries > self.cm.data["max_retries"]:
                with self.lock: self.stats["errors"] += 1
                q.task_done(); continue

            p_dict, p_raw = ph.get_proxy()
            if not p_dict:
                time.sleep(2)
                q.put((user, retries)); q.task_done(); continue

            try:
                r = session.post("https://discord.com/api/v9/unique-username/username-attempt-unauthed",
                                json={"username": user}, proxies=p_dict, timeout=tuple(self.cm.data["timeout"]))
                
                with self.lock: self.stats["total"] += 1
                if r.status_code == 200:
                    data = r.json()
                    if not data.get('taken'):
                        with self.lock: self.stats["hits"] += 1
                        print(f"\033[92m[+] HIT: {user.ljust(15)} | RPS: {self.stats['rps']}\033[0m")
                        with open('results/hits.txt', 'a') as f: f.write(f"{user}\n")
                        self.webhook_queue.put(user)
                    else:
                        with self.lock: self.stats["taken"] += 1
                elif r.status_code == 429:
                    time.sleep(r.json().get('retry_after', 5) + 1)
                    q.put((user, retries + 1))
                else:
                    ph.report_bad(p_raw)
                    q.put((user, retries + 1))
            except:
                ph.report_bad(p_raw)
                q.put((user, retries + 1))
            q.task_done()

    def start(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"\033[95mCURSE - HARDENED PRODUCTION ENGINE\033[0m")
        
        with open('data/proxies.txt', 'r') as f: pxs = f.readlines()
        ph = ProxyHandler(pxs, self.cm.data["proxy_type"], self.cm.data["proxy_threshold"])
        
        q = queue.Queue(maxsize=10000)
        
        threading.Thread(target=self.webhook_dispatcher, daemon=True).start()
        
        threads = []
        for _ in range(self.cm.data["threads"]):
            t = threading.Thread(target=self.worker, args=(q, ph))
            t.start(); threads.append(t)

        def producer():
            length = int(input("User Length: ") or 3)
            for u in self.username_gen(length):
                if self.stop_event.is_set(): break
                q.put((u, 0))
        
        threading.Thread(target=producer, daemon=True).start()

        try:
            while any(t.is_alive() for t in threads):
                curr = self.stats['total']
                time.sleep(1)
                self.stats['rps'] = self.stats['total'] - curr
                title = f"Curse | Hits: {self.stats['hits']} | RPS: {self.stats['rps']}"
                if os.name == 'nt': ctypes.windll.kernel32.SetConsoleTitleW(title)
        except KeyboardInterrupt:
            self.stop_event.set()
        
        print(f"\n[!] Shutting down Curse...")
        for t in threads: t.join()

if __name__ == "__main__":
    Curse().start()
