import argparse
import asyncio
from typing import NamedTuple

from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey

from constants import *
from orca_whirlpools_py.whirlpools import get_positions_by_wallet_pubkey

class PositionRelatedAccounts(NamedTuple):
    mint: Pubkey
    token_account: Pubkey
    position: Pubkey

'''
This script is useful for getting only positions that are belogned to your wallet while ignoring the whirlpools.
'''
async def main():
    parser = argparse.ArgumentParser(description="Get positions that are belonged to your wallet.")
    parser.add_argument('-W', "--wallet_pubkey", help="Wallet Public Key")
    args = parser.parse_args()

    if args.wallet_pubkey is None:
        parser.error("Invalid wallet public key")
    
    connection = AsyncClient(RPC_ENDPOINT_URL)
    # wallet_pubkey = Pubkey.from_string("93jK1URnVqR9j5CLfiEuJEN3jtKkr5dtqcs1PuLpsYAJ")
    wallet_pubkey = Pubkey.from_string(args.wallet_pubkey)
    print(f"wallet pubkey {wallet_pubkey}")
    positions = await get_positions_by_wallet_pubkey(connection=connection, wallet_pubkey=wallet_pubkey)
    for position in positions:
        if position is None:
            continue

        print('{:*^80}'.format("POSITION"))        
        print('{:>16} {}'.format("mint:", position['mint']))
        print('{:>16} {}'.format("token_account:", position['token_account']))
        print('{:>16} {}'.format("position_pubkey:", position['position_pubkey']))
        print('{:>16} {}'.format("whirlpool:", position['whirlpool']))
        print('{:>16} {}'.format("token_a:", position['token_a']))
        print('{:>16} {}'.format("token_b:", position['token_b']))
        print('{:>16} {}'.format("liquidity:", position['liquidity']))
        print('{:>16} {}'.format("token_amount_a:", position['token_amount_a']))
        print('{:>16} {}'.format("token_amount_b:", position['token_amount_b']))
        print('{:>16} {}'.format("status:", position['status']))

asyncio.run(main())

''' Sample Output
wallet pubkey 93jK1URnVqR9j5CLfiEuJEN3jtKkr5dtqcs1PuLpsYAJ
**********************************************POSITION**********************************************
POSITION
           mint: 5ebE8hm4g2scC7w7KQGP8z22hMDdkShWVCgE3MHBFSLE
  token_account: BGCoRpKz7sSwFDE3B4e2z5j4kp8aaeEmpSua17SfX4ng
position_pubkey: FAQ1vEowUDxCkErvvYKytay7tUKGU56z2Ro3YXvpftm9
      whirlpool: HJPjoWUrhoZzkNfRpHuieeFk9WcZWjwy6PBjZ81ngndJ
        token_a: So11111111111111111111111111111111111111112
        token_b: EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v
        token_a: So11111111111111111111111111111111111111112
      liquidity: 2350530
 token_amount_a: 1062394
 token_amount_b: 287108
         status: In Range

'''