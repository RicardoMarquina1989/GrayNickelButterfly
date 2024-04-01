import asyncio

from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient

from constants import *
from orca_whirlpools_py.whirlpools import get_liquidity_distribution_by_whirlpools_pubkey

'''
Get liquidity distributions
'''
async def main():
    connection = AsyncClient(RPC_ENDPOINT_URL)
    # Pick SOL/USDC(64) whirlpool to test 
    whirlpool_pubkey = Pubkey.from_string("HJPjoWUrhoZzkNfRpHuieeFk9WcZWjwy6PBjZ81ngndJ")
    liquidity_distribution = await get_liquidity_distribution_by_whirlpools_pubkey(connection, whirlpool_pubkey)
    
    # show the result
    print('{:<20} {:<20} {:<20}'.format("tick_lower_index", "tick_upper_index", "liquidity"))

    for ld in liquidity_distribution:
        print('{:<20} {:<20} {:<20}'.format(ld.tick_lower_index, ld.tick_upper_index, ld.liquidity))

    print('{:<20} {:<20} {:<20}'.format("tick_lower_index", "tick_upper_index", "liquidity"))
    print(len(liquidity_distribution), "liquidity distributions found")
asyncio.run(main())