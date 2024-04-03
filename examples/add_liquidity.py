import argparse
import asyncio
import sys

from solders.pubkey import Pubkey

from orca_whirlpools_py.position_manager import add_liquidity
from utils import get_context
'''
Open a position considering various options.
Command sample
python add_liquidity.py -P 5ebE8hm4g2scC7w7KQGP8z22hMDdkShWVCgE3MHBFSLE -s 0.3 -S 0 -D 0.001
'''
async def main():
    parser = argparse.ArgumentParser(description="Open a position in the specific whirlpool.")
    parser.add_argument("-P", "--position_pubkey", help="Position public key")
    parser.add_argument('-s', "--slippage", type=float, help="acceptable slippage value when deposit", default=0.3)
    parser.add_argument('-S', "--priority_fee", type=float, help="Priority fee(0~1000)", default=0)
    parser.add_argument('-D', "--deposit_amount", type=float, help="Deposit amount when increase liquidity")
    args = parser.parse_args()

    if args.position_pubkey is None or args.deposit_amount is None :
        parser.error("Invalid input parameters. Please check position_pubkey and deposit_amount value.")
        sys.exit(1)
    
    ctx = get_context()
    position_pubkey = Pubkey.from_string(args.position_pubkey)
    await add_liquidity(ctx=ctx, position_pubkey=position_pubkey, slippage=args.slippage, priority_fee=0, deposit_amount='0.01')
        
asyncio.run(main())