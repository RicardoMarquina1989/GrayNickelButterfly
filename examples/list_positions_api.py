import argparse
import asyncio

from orca_whirlpools_py.positions import find_positions
from solders.pubkey import Pubkey
from utils import get_context

'''
@func: Check fees of the targeted ones.
@Command sample
    - To check fees of a specific position
    python check_fees.py position -P 5ebE8hm4g2scC7w7KQGP8z22hMDdkShWVCgE3MHBFSLE
    - To check fees of a specific whirlpool
    python list_positions_api.py -W HJPjoWUrhoZzkNfRpHuieeFk9WcZWjwy6PBjZ81ngndJ
    - To check fees of all my own positions of wallet
    python check_fees.py wallet
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
    orca_positions = await find_positions(ctx=ctx, whirlpool_pubkey=whirlpool_pubkey)
    print(orca_positions)
    return
    # To show the result
    print('{:<43} {:<20} {:<8} {:<25} {:<45} {:<45} {:<4}'.format('address', 'name', 'usdTVL', 'price', 'mintA', 'mintB', 'tick_spacing'))
    for p in orca_positions:
        address = str(p.get("address", ""))
        name = p.get("name", "")
        price = p.get("price", 0)
        formatedPrice = "${:,.2f}".format(price)
        usdTVL = p.get("usdTVL", 0)
        formatedUsdTVL = "${:,.2f}".format(usdTVL)
        mintA = str(p.get("mintA", ""))
        mintB = str(p.get("mintB", ""))
        tick_spacing = p.get("tick_spacing", "")
        print('{:<43} {:<20} {:<8} {:<25} {:<45} {:<45} {:<4}'.format(address, name, formatedUsdTVL, formatedPrice, mintA, mintB, tick_spacing))
        
    print('{:<43} {:<20} {:<8} {:<25} {:<45} {:<45} {:<4}'.format('address', 'name', 'usdTVL', 'price', 'mintA', 'mintB', 'tick_spacing'))

    print(len(orca_positions), "whirlpools found")
    
asyncio.run(main())