from aiohttp import (
    ClientResponseError,
    ClientSession,
    ClientTimeout
)
from aiohttp_socks import ProxyConnector
from fake_useragent import FakeUserAgent
from bech32 import bech32_encode, convertbits
from eth_account import Account
from datetime import datetime
from colorama import init, Fore, Style
import asyncio, json, os, pytz
from dotenv import load_dotenv

# Initialize colorama for auto-resetting colors
init(autoreset=True)
load_dotenv()

# === Terminal Color Setup ===
class Colors:
    RESET = Style.RESET_ALL
    BOLD = Style.BRIGHT
    GREEN = Fore.GREEN
    YELLOW = Fore.YELLOW
    RED = Fore.RED
    CYAN = Fore.CYAN
    MAGENTA = Fore.MAGENTA
    BLUE = Fore.BLUE
    WHITE = Fore.WHITE
    BRIGHT_GREEN = Fore.LIGHTGREEN_EX
    BRIGHT_MAGENTA = Fore.LIGHTMAGENTA_EX
    BRIGHT_WHITE = Fore.LIGHTWHITE_EX
    BRIGHT_BLACK = Fore.LIGHTBLACK_EX

class Logger:
    @staticmethod
    def log(label, symbol, msg, color):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"{Colors.BRIGHT_BLACK}[{timestamp}]{Colors.RESET} {color}[{symbol}] {msg}{Colors.RESET}")

    @staticmethod
    def info(msg): Logger.log("INFO", "✓", msg, Colors.GREEN)
    @staticmethod
    def warn(msg): Logger.log("WARN", "!", msg, Colors.YELLOW)
    @staticmethod
    def error(msg): Logger.log("ERR", "✗", msg, Colors.RED)
    @staticmethod
    def success(msg): Logger.log("OK", "+", msg, Colors.GREEN)
    @staticmethod
    def loading(msg): Logger.log("LOAD", "⟳", msg, Colors.CYAN)
    @staticmethod
    def step(msg): Logger.log("STEP", "➤", msg, Colors.WHITE)
    @staticmethod
    def swap(msg): Logger.log("SWAP", "↪️", msg, Colors.CYAN)
    @staticmethod
    def swapSuccess(msg): Logger.log("SWAP", "✅", msg, Colors.GREEN)

logger = Logger()

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

async def display_welcome_screen():
    clear_console()
    now = datetime.now()
    print(f"{Colors.BRIGHT_GREEN}{Colors.BOLD}")
    print("  ╔══════════════════════════════════════╗")
    print("  ║         D Z A P   B O T              ║")
    print("  ║                                      ║")
    print(f"  ║       {Colors.YELLOW}{now.strftime('%H:%M:%S %d.%m.%Y')}{Colors.BRIGHT_GREEN}         ║")
    print("  ║                                      ║")
    print("  ║       MONAD TESTNET AUTOMATION       ║")
    print(f"  ║   {Colors.BRIGHT_WHITE}ZonaAirdrop{Colors.BRIGHT_GREEN}  |  t.me/ZonaAirdr0p   ║")
    print("  ╚══════════════════════════════════════╝")
    print(f"{Colors.RESET}")
    await asyncio.sleep(1)

eastern_asia_timezone = pytz.timezone('Asia/Jakarta')

class FaucetAutomationCore:
    def __init__(self, initial_headers: dict = None) -> None:
        self._http_headers = {
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://multivm.injective.com/",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "User-Agent": FakeUserAgent().random,
            "Origin": "https://multivm.injective.com",
        }
        if initial_headers:
            self._http_headers.update(initial_headers)

        self.api_base_url = "https://jsbqfdd4yk.execute-api.us-east-1.amazonaws.com/v2"
        self.proxy_list = []
        self.current_proxy_idx = 0
        self.account_proxy_mapping = {}
        self.project_id = None # Inisialisasi project_id di sini

    def log(self, message, level="info"):
        if level == "info":
            logger.info(message)
        elif level == "warn":
            logger.warn(message)
        elif level == "error":
            logger.error(message)
        elif level == "success":
            logger.success(message)
        elif level == "loading":
            logger.loading(message)
        elif level == "step":
            logger.step(message)
        elif level == "swap":
            logger.swap(message)
        elif level == "swapSuccess":
            logger.swapSuccess(message)
        else:
            print(message, flush=True)

    def format_seconds(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
    
    def load_project_id(self):
        try:
            with open("project_id.txt", 'r') as file:
                captcha_key = file.read().strip()
            return captcha_key
        except Exception as e:
            self.log(f"Failed to load project_id.txt: {e}", level="error")
            return None
    
    async def load_proxies(self, use_proxy_choice: int):
        filename = "proxy.txt"
        try:
            if use_proxy_choice == 1: # This is now "Run With Private Proxy"
                if not os.path.exists(filename):
                    logger.error(f"File {filename} Not Found.")
                    return
                with open(filename, 'r') as f:
                    self.proxy_list = [line.strip() for line in f.read().splitlines() if line.strip()]
            
            if not self.proxy_list and use_proxy_choice == 1:
                logger.warn("No Private Proxies Found in proxy.txt.")
                return

            if use_proxy_choice == 1:
                logger.info(f"Proxies Total: {len(self.proxy_list)}")
        
        except Exception as e:
            logger.error(f"Failed To Load Proxies: {e}")
            self.proxy_list = []

    def check_proxy_schemes(self, proxies):
        schemes = ["http://", "https://", "socks4://", "socks5://"]
        if any(proxies.startswith(scheme) for scheme in schemes):
            return proxies
        return f"http://{proxies}"

    def get_next_proxy_for_account(self, account):
        if account not in self.account_proxy_mapping:
            if not self.proxy_list:
                return None
            proxy = self.check_proxy_schemes(self.proxy_list[self.current_proxy_idx])
            self.account_proxy_mapping[account] = proxy
            self.current_proxy_idx = (self.current_proxy_idx + 1) % len(self.proxy_list)
        return self.account_proxy_mapping[account]

    def rotate_proxy_for_account(self, account):
        if not self.proxy_list:
            return None
        proxy = self.check_proxy_schemes(self.proxy_list[self.current_proxy_idx])
        self.account_proxy_mapping[account] = proxy
        self.current_proxy_idx = (self.current_proxy_idx + 1) % len(self.proxy_list)
        return proxy
        
    def generate_address(self, account_private_key: str):
        try:
            # Pastikan kunci privat adalah string heksadesimal yang benar
            # Account.from_key() bisa menerima dengan atau tanpa '0x' prefix
            account_obj = Account.from_key(account_private_key)
            address = account_obj.address
            return address
        except Exception as e:
            logger.error(f"Error generating address: {e}")
            return None
    
    def mask_account(self, address: str):
        # Memastikan address bukan None sebelum mencoba mengiris string
        if address is None:
            return "None" # Atau string lain yang menunjukkan kesalahan
        try:
            mask_address = address[:6] + '*' * 6 + address[-6:]
            return mask_address
        except Exception as e:
            logger.error(f"Error masking account: {e}")
            return "Error Masking"

    def generate_inj_address(self, address: str):
        try:
            if not address.startswith("0x") or len(address) != 42:
                raise ValueError("Invalid Ethereum address")

            evm_bytes = bytes.fromhex(address[2:])
            bech32_words = convertbits(evm_bytes, 8, 5)
            injective_address = bech32_encode("inj", bech32_words)

            return injective_address
        except Exception as e:
            raise Exception(f"Generate Injective Address Failed: {str(e)}")

    def print_question(self):
        while True:
            try:
                # Hanya ada 2 pilihan sekarang
                print(f"{Colors.WHITE}{Colors.BOLD}1. Run With Private Proxy{Colors.RESET}")
                print(f"{Colors.WHITE}{Colors.BOLD}2. Run Without Proxy{Colors.RESET}")
                choose = int(input(f"{Colors.BLUE}{Colors.BOLD}Choose [1/2] -> {Colors.RESET}").strip())

                if choose in [1, 2]:
                    proxy_type = (
                        "With Private" if choose == 1 else 
                        "Without"
                    )
                    logger.info(f"Run {proxy_type} Proxy Selected.")
                    break
                else:
                    logger.error("Please enter either 1 or 2.")
            except ValueError:
                logger.error("Invalid input. Enter a number (1 or 2).")

        rotate = False
        if choose == 1: # Rotate hanya jika memilih Private Proxy
            while True:
                rotate_input = input(f"{Colors.BLUE}{Colors.BOLD}Rotate Invalid Proxy? [y/n] -> {Colors.RESET}").strip().lower()

                if rotate_input in ["y", "n"]:
                    rotate = rotate_input == "y"
                    break
                else:
                    logger.error("Invalid input. Enter 'y' or 'n'.")

        return choose, rotate
    
    async def check_connection(self, proxy=None):
        connector = ProxyConnector.from_url(proxy) if proxy else None
        try:
            async with ClientSession(connector=connector, timeout=ClientTimeout(total=30)) as session:
                async with session.post(url="http://ip-api.com/json") as response:
                    response.raise_for_status()
                    return await response.json()
        except (Exception, ClientResponseError) as e:
            logger.warn(f"Connection Not 200 OK - {str(e)}")
            return None
    
    async def claim_faucet(self, address: str, proxy=None, retries=5):
        url = f"{self.api_base_url}/faucet"
        data = json.dumps({"address": self.generate_inj_address(address)})
        
        # Inisialisasi headers dengan _http_headers
        headers = {
            **self._http_headers,
            "Content-Length": str(len(data)),
            "Content-Type": "application/json"
        }
        
        # Tambahkan project_id (captcha key) ke header jika tersedia
        if self.project_id:
            headers["X-Injective-Grecaptcha-Token"] = self.project_id # Asumsi nama header
            logger.info(f"Adding CAPTCHA token to headers.") # Logging untuk debug

        for attempt in range(retries):
            connector = ProxyConnector.from_url(proxy) if proxy else None
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=headers, data=data, ssl=False) as response:
                        if response.status == 400:
                            logger.warn("Faucet: Already Claimed")
                            return None
                        response.raise_for_status()
                        return await response.text()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    logger.warn(f"Faucet: Claim attempt {attempt + 1} failed. Retrying in 5 seconds. Error: {str(e)}")
                    await asyncio.sleep(5)
                    continue
                logger.error(f"Faucet: Not Claimed - {str(e)}")
        return None

    async def process_check_connection(self, address: str, use_proxy: bool, rotate_proxy: bool):
        while True:
            proxy = self.get_next_proxy_for_account(address) if use_proxy else None
            if proxy:
                logger.step(f"Using proxy: {proxy}")
            else:
                logger.step("No proxy being used.")

            check = await self.check_connection(proxy)
            if check and check.get("status") == "success":
                logger.success("Connection check successful.")
                return True
            
            if rotate_proxy:
                logger.warn("Connection check failed. Rotating proxy...")
                proxy = self.rotate_proxy_for_account(address)
                await asyncio.sleep(5)
                continue
            else:
                logger.error("Connection check failed. Not rotating proxy.")
            return False
        
    async def process_accounts(self, account_private_key: str, use_proxy: bool, rotate_proxy: bool):
        address = self.generate_address(account_private_key)
        # Tambahkan pemeriksaan di sini untuk alamat yang tidak valid
        if not address:
            logger.error("Invalid Private Key or Library Version Not Supported")
            return 

        logger.step(f"Processing account: {self.mask_account(address)}")

        is_valid = await self.process_check_connection(address, use_proxy, rotate_proxy)
        if is_valid:
            proxy = self.get_next_proxy_for_account(address) if use_proxy else None
            logger.loading("Attempting to claim faucet...")
            claim = await self.claim_faucet(address, proxy)
            if claim:
                logger.success("Faucet: Claimed Successfully")

    async def run_faucet_bot(self):
        try:
            await display_welcome_screen()

            with open('accounts.txt', 'r') as file:
                accounts = [line.strip() for line in file if line.strip()]

            # Panggil load_project_id untuk memuat CAPTCHA key
            project_id = self.load_project_id()
            if project_id:
                self.project_id = project_id # Simpan CAPTCHA key ke instance bot

            use_proxy_choice, rotate_proxy = self.print_question()

            use_proxy = False
            if use_proxy_choice == 1: 
                use_proxy = True

            while True:
                await display_welcome_screen()
                logger.info(f"Account's Total: {len(accounts)}")

                if use_proxy:
                    await self.load_proxies(use_proxy_choice) 
                
                for account_private_key in accounts: 
                    await self.process_accounts(account_private_key, use_proxy, rotate_proxy)

                delay = 12 * 60 * 60
                while delay > 0:
                    formatted_time = self.format_seconds(delay)
                    print(
                        f"{Colors.CYAN}{Colors.BOLD}[ Wait for{Colors.RESET}"
                        f"{Colors.WHITE}{Colors.BOLD} {formatted_time} {Colors.RESET}"
                        f"{Colors.CYAN}{Colors.BOLD}... ]{Colors.RESET}"
                        f"{Colors.WHITE}{Colors.BOLD} | {Colors.RESET}"
                        f"{Colors.YELLOW}{Colors.BOLD}All Accounts Have Been Processed...{Colors.RESET}       ",
                        end="\r",
                        flush=True
                    )
                    await asyncio.sleep(1)
                    delay -= 1
                
                print("\n")
                logger.info("=" * 72)

        except FileNotFoundError:
            logger.error("File 'accounts.txt' Not Found.")
            return
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            raise e

if __name__ == "__main__":
    try:
        faucet_runner_instance = FaucetAutomationCore()
        asyncio.run(faucet_runner_instance.run_faucet_bot())
    except KeyboardInterrupt:
        logger.info("[ EXIT ] Injective Faucet Bot Terminated.")
    except Exception as e:
        logger.error(f"Critical error during bot execution: {e}")
