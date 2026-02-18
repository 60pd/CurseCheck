import threading, queue, sys, time, string, ctypes, os, requests, random
from requests.adapters import HTTPAdapter
from config import ConfigManager
from Proxy import ProxyHandler

WEBHOOK_URL = "Webhook_here_my_baby_ezra"
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
        self.webhook_queue = queue.Queue()
        self.thread_local = threading.local()
        self.generated_users = set()
        self._load_history()

    def _load_history(self):
        history_file = 'results/hits.txt'
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
            
            p_display = f"{CYAN}Curse{'*' * 10}{RESET}"

            try:
                r = session.post("https://discord.com/api/v9/unique-username/username-attempt-unauthed",
                                json={"username": user}, proxies=p_dict, timeout=5)
                
                with self.lock: self.stats["total"] += 1
                rps_val = f"{CYAN}{str(self.stats['rps']).ljust(2)}{RESET}"
                user_val = f"{CYAN}{user.ljust(6)}{RESET}"

                if r.status_code == 200:
                    is_taken = r.json().get('taken')
                    resp_json = f"{CYAN}{{'taken': {is_taken}}}{RESET}"
                    
                    if not is_taken:
                        with self.lock: self.stats["hits"] += 1
                        print(f"{WHITE}[{CYAN}+{WHITE}]{RESET} Available {WHITE}:{RESET} {user_val}{WHITE},{RESET}   RPS {WHITE}:{RESET} {rps_val} {WHITE}/ s,{RESET}   resp {WHITE}:{RESET} {resp_json}{WHITE},{RESET}  proxy {WHITE}:{RESET} {p_display}")
                        with open('results/hits.txt', 'a') as f: f.write(f"{user}\n")
                    else:
                        with self.lock: self.stats["taken"] += 1
                        print(f"{WHITE}[{CYAN}-{WHITE}]{RESET}   Taken   {WHITE}:{RESET} {user_val}{WHITE},{RESET}   RPS {WHITE}:{RESET} {rps_val} {WHITE}/ s,{RESET}   resp {WHITE}:{RESET} {resp_json}{WHITE},{RESET}   proxy {WHITE}:{RESET} {p_display}")
                elif r.status_code == 429:
                    time.sleep(5)
                else:
                    ph.report_bad(p_raw)
            except Exception:
                with self.lock: self.stats["errors"] += 1
                ph.report_bad(p_raw)

    def start(self):
        os.system('cls')
        proxy_path = 'proxies.txt'
        if not os.path.exists(proxy_path):
            print(f"Error: {proxy_path} not found!")
            return

        with open(proxy_path, 'r') as f: pxs = f.readlines()
        ph = ProxyHandler(pxs, self.cm.data["proxy_type"], self.cm.data["proxy_threshold"])
        
        for _ in range(self.cm.data["threads"]):
            t = threading.Thread(target=self.worker, args=(ph,), daemon=True)
            t.start()

        try:
            while True:
                curr = self.stats['total']
                time.sleep(1)
                self.stats['rps'] = self.stats['total'] - curr
                title = f"Requests: {self.stats['total']} | Hits: {self.stats['hits']} | RPS:
