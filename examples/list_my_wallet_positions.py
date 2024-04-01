import asyncio
import json
from typing import NamedTuple
from pathlib import Path

from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.keypair import Keypair

from constants import *
from orca_whirlpools_py.whirlpools import get_positions_by_whrilpool_pubkey

class PositionRelatedAccounts(NamedTuple):
    mint: Pubkey
    token_account: Pubkey
    position: Pubkey


async def main():
    connection = AsyncClient(RPC_ENDPOINT_URL)
    # read wallet
    # - how to create: solana-keygen new -o wallet.json
    # - need some USDC and SOL
    with Path("./wallet_main.json").open() as f:
        keypair = Keypair.from_bytes(bytes(json.load(f)))
    print("wallet pubkey", keypair.pubkey())
    
    positions = await get_positions_by_whrilpool_pubkey(connection=connection, wallet_pubkey=keypair.pubkey())
    for position in positions:
        if position is None:
            continue

        print('{:*^100}'.format("POSITION"))
        
        # print('{:*^20} {:<20} {:<20}'.format(ld.tick_lower_index, ld.tick_upper_index, ld.liquidity))
        print("POSITION")
        print('{:>16} {}'.format("mint:", position['mint']))
        print('{:>16} {}'.format("token_account:", position['token_account']))
        print('{:>16} {}'.format("position_pubkey:", position['position_pubkey']))
        print('{:>16} {}'.format("whirlpool:", position['whirlpool']))
        print('{:>16} {}'.format("token_a:", position['token_a']))
        print('{:>16} {}'.format("token_b:", position['token_b']))
        print('{:>16} {}'.format("token_a:", position['token_a']))
        print('{:>16} {}'.format("liquidity:", position['liquidity']))
        print('{:>16} {}'.format("token_amount_a:", position['token_amount_a']))
        print('{:>16} {}'.format("token_amount_b:", position['token_amount_b']))
        print('{:>16} {}'.format("status:", position['status']))
        # print("  mint:", accounts.mint)
        # print("  token_account:", accounts.token_account)
        # print("  position pubkey:", accounts.position)
        # print("  whirlpool:", position.whirlpool)
        # print("    token_a:", whirlpool.token_mint_a)
        # print("    token_b:", whirlpool.token_mint_b)
        # print("  liquidity:", position.liquidity)
        # print("  token_a(u64):", amounts.token_a)
        # print("  token_b(u64):", amounts.token_b)
        # print("  status:", status)

asyncio.run(main())