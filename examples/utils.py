import json
from pathlib import Path

from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair

from orca_whirlpool.constants import ORCA_WHIRLPOOL_PROGRAM_ID
from orca_whirlpool.context import WhirlpoolContext

from constants import *

"""
    Read wallet from file and return the keypair.
    Select one wallet based on APP_ENV.
"""
def get_context() -> WhirlpoolContext:   
    wallet_path = ("wallet.json", "wallet_main.json")[APP_ENV == "main"]
    with Path(wallet_path).open() as f:
        keypair = Keypair.from_bytes(bytes(json.load(f)))
    print(f"wallet pubkey {keypair.pubkey()}")

    connection = AsyncClient(RPC_ENDPOINT_URL)  # Create Solana RPC client
    ctx = WhirlpoolContext(ORCA_WHIRLPOOL_PROGRAM_ID, connection, keypair)  # Create Whirlpool context
    return ctx