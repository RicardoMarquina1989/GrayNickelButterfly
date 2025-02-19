import argparse
import asyncio

from decimal import Decimal
from orca_whirlpools_py.positions import find_positions
from solders.pubkey import Pubkey
from utils import get_context

'''
@func: List all positions of the designated whirlpool.
@Command sample
    - To list all positions of the whirlpool
    python list_positions_api.py -W HJPjoWUrhoZzkNfRpHuieeFk9WcZWjwy6PBjZ81ngndJ
    - To show the position in more detail
    python list_positions_api.py -P 5ebE8hm4g2scC7w7KQGP8z22hMDdkShWVCgE3MHBFSLE
'''

async def main():
    parser = argparse.ArgumentParser(description="Get positions that are belonged to the whirlpool.")
    parser.add_argument('-W', "--whirlpool_pubkey", help="Wallet Public Key")
    args = parser.parse_args()

    if args.whirlpool_pubkey is None:
        parser.error("Whirlpool address is required.")
    # The result are equivalent with when you access to https://www.orca.so/pools?mintvl=0
    ctx = get_context()
    whirlpool_pubkey = Pubkey.from_string(args.whirlpool_pubkey)
    poolPositions = await find_positions(ctx=ctx, whirlpool_pubkey=whirlpool_pubkey)
    
    # To show the result
    
    print(f"🌀Whirlpool listPositions")
    print(f"🌀Whirlpool pubkey {whirlpool_pubkey}")
    print("Summary")
    print('{:<25} {:<6} {:<8}'.format('all positions', poolPositions['positionSummary']['numPositions']))
    print('{:<25} {:<6} {:<8}'.format('0 liquidity', poolPositions['positionSummary']['numZeroLiquidityPositions'], get_rate_string(poolPositions['positionSummary']['numZeroLiquidityPositions'], poolPositions['positionSummary']['numPositions'])))
    print('{:<25} {:<6} {:<8}'.format('full range', poolPositions['positionSummary']['numFullRangePositions'], get_rate_string(poolPositions['positionSummary']['numFullRangePositions'], poolPositions['positionSummary']['numPositions'])))
    print('{:<25} {:<6} {:<8}'.format('status: In Range', poolPositions['positionSummary']['numStatusPriceIsInRangePositions'], get_rate_string(poolPositions['positionSummary']['numFullRangePositions'], poolPositions['positionSummary']['numPositions'])))
    print('{:<25} {:<6} {:<8}'.format('status: Price is Above', poolPositions['positionSummary']['numStatusPriceIsAboveRangePositions']))
    print('{:<25} {:<6} {:<8}'.format('status: Price is Below', poolPositions['positionSummary']['numStatusPriceIsBelowRangePositions']))
    
    # for p in poolPositions:
    #     address = str(p.get("address", ""))
    #     name = p.get("name", "")
    #     price = p.get("price", 0)
    #     formatedPrice = "${:,.2f}".format(price)
    #     usdTVL = p.get("usdTVL", 0)
    #     formatedUsdTVL = "${:,.2f}".format(usdTVL)
    #     mintA = str(p.get("mintA", ""))
    #     mintB = str(p.get("mintB", ""))
    #     tick_spacing = p.get("tick_spacing", "")
    #     print('{:<43} {:<20} {:<8} {:<25} {:<45} {:<45} {:<4}'.format(address, name, formatedUsdTVL, formatedPrice, mintA, mintB, tick_spacing))
        
    # print('{:<43} {:<20} {:<8} {:<25} {:<45} {:<45} {:<4}'.format('address', 'name', 'usdTVL', 'price', 'mintA', 'mintB', 'tick_spacing'))

    # print(len(pool_positions), "whirlpools found")
    
def get_rate_string(num, denom):
    if denom == 0:
        return ""

    rate = Decimal(round(num / denom * 100 * 100)).div(100)
    return f"{rate:.2f} %"

  

asyncio.run(main())

