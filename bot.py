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
from colorama import *
import asyncio, json, os, pytz

wib = pytz.timezone('Asia/Jakarta')

class Injective:
    def __init__(self) -> None:
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": "https://multivm.injective.com",
            "Referer": "https://multivm.injective.com/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
            "User-Agent": FakeUserAgent().random
        }
        self.BASE_API = "https://jsbqfdd4yk.execute-api.us-east-1.amazonaws.com/v2"
        self.proxies = []
        self.proxy_index = 0
        self.account_proxies = {}
        self.project_id = None # Tambahkan inisialisasi project_id

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    # Modifikasi fungsi log agar bisa menerima do_print_newline
    def log(self, message, do_print_newline=True, end_char="\n"):
        timestamp = datetime.now().astimezone(wib).strftime('%x %X %Z')
        log_message = (
            f"{Fore.CYAN + Style.BRIGHT}[ {timestamp} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}{message}"
        )
        if do_print_newline:
            print(log_message, flush=True, end=end_char)
        else:
            # Hapus baris sebelum mencetak ulang untuk update di tempat
            print(f"\r{' ' * 200}\r{log_message}", flush=True, end=end_char)


    def welcome(self):
        print(
            f"""
        {Fore.GREEN + Style.BRIGHT}Auto Claim Faucet {Fore.BLUE + Style.BRIGHT}Injective - BOT
            """
            f"""
        {Fore.GREEN + Style.BRIGHT}Rey? {Fore.YELLOW + Style.BRIGHT}<INI WATERMARK>
            """
        )

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
            self.log(f"{Fore.RED + Style.BRIGHT}Failed to load project_id.txt: {e}{Style.RESET_ALL}")
            return None
    
    async def load_proxies(self, use_proxy_choice: int):
        filename = "proxy.txt"
        try:
            if use_proxy_choice == 1:
                async with ClientSession(timeout=ClientTimeout(total=30)) as session:
                    async with session.get("https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&proxy_format=protocolipport&format=text") as response:
                        response.raise_for_status()
                        content = await response.text()
                        with open(filename, 'w') as f:
                            f.write(content)
                        self.proxies = [line.strip() for line in content.splitlines() if line.strip()]
            else:
                if not os.path.exists(filename):
                    self.log(f"{Fore.RED + Style.BRIGHT}File {filename} Not Found.{Style.RESET_ALL}")
                    return
                with open(filename, 'r') as f:
                    self.proxies = [line.strip() for line in f.read().splitlines() if line.strip()]
            
            if not self.proxies:
                self.log(f"{Fore.RED + Style.BRIGHT}No Proxies Found.{Style.RESET_ALL}")
                return

            self.log(
                f"{Fore.GREEN + Style.BRIGHT}Proxies Total  : {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{len(self.proxies)}{Style.RESET_ALL}"
            )
        
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}Failed To Load Proxies: {e}{Style.RESET_ALL}")
            self.proxies = []

    def check_proxy_schemes(self, proxies):
        schemes = ["http://", "https://", "socks4://", "socks5://"]
        if any(proxies.startswith(scheme) for scheme in schemes):
            return proxies
        return f"http://{proxies}"

    def get_next_proxy_for_account(self, account):
        if account not in self.account_proxies:
            if not self.proxies:
                return None
            proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
            self.account_proxies[account] = proxy
            self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return self.account_proxies[account]

    def rotate_proxy_for_account(self, account):
        if not self.proxies:
            return None
        proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
        self.account_proxies[account] = proxy
        self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return proxy
        
    def generate_address(self, account_private_key: str):
        try:
            account_obj = Account.from_key(account_private_key)
            address = account_obj.address
            return address
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}Error generating address: {e}{Style.RESET_ALL}")
            return None
    
    def mask_account(self, account):
        try:
            if account is None: # Pastikan account bukan None
                return "None"
            mask_account = account[:6] + '*' * 6 + account[-6:]
            return mask_account
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}Error masking account: {e}{Style.RESET_ALL}")
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
                print(f"{Fore.WHITE + Style.BRIGHT}1. Run With Proxyscrape Free Proxy{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}2. Run With Private Proxy{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}3. Run Without Proxy{Style.RESET_ALL}")
                choose = int(input(f"{Fore.BLUE + Style.BRIGHT}Choose [1/2/3] -> {Style.RESET_ALL}").strip())

                if choose in [1, 2, 3]:
                    proxy_type = (
                        "With Proxyscrape Free" if choose == 1 else 
                        "With Private" if choose == 2 else 
                        "Without"
                    )
                    self.log(f"{Fore.GREEN + Style.BRIGHT}Run {proxy_type} Proxy Selected.{Style.RESET_ALL}")
                    break
                else:
                    self.log(f"{Fore.RED + Style.BRIGHT}Please enter either 1, 2 or 3.{Style.RESET_ALL}")
            except ValueError:
                self.log(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number (1, 2 or 3).{Style.RESET_ALL}")

        rotate = False
        if choose in [1, 2]:
            while True:
                rotate_input = input(f"{Fore.BLUE + Style.BRIGHT}Rotate Invalid Proxy? [y/n] -> {Style.RESET_ALL}").strip().lower() # Ubah nama variabel agar tidak tumpang tindih

                if rotate_input in ["y", "n"]:
                    rotate = rotate_input == "y"
                    break
                else:
                    self.log(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter 'y' or 'n'.{Style.RESET_ALL}")

        return choose, rotate
    
    async def check_connection(self, proxy=None):
        connector = ProxyConnector.from_url(proxy) if proxy else None
        try:
            async with ClientSession(connector=connector, timeout=ClientTimeout(total=30)) as session:
                async with session.post(url="http://ip-api.com/json") as response:
                    response.raise_for_status()
                    return await response.json()
        except (Exception, ClientResponseError) as e:
            self.log(
                f"{Fore.CYAN + Style.BRIGHT}Status:{Style.RESET_ALL}"
                f"{Fore.RED + Style.BRIGHT} Connection Not 200 OK {Style.RESET_ALL}"
                f"{Fore.MAGENTA + Style.BRIGHT}-{Style.RESET_ALL}"
                f"{Fore.YELLOW + Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
            )
            return None
    
    async def claim_faucet(self, address: str, proxy=None, retries=5):
        url = f"{self.BASE_API}/faucet"
        data = json.dumps({"address":self.generate_inj_address(address)})
        headers = {
            **self.headers,
            "Content-Length": str(len(data)),
            "Content-Type": "application/json"
        }
        # Tambahkan project_id (captcha key) ke header jika tersedia
        if self.project_id:
            headers["X-Injective-Grecaptcha-Token"] = self.project_id
            self.log(f"{Fore.MAGENTA + Style.BRIGHT}Adding CAPTCHA token to headers.{Style.RESET_ALL}")


        for attempt in range(retries):
            connector = ProxyConnector.from_url(proxy) if proxy else None
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=headers, data=data, ssl=False) as response:
                        if response.status == 400:
                            self.log(
                                f"{Fore.CYAN + Style.BRIGHT}Faucet:{Style.RESET_ALL}"
                                f"{Fore.YELLOW + Style.BRIGHT} Already Claimed {Style.RESET_ALL}"
                            )
                            return None
                        response.raise_for_status()
                        return await response.text()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    self.log(f"{Fore.YELLOW + Style.BRIGHT}Faucet: Claim attempt {attempt + 1} failed. Retrying in 5 seconds. Error: {str(e)}{Style.RESET_ALL}")
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN + Style.BRIGHT}Faucet:{Style.RESET_ALL}"
                    f"{Fore.RED + Style.BRIGHT} Not Claimed {Style.RESET_ALL}"
                    f"{Fore.MAGENTA + Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW + Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None

    async def process_check_connection(self, address: str, use_proxy: bool, rotate_proxy: bool):
        while True:
            proxy = self.get_next_proxy_for_account(address) if use_proxy else None
            self.log(
                f"{Fore.CYAN + Style.BRIGHT}Proxy :{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} {proxy} {Style.RESET_ALL}"
            )

            check = await self.check_connection(proxy)
            if check and check.get("status") == "success":
                self.log(f"{Fore.GREEN + Style.BRIGHT}Connection check successful.{Style.RESET_ALL}")
                return True
            
            if rotate_proxy:
                self.log(f"{Fore.YELLOW + Style.BRIGHT}Connection check failed. Rotating proxy...{Style.RESET_ALL}")
                proxy = self.rotate_proxy_for_account(address)
                await asyncio.sleep(5)
                continue

            self.log(f"{Fore.RED + Style.BRIGHT}Connection check failed. Not rotating proxy.{Style.RESET_ALL}")
            return False
        
    async def process_accounts(self, account_private_key: str, use_proxy: bool, rotate_proxy: bool):
        address = self.generate_address(account_private_key)
        if not address:
            self.log(
                f"{Fore.RED + Style.BRIGHT}Invalid Private Key or Library Version Not Supported{Style.RESET_ALL}"
            )
            return 

        self.log(
            f"{Fore.CYAN + Style.BRIGHT}Processing account: {self.mask_account(address)}{Style.RESET_ALL}"
        )

        is_valid = await self.process_check_connection(address, use_proxy, rotate_proxy)
        if is_valid:
            proxy = self.get_next_proxy_for_account(address) if use_proxy else None
            self.log(f"{Fore.CYAN + Style.BRIGHT}Attempting to claim faucet...{Style.RESET_ALL}")
            claim = await self.claim_faucet(address, proxy)
            if claim:
                self.log(
                    f"{Fore.CYAN + Style.BRIGHT}Faucet:{Style.RESET_ALL}"
                    f"{Fore.GREEN + Style.BRIGHT} Claimed Successfully {Style.RESET_ALL}"
                )

    async def main(self):
        try:
            with open('accounts.txt', 'r') as file:
                accounts = [line.strip() for line in file if line.strip()]

            project_id = self.load_project_id()
            if project_id:
                self.project_id = project_id

            use_proxy_choice, rotate_proxy = self.print_question()

            use_proxy = False
            if use_proxy_choice in [1, 2]:
                use_proxy = True

            while True:
                self.clear_terminal()
                self.welcome()
                self.log(
                    f"{Fore.GREEN + Style.BRIGHT}Account's Total: {Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT}{len(accounts)}{Style.RESET_ALL}"
                )

                if use_proxy:
                    await self.load_proxies(use_proxy_choice)

                separator = "=" * 25
                for account in accounts:
                    if account:
                        address = self.generate_address(account)
                        self.log(
                            f"{Fore.CYAN + Style.BRIGHT}{separator}[{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} {self.mask_account(address)} {Style.RESET_ALL}"
                            f"{Fore.CYAN + Style.BRIGHT}]{separator}{Style.RESET_ALL}"
                        )

                        if not address:
                            self.log(
                                f"{Fore.CYAN + Style.BRIGHT}Status:{Style.RESET_ALL}"
                                f"{Fore.RED + Style.BRIGHT} Invalid Private Key or Library Version Not Supported {Style.RESET_ALL}"
                            )
                            continue
                        
                        await self.process_accounts(address, use_proxy, rotate_proxy)

                self.log(f"{Fore.CYAN + Style.BRIGHT}={Style.RESET_ALL}"*72)
                
                # Pesan Task Completed
                self.log(f"{Fore.GREEN + Style.BRIGHT}Task Completed ✅ Waiting next Claim 12 Hours{Style.RESET_ALL}")
                
                delay = 12 * 60 * 60
                while delay > 0:
                    formatted_time = self.format_seconds(delay)
                    # Gunakan self.log dengan do_print_newline=False untuk update di tempat
                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}[ Wait for{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {formatted_time} {Style.RESET_ALL}"
                        f"{Fore.CYAN+Style.BRIGHT}... ]{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.YELLOW+Style.BRIGHT}Next Claim In{Style.RESET_ALL}",
                        do_print_newline=False, # Ini kunci untuk update di tempat
                        end_char="" # Pastikan tidak ada karakter baris baru di akhir
                    )
                    await asyncio.sleep(1)
                    delay -= 1
                
                # Setelah countdown selesai, cetak baris baru untuk membersihkan baris countdown terakhir
                print() # Mencetak baris baru
                self.log(f"{Fore.CYAN + Style.BRIGHT}={Style.RESET_ALL}"*72)

        except FileNotFoundError:
            self.log(f"{Fore.RED}File 'accounts.txt' Not Found.{Style.RESET_ALL}")
            return
        except Exception as e:
            self.log(f"{Fore.RED+Style.BRIGHT}Error: {e}{Style.RESET_ALL}")
            raise e

if __name__ == "__main__":
    try:
        bot = Injective()
        asyncio.run(bot.main())
    except KeyboardInterrupt:
        # Pastikan baris bersih sebelum mencetak pesan keluar
        print(f"\r{' ' * 200}\r", end="", flush=True)
        bot.log(
            f"{Fore.RED + Style.BRIGHT}[ EXIT ] Injective - BOT{Style.RESET_ALL}",
            do_print_newline=True # Cetak pesan exit di baris baru
        )
    except Exception as e:
        bot.log(f"{Fore.RED+Style.BRIGHT}Critical error during bot execution: {e}{Style.RESET_ALL}")
