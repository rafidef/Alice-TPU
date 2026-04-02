#!/usr/bin/env python3
"""
Alice Protocol Wallet CLI

用法:
  python3 alice_wallet.py balance
  python3 alice_wallet.py transfer <to_address> <amount>
  python3 alice_wallet.py info
"""

import argparse
import json
import sys
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from substrateinterface import SubstrateInterface, Keypair
except ImportError:
    print("Missing dependency: pip install substrate-interface")
    sys.exit(1)

DEFAULT_CHAIN_URL = os.environ.get("ALICE_CHAIN_URL", "wss://rpc.aliceprotocol.org")
WALLET_PATH = Path.home() / ".alice" / "wallet.json"
SS58_FORMAT = 300
TOKEN_DECIMALS = 12  # adjust based on chain config
TOKEN_SYMBOL = "ALICE"


def load_wallet(password: str = None) -> Keypair:
    """Load wallet from ~/.alice/wallet.json"""
    if not WALLET_PATH.exists():
        print(f"❌ Wallet not found: {WALLET_PATH}")
        print(f"   Create one with: python3 miner/alice_wallet.py create")
        sys.exit(1)

    try:
        data = json.loads(WALLET_PATH.read_text())
    except Exception as e:
        print(f"❌ Failed to read wallet: {e}")
        sys.exit(1)

    # Try loading seed/mnemonic from wallet data
    seed = data.get("seed") or data.get("mnemonic") or data.get("secret_seed")

    if not seed:
        # Encrypted wallet — need password
        try:
            from core.secure_wallet import load_wallet as load_secure
            wallet_data = load_secure(password)
            seed = wallet_data.get("seed") or wallet_data.get("mnemonic")
        except Exception:
            # Try environment variable
            seed = os.environ.get("ALICE_MINER_SEED")

    if not seed:
        print("❌ Cannot load wallet. Set ALICE_MINER_SEED environment variable.")
        sys.exit(1)

    try:
        if seed.startswith("0x") or len(seed) == 64:
            kp = Keypair.create_from_seed(seed, ss58_format=SS58_FORMAT)
        elif len(seed.split()) >= 12:
            kp = Keypair.create_from_mnemonic(seed, ss58_format=SS58_FORMAT)
        else:
            kp = Keypair.create_from_uri(seed, ss58_format=SS58_FORMAT)
        return kp
    except Exception as e:
        print(f"❌ Failed to create keypair: {e}")
        sys.exit(1)


def create_wallet():
    """Create a new wallet"""
    if WALLET_PATH.exists():
        print(f"⚠️  Wallet already exists: {WALLET_PATH}")
        confirm = input("Overwrite? (type 'yes' to confirm): ")
        if confirm.lower() != 'yes':
            print("Cancelled.")
            return

    mnemonic = Keypair.generate_mnemonic()
    kp = Keypair.create_from_mnemonic(mnemonic, ss58_format=SS58_FORMAT)

    WALLET_PATH.parent.mkdir(parents=True, exist_ok=True)
    wallet_data = {
        "address": kp.ss58_address,
        "mnemonic": mnemonic,
        "ss58_format": SS58_FORMAT,
    }
    WALLET_PATH.write_text(json.dumps(wallet_data, indent=2))
    os.chmod(WALLET_PATH, 0o600)

    print(f"✅ Wallet created!")
    print(f"   Address:  {kp.ss58_address}")
    print(f"   Mnemonic: {mnemonic}")
    print(f"   Saved to: {WALLET_PATH}")
    print()
    print(f"⚠️  BACK UP YOUR MNEMONIC! If lost, your tokens are gone forever.")


def connect_chain(url: str) -> SubstrateInterface:
    """Connect to Alice chain"""
    try:
        substrate = SubstrateInterface(url=url)
        return substrate
    except Exception as e:
        print(f"❌ Cannot connect to chain: {url}")
        print(f"   Error: {e}")
        sys.exit(1)


def format_balance(raw: int) -> str:
    """Format raw balance to human readable"""
    if TOKEN_DECIMALS > 0:
        value = raw / (10 ** TOKEN_DECIMALS)
        return f"{value:,.{min(4, TOKEN_DECIMALS)}f} {TOKEN_SYMBOL}"
    return f"{raw} {TOKEN_SYMBOL}"


def cmd_balance(args):
    """Show wallet balance"""
    kp = load_wallet()
    substrate = connect_chain(args.chain_url)

    result = substrate.query("System", "Account", [kp.ss58_address])
    data = result.value.get("data", {})

    free = int(data.get("free", 0))
    reserved = int(data.get("reserved", 0))
    total = free + reserved

    print(f"   Address:  {kp.ss58_address}")
    print(f"   Free:     {format_balance(free)}")
    print(f"   Reserved: {format_balance(reserved)}")
    print(f"   Total:    {format_balance(total)}")


def cmd_transfer(args):
    """Transfer ALICE tokens"""
    kp = load_wallet()
    substrate = connect_chain(args.chain_url)

    to_address = args.to
    amount = int(float(args.amount) * (10 ** TOKEN_DECIMALS))

    # Validate destination address
    try:
        Keypair(ss58_address=to_address, ss58_format=SS58_FORMAT)
    except Exception:
        print(f"❌ Invalid Alice address: {to_address}")
        print(f"   Alice addresses start with 'a'")
        sys.exit(1)

    # Check balance
    result = substrate.query("System", "Account", [kp.ss58_address])
    free = int(result.value.get("data", {}).get("free", 0))

    if free < amount:
        print(f"❌ Insufficient balance: {format_balance(free)}")
        print(f"   Trying to send: {format_balance(amount)}")
        sys.exit(1)

    # Confirm
    print(f"   From:   {kp.ss58_address}")
    print(f"   To:     {to_address}")
    print(f"   Amount: {format_balance(amount)}")
    print()
    confirm = input("Confirm transfer? (type 'yes'): ")
    if confirm.lower() != 'yes':
        print("Cancelled.")
        return

    # Execute transfer
    try:
        call = substrate.compose_call(
            call_module="Balances",
            call_function="transfer_keep_alive",
            call_params={
                "dest": to_address,
                "value": amount,
            },
        )

        extrinsic = substrate.create_signed_extrinsic(call=call, keypair=kp)
        receipt = substrate.submit_extrinsic(extrinsic, wait_for_inclusion=True)

        if receipt.is_success:
            tx_hash = getattr(receipt, "extrinsic_hash", "unknown")
            print(f"✅ Transfer successful!")
            print(f"   TX: {tx_hash}")
        else:
            print(f"❌ Transfer failed: {receipt.error_message}")

    except Exception as e:
        print(f"❌ Transfer error: {e}")


def cmd_info(args):
    """Show wallet and chain info"""
    kp = load_wallet()
    substrate = connect_chain(args.chain_url)

    # Chain info
    chain = substrate.rpc_request("system_chain", [])
    version = substrate.rpc_request("system_version", [])
    health = substrate.rpc_request("system_health", [])

    print(f"   Chain:   {chain.get('result', 'unknown')}")
    print(f"   Version: {version.get('result', 'unknown')}")
    print(f"   Peers:   {health.get('result', {}).get('peers', 0)}")
    print()
    print(f"   Wallet:  {kp.ss58_address}")
    print(f"   File:    {WALLET_PATH}")


def cmd_create(args):
    """Create new wallet"""
    create_wallet()


def main():
    parser = argparse.ArgumentParser(
        description="Alice Protocol Wallet",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 alice_wallet.py balance
  python3 alice_wallet.py transfer a2vRdm… 100.5
  python3 alice_wallet.py info
  python3 alice_wallet.py create
""",
    )
    parser.add_argument(
        "--chain-url",
        default=DEFAULT_CHAIN_URL,
        help=f"Chain WebSocket URL (default: {DEFAULT_CHAIN_URL})",
    )

    subparsers = parser.add_subparsers(dest="command", help="Command")

    # balance
    subparsers.add_parser("balance", help="Show wallet balance")

    # transfer
    p_transfer = subparsers.add_parser("transfer", help="Transfer ALICE tokens")
    p_transfer.add_argument("to", help="Destination address (starts with 'a')")
    p_transfer.add_argument("amount", help="Amount of ALICE to send")

    # info
    subparsers.add_parser("info", help="Show wallet and chain info")

    # create
    subparsers.add_parser("create", help="Create new wallet")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    commands = {
        "balance": cmd_balance,
        "transfer": cmd_transfer,
        "info": cmd_info,
        "create": cmd_create,
    }

    print()
    print(f"   Alice Wallet")
    print(f"   {'='*40}")
    commands[args.command](args)
    print()


if __name__ == "__main__":
    main()
