import argparse
import asyncio
import sys

from solders.pubkey import Pubkey

from orca_whirlpools_py.position_manager import harvest_position_fees, harvest_whirlpool_fees, harvest_wallet_fees
from utils import get_context

'''
@func: Collect fees from a position or a whirlpool.
@Command sample
    - To harvest fees from a specific position
    python harvest_fees.py -P 5ebE8hm4g2scC7w7KQGP8z22hMDdkShWVCgE3MHBFSLE
    - To harvest fees from a specific whirlpool
    python harvest_fees.py -W HJPjoWUrhoZzkNfRpHuieeFk9WcZWjwy6PBjZ81ngndJ
    - To harvest fees from all my own positions of wallet
    python harvest_fees.py
'''
async def main():
    parser = argparse.ArgumentParser(description="Open a position in the specific whirlpool.")
    parser.add_argument("target", choices=["position", "whirlpool", "wallet"], help="Determine to harvest from position or whirlpool or your own wallet")
    parser.add_argument("-P", "--position_pubkey", help="Position public key")
    parser.add_argument("-W", "--whirlpool_pubkey", help="Whirlpool public key")
    parser.add_argument('-T', "--to_wallet", type=float, help="Collected fees and rewards are transferred to the designated wallet")
    args = parser.parse_args()

    ctx = get_context()
    
    if args.operation == "position":
        if args.position_pubkey is None:
            parser.error("To harvest fees from a position, position_pubkey parameter is required.")
        else:
            position_pubkey = Pubkey.from_string(args.position_pubkey)
            await harvest_position_fees(ctx=ctx, position_pubkey=position_pubkey)
    elif args.operation == "whirlpool":
        if args.whirlpool_pubkey is None:
            parser.error("To harvest fees from a whirlpool, whirlpool_pubkey parameter is required.")
        else:
            whirlpool_pubkey = Pubkey.from_string(args.whirlpool_pubkey)
            await harvest_whirlpool_fees(ctx=ctx, whirlpool_pubkey=whirlpool_pubkey)
    elif args.operation == "wallet":
        harvest_wallet_fees(ctx=ctx)
    else:
        parser.error("Invalid target to harvest.")
        
asyncio.run(main())