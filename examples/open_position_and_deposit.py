import argparse
import asyncio

from solders.pubkey import Pubkey

from constants import SOL_USDC_WHIRLPOOL_PUBKEY
from orca_whirlpools_py.position_manager import open_position
from utils import get_context
'''
Open a position considering various options.
Command sample
python open_position_and_deposit.py -U 300 -L 100 -D 0.01 -S 0 -s 50 -W HJPjoWUrhoZzkNfRpHuieeFk9WcZWjwy6PBjZ81ngndJ
'''
async def main():
    parser = argparse.ArgumentParser(description="Open a position in the specific whirlpool.")
    parser.add_argument("-U", "--upper", help="Upper end of position")
    parser.add_argument("-L", "--lower", help="Lower end of position")
    parser.add_argument("-W", "--whirlpool_pubkey", help="Whirlpool public key", default=SOL_USDC_WHIRLPOOL_PUBKEY)
    parser.add_argument('-s', "--slippage", type=float, help="acceptable slippage value when deposit", default=0.3)
    parser.add_argument('-S', "--priority_fee", type=float, help="Priority fee(0~1000)", default=0)
    parser.add_argument('-D', "--deposit_amount", type=float, help="Deposit amount when increase liquidity")
    args = parser.parse_args()

    if args.upper is None or args.lower is None or args.deposit_amount is None :
        parser.error("Invalid input parameters. Please check upper, lower, and deposit_amount value.")
    
    ctx = get_context()
    whirlpool_pubkey = Pubkey.from_string(args.whirlpool_pubkey)
    await open_position(ctx=ctx, whirlpool_pubkey=whirlpool_pubkey, upper=args.upper, lower=args.lower, slippage=args.slippage, priority_fee=0, deposit_amount='0.01')
    
asyncio.run(main())