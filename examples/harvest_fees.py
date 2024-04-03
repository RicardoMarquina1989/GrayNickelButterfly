import argparse
import asyncio
import sys

from solders.pubkey import Pubkey

from orca_whirlpools_py.position_manager import add_liquidity
from utils import get_context
'''
@func: Collect fees from a position or a whirlpool.
@Command sample
    - Gather from a specific position
    python harvest_fees.py -P 5ebE8hm4g2scC7w7KQGP8z22hMDdkShWVCgE3MHBFSLE
    - Gather from a specific whirlpool
    python harvest_fees.py -W HJPjoWUrhoZzkNfRpHuieeFk9WcZWjwy6PBjZ81ngndJ
'''
async def main():
    parser = argparse.ArgumentParser(description="Open a position in the specific whirlpool.")
    parser.add_argument("-P", "--position_pubkey", help="Position public key")
    parser.add_argument("-W", "--whirlpool_pubkey", help="Whirlpool public key")
    # parser.add_argument('-s', "--slippage", type=float, help="acceptable slippage value when deposit", default=0.3)
    # parser.add_argument('-S', "--priority_fee", type=float, help="Priority fee(0~1000)", default=0)
    # parser.add_argument('-D', "--deposit_amount", type=float, help="Deposit amount when increase liquidity")
    args = parser.parse_args()

    if args.position_pubkey is None and args.whirlpool_pubkey is None :
        parser.error("Invalid input parameters. Please type either position_pubkey or whirlpool_pubkey to harvest.")
        sys.exit(1)
    
    ctx = get_context()
    position_pubkey = Pubkey.from_string(args.position_pubkey)
    await add_liquidity(ctx=ctx, position_pubkey=position_pubkey, slippage=args.slippage, priority_fee=0, deposit_amount='0.01')
        
asyncio.run(main())