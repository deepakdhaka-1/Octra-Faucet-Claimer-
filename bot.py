#!/usr/bin/env python3

import os
import sys
import time
import requests
import shutil
import functools
from typing import List, Tuple, Optional
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table

console = Console()

# ========= CONFIGURATION ========= #
class Config:
    SOLVER_API_KEY: str = ""  # Will be set via user input
    SOLVER_IN_URL: str = "https://api.solvecaptcha.com/in.php"
    SOLVER_RES_URL: str = "https://api.solvecaptcha.com/res.php"
    FAUCET_CLAIM_URL: str = "https://faucet.octra.network/claim"
    FAUCET_PAGE_URL: str = "https://faucet.octra.network/"
    FAUCET_SITEKEY: str = "6LekoXkrAAAAAMlLCpc2KJqSeUHye6KMxOL5_SES"
    MAX_RETRIES: int = 3
    RETRY_DELAY_SECONDS: int = 5
    WALLET_DELAY_SECONDS: int = 10
    WALLET_LIST_FILE: str = "wallets.txt"

# ========= UTILITY FUNCTIONS ========= #
def clean_project_cache():
    try:
        cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '__pycache__')
        if os.path.isdir(cache_dir):
            shutil.rmtree(cache_dir)
            console.print("[bold yellow]🧹 Cleaned project cache.[/bold yellow]")
    except Exception as e:
        console.print(f"[yellow]Warning: Failed to clean cache - {e}[/yellow]")

def retry_handler(max_retries: int, delay: int):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                if attempt > 0:
                    console.print(f"\n   --- [ Retrying - Attempt {attempt + 1}/{max_retries} ] ---")
                try:
                    if func(*args, **kwargs): return True
                except requests.exceptions.RequestException as e:
                    console.print(f"   [yellow]Connection Error: {e}[/yellow]")
                if attempt < max_retries - 1:
                    console.print(f"   [cyan]Waiting {delay} seconds before next attempt...[/cyan]")
                    time.sleep(delay)
            console.print("[bold red]✗ Permanent failure after all retries.[/bold red]")
            return False
        return wrapper
    return decorator

# ========= CAPTCHA + CLAIM ========= #
def get_captcha_token() -> Optional[str]:
    console.print("   [cyan]1. Requesting CAPTCHA token...[/cyan]")
    payload = {
        'key': Config.SOLVER_API_KEY,
        'method': 'userrecaptcha',
        'googlekey': Config.FAUCET_SITEKEY,
        'pageurl': Config.FAUCET_PAGE_URL,
        'json': 1
    }
    response = requests.post(Config.SOLVER_IN_URL, data=payload, timeout=30)
    response.raise_for_status()
    result = response.json()
    if result.get('status') != 1:
        console.print(f"   [red]Solver Error: {result.get('request')}[/red]")
        return None

    req_id = result['request']
    params = {'key': Config.SOLVER_API_KEY, 'action': 'get', 'id': req_id, 'json': 1}
    end_time = time.time() + 180  # max wait = 3 minutes

    with console.status("[bold green]Waiting for CAPTCHA solution...[/bold green]"):
        while time.time() < end_time:
            time.sleep(5)
            poll = requests.get(Config.SOLVER_RES_URL, params=params, timeout=30)
            poll.raise_for_status()
            poll_result = poll.json()
            if poll_result.get('status') == 1:
                console.print("[green]✓ CAPTCHA successfully solved![/green]")
                return poll_result['request']
            elif poll_result.get('request') != "CAPCHA_NOT_READY":
                console.print(f"[red]Solver Error: {poll_result['request']}[/red]")
                return None
    console.print("[red]✗ Timeout waiting for CAPTCHA (3 minutes).[/red]")
    return None

def claim_faucet(wallet_address: str, captcha_token: str) -> bool:
    console.print(f"   [cyan]2. Submitting faucet claim for[/cyan] [yellow]{wallet_address}[/yellow]")
    form_data = {
        'address': (None, wallet_address),
        'is_validator': (None, 'false'),
        'g-recaptcha-response': (None, captcha_token)
    }
    headers = {'User-Agent': 'Mozilla/5.0'}

    response = requests.post(Config.FAUCET_CLAIM_URL, files=form_data, headers=headers, timeout=30)
    response.raise_for_status()
    try:
        result = response.json()
        if result.get("success"):
            console.print(f"[bold green]✓ Success:[/bold green] {result.get('amount')} | Tx: [cyan]{result.get('tx_hash')[:16]}...[/cyan]")
            return True
        else:
            console.print(f"[red]✗ Failed:[/red] {result.get('error', 'Unknown error')}")
            return False
    except ValueError:
        console.print("[red]✗ Failed: Invalid JSON response from server.[/red]")
        return False

@retry_handler(Config.MAX_RETRIES, Config.RETRY_DELAY_SECONDS)
def process_single_wallet(address: str) -> bool:
    token = get_captcha_token()
    if not token: return False
    return claim_faucet(address, token)

# ========= SUMMARY ========= #
def display_results_summary(successful: List[Tuple[int, str]], failed: List[Tuple[int, str]]):
    text = Text()
    text.append(f"Total Processed: {len(successful) + len(failed)}\n")
    text.append(f"Successful: ", style="bold green"); text.append(f"{len(successful)}\n")
    text.append(f"Failed: ", style="bold red"); text.append(f"{len(failed)}")

    if failed:
        table = Table(title="❌ Failed Wallets")
        table.add_column("No", justify="right", style="cyan")
        table.add_column("Address", style="red")
        for idx, addr in failed:
            table.add_row(str(idx), addr)
        console.print(table)

    console.print(Panel(text, title="📊 Final Summary", border_style="green"))

# ========= MAIN ========= #
def main():
    console.print(Panel("[bold cyan]OCTRA Faucet Auto-Claimer[/bold cyan]\nUsing `wallets.txt` file", title="[yellow]Welcome[/yellow]"))

    # Prompt API Key
    Config.SOLVER_API_KEY = input("🔐 Enter your SolveCaptcha API Key: ").strip()
    if not Config.SOLVER_API_KEY:
        console.print("[red]Error: API Key is required.[/red]")
        sys.exit(1)

    # Load wallet addresses
    if not os.path.isfile(Config.WALLET_LIST_FILE):
        console.print(f"[red]File {Config.WALLET_LIST_FILE} not found.[/red]")
        sys.exit(1)

    with open(Config.WALLET_LIST_FILE, "r", encoding="utf-8") as f:
        wallets = [line.strip() for line in f if line.strip().startswith("oct")]

    if not wallets:
        console.print("[yellow]No valid wallet addresses found.[/yellow]")
        return

    successful = []
    failed = []

    for i, address in enumerate(wallets, 1):
        console.print(f"\n[bold]--- Wallet {i}/{len(wallets)} ---[/bold]")
        success = process_single_wallet(address)
        if success:
            successful.append((i, address))
        else:
            failed.append((i, address))

        clean_project_cache()
        if i < len(wallets):
            console.print(f"[cyan]Waiting {Config.WALLET_DELAY_SECONDS} seconds before next wallet...[/cyan]")
            time.sleep(Config.WALLET_DELAY_SECONDS)

    display_results_summary(successful, failed)

# ========= START ========= #
if __name__ == "__main__":
    main()
