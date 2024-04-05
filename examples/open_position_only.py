import argparse
import asyncio

from orca_whirlpools_py.position_manager import open_position_only
from constants import SOL_USDC_WHIRLPOOL_PUBKEY
from utils import get_context

'''
Open a position considering various options.
Sample command
python open_position_only.py -U 300 -L 100 -W HJPjoWUrhoZzkNfRpHuieeFk9WcZWjwy6PBjZ81ngndJ
'''
async def main():
    parser = argparse.ArgumentParser(description="Open a position in the specific whirlpool.")
    parser.add_argument("-W", "--whirlpool_pubkey", help="Whirlpool public key", default=SOL_USDC_WHIRLPOOL_PUBKEY)
    parser.add_argument("-U", "--upper", help="Upper end of position")
    parser.add_argument("-L", "--lower", help="Lower end of position")
    args = parser.parse_args()

    if args.upper is None or args.lower is None:
        parser.error("Invalid input parameters. Please check upper, lower value.")
    
    ctx = get_context()
    await open_position_only(ctx=ctx, whirlpool_pubkey=SOL_USDC_WHIRLPOOL_PUBKEY, upper=args.upper, lower=args.lower)
    
asyncio.run(main())
''' Sample output
wallet pubkey 93jK1URnVqR9j5CLfiEuJEN3jtKkr5dtqcs1PuLpsYAJ
whirlpool token_mint_a So11111111111111111111111111111111111111112
whirlpool token_mint_b EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v
whirlpool tick_spacing 64
whirlpool tick_current_index -16803
whirlpool sqrt_price 7962878654069809622
whirlpool price 186.337708
TX signature 3SfxDGbV1VnQZ2sxGr4hrUJpyQAdK4p4zMrsFoDKki39taHYiqCj2SJySTFShtt34af6D4LFsTtX5dbCdn4jz3U2

'''