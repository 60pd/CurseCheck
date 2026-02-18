import threading, queue, sys, time, string, ctypes, os, requests, random
from requests.adapters import HTTPAdapter
from config import ConfigManager
from Proxy import ProxyHandler

THUMB_URL = "https://i.postimg.cc/T2z9x3ZS/A8DC0327-930F-47C3-AC8C-3F25670A294B.gif"
CYAN = "\033[96m"
WHITE = "\033[97m"
RESET = "\033[0m"

class Curse:
    def __init__(self):
        self.cm = ConfigManager()
        self.stats = {"hits": 0, "taken": 0, "errors": 0, "total": 0, "rps": 0}
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.thread_local = threading.local()
        self.generated_users = set()
        self._load_history()

    def _load_history(self):
        history_file = 'hits.txt'
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                for line in f:
                    u = line.strip()
                    if u: self.generated_users.add(u)

    def _get_session(self):
        if not hasattr(self.thread_local, "session"):
            s = requests.Session()
            s.mount('https://', HTTPAdapter(pool_connections=1, pool_maxsize=1))
            s.headers.update({"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"})
            self.thread_local.session = s
        return self.thread_local.session

    def send_webhook(self, username):
        url = self.cm.WEBHOOK
        if not url or "http" not in url: return
        try:
            payload = {
                "content": "@everyone",
                "embeds": [{
                    "title": "New Hit Found!",
                    "description": f"Username: **{username}**",
                    "color": 0x00FFFF,
                    "thumbnail": {"url": THUMB_URL},
                    "footer": {"text": "Curse Discord Checker"}
                }]
            }
            requests.post(url, json=payload, timeout=5)
        except: pass

    def worker(self, ph):
        session = self._get_session()
        chars = string.ascii_lowercase + string.digits + "_."
        while not self.stop_event.is_set():
            p_dict, p_raw = ph.get_proxy()
            if not p_dict:
                time.sleep(1)
                continue
            while True:
                length = random.choice([3, 4])
                user = ''.join(random.choices(chars, k=length))
                with self.lock:
                    if user not in self.generated_users:
                        self.generated_users.add(user)
                        break
            try:
                r = session.post("https://discord.com/api/v9/unique-username/username-attempt-unauthed",
                                json={"username": user}, proxies=p_dict, timeout=5)
                with self.lock: self.stats["total"] += 1
                if r.status_code == 200:
                    is_taken = r.json().get('taken')
                    if not is_taken:
                        with self.lock: self.stats["hits"] += 1
                        print(f"{WHITE}[{CYAN}+{WHITE}]{RESET} Available : {CYAN}{user.ljust(6)}{RESET} | RPS: {CYAN}{str(self.stats['rps'])}{RESET}")
                        with open('hits.txt', 'a') as f: f.write(f"{user}\n")
                        threading.Thread(target=self.send_webhook, args=(user,), daemon=True).start()
                    else:
                        with self.lock: self.stats["taken"] += 1
                elif r.status_code == 429:
                    time.sleep(5)
                else:
                    ph.report_bad(p_raw)
            except Exception:
                ph.report_bad(p_raw)

    def start(self):
        os.system('cls')
        proxy_path = 'proxies.txt'
        if not os.path.exists(proxy_path):
            print(f"Error: {proxy_path} not found!")
            return
        with open(proxy_path, 'r') as f: pxs = f.readlines()
        ph = ProxyHandler(pxs, self.cm.PROXY_TYPE, self.cm.PROXY_THRESHOLD)
        for _ in range(self.cm.THREADS):
            threading.Thread(target=self.worker, args=(ph,), daemon=True).start()
        try:
            while True:
                curr = self.stats['total']
                time.sleep(1)
                self.stats['rps'] = self.stats['total'] - curr
                ctypes.windll.kernel32.SetConsoleTitleW(f"Hits: {self.stats['hits']} | RPS: {self.stats['rps']}")
        except KeyboardInterrupt:
            self.stop_event.set()

if __name__ == "__main__":
    Curse().start()
