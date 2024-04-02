import argparse
import asyncio
import sys

from orca_whirlpools_py.position_manager import open_position
from constants import SOL_USDC_WHIRLPOOL_PUBKEY
from utils import get_context

'''
Open a position considering various options.
'''
async def main():
    parser = argparse.ArgumentParser(description="Open a position in the specific whirlpool.")
    parser.add_argument("wallet_pubkey", help="Wallet Public Key")
    args = parser.parse_args()

    if args.wallet_pubkey is None:
        parser.error("Invalid wallet public key")
        sys.exit(1)
    
    ctx = get_context()
    open_position(ctx=ctx, whirlpool_pubkey=SOL_USDC_WHIRLPOOL_PUBKEY)
    # positions = await get_positions_by_whrilpool_pubkey(connection=connection, wallet_pubkey=wallet_pubkey)
    # for position in positions:
    #     if position is None:
    #         continue

    #     print('{:*^80}'.format("POSITION"))        
    #     print('{:>16} {}'.format("mint:", position['mint']))
    #     print('{:>16} {}'.format("token_account:", position['token_account']))
    #     print('{:>16} {}'.format("position_pubkey:", position['position_pubkey']))
    #     print('{:>16} {}'.format("whirlpool:", position['whirlpool']))
    #     print('{:>16} {}'.format("token_a:", position['token_a']))
    #     print('{:>16} {}'.format("token_b:", position['token_b']))
    #     print('{:>16} {}'.format("token_a:", position['token_a']))
    #     print('{:>16} {}'.format("liquidity:", position['liquidity']))
    #     print('{:>16} {}'.format("token_amount_a:", position['token_amount_a']))
    #     print('{:>16} {}'.format("token_amount_b:", position['token_amount_b']))
    #     print('{:>16} {}'.format("status:", position['status']))

asyncio.run(main())