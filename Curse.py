import threading, queue, sys, time, string, ctypes, os, requests, random
from requests.adapters import HTTPAdapter
from config import ConfigManager
from Proxy import ProxyHandler

WEBHOOK_URL = "YOUR_WEBHOOK_HERE"
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

    def _get_session(self):
        if not hasattr(self.thread_local, "session"):
            s = requests.Session()
            s.mount('https://', HTTPAdapter(pool_connections=1, pool_maxsize=1))
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
                        "description": f"Discord Hit: @{username}",
                        "color": 0x00FFFF,
                        "thumbnail": {"url": THUMB_URL}
                    }]
                }
                requests.post(url, json=payload, timeout=10)
                self.webhook_queue.task_done()
            except: continue

    def worker(self, ph):
        session = self._get_session()
        chars = string.ascii_lowercase + string.digits + "_."
        
        while not self.stop_event.is_set():
            # Random Generation with Duplicate Check
            while True:
                length = random.choice([3, 4])
                user = ''.join(random.choices(chars, k=length))
                
                with self.lock:
                    if user not in self.generated_users:
                        self.generated_users.add(user)
                        break
            
            p_dict, p_raw = ph.get_proxy()
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
                        self.webhook_queue.put(user)
                    else:
                        with self.lock: self.stats["taken"] += 1
                        print(f"{WHITE}[{CYAN}-{WHITE}]{RESET}   Taken   {WHITE}:{RESET} {user_val}{WHITE},{RESET}   RPS {WHITE}:{RESET} {rps_val} {WHITE}/ s,{RESET}   resp {WHITE}:{RESET} {resp_json}{WHITE},{RESET}   proxy {WHITE}:{RESET} {p_display}")
                elif r.status_code == 429:
                    time.sleep(r.json().get('retry_after', 5))
            except:
                with self.lock: self.stats["errors"] += 1

    def start(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        
        with open('data/proxies.txt', 'r') as f: pxs = f.readlines()
        ph = ProxyHandler(pxs, self.cm.data["proxy_type"], self.cm.data["proxy_threshold"])
        
        threading.Thread(target=self.webhook_dispatcher, daemon=True).start()
        
        threads = []
        for _ in range(self.cm.data["threads"]):
            t = threading.Thread(target=self.worker, args=(ph,))
            t.daemon = True
            t.start(); threads.append(t)

        try:
            while True:
                curr = self.stats['total']
                time.sleep(1)
                self.stats['rps'] = self.stats['total'] - curr
                ctypes.windll.kernel32.SetConsoleTitleW(f"Requests = {self.stats['total']} | RPS > {self.stats['rps']}")
        except KeyboardInterrupt:
            self.stop_event.set()

if __name__ == "__main__":
    Curse().start()
