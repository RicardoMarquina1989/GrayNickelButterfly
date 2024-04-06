import argparse
import asyncio

from solders.pubkey import Pubkey

from constants import SOL_USDC_WHIRLPOOL_PUBKEY
from orca_whirlpools_py.position_manager import close_position
from utils import get_context
'''
Close a position considering various options.
Command sample
Withdraw max amount of tokens
python close_position.py -S 0 -s 0.05 -P 5ebE8hm4g2scC7w7KQGP8z22hMDdkShWVCgE3MHBFSLE
'''
async def main():
    parser = argparse.ArgumentParser(description="Close a position in the specific whirlpool.")
    parser.add_argument("-P", "--position_pubkey", help="Whirlpool public key", default=SOL_USDC_WHIRLPOOL_PUBKEY)
    parser.add_argument('-s', "--slippage", type=float, help="acceptable slippage value when deposit", default=0.3)
    parser.add_argument('-S', "--priority_fee", type=float, help="Priority fee(0~1000)", default=0)
    args = parser.parse_args()

    ctx = get_context()
    position_pubkey = Pubkey.from_string(args.position_pubkey)
    await close_position(ctx=ctx, position_pubkey=position_pubkey, slippage=args.slippage, priority_fee=0)
    
asyncio.run(main())