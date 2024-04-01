import requests
import time
from typing import NamedTuple

from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient
from solana.rpc.types import TokenAccountOpts
from solders.keypair import Keypair
from spl.token.constants import TOKEN_PROGRAM_ID

from orca_whirlpool.accounts import AccountFinder, AccountFetcher
from orca_whirlpool.constants import ORCA_WHIRLPOOL_PROGRAM_ID
from orca_whirlpool.context import WhirlpoolContext
from orca_whirlpool.utils import PoolUtil, TokenUtil, LiquidityMath, PriceMath, PDAUtil, PositionUtil

# Global variable to hold cached data and its timestamp
cached_data = {
    'data': None,
    'timestamp': None
}

# Expiration time in seconds (15 minutes)
expiration_time = 15 * 60  

async def find_whirlpools():
    global cached_data
    
    # If data is already cached and not expired, return it
    if cached_data['data'] and (time.time() - cached_data['timestamp'] < expiration_time):
        return cached_data['data']
    
    url = "https://api.mainnet.orca.so/v1/whirlpool/list"

    # Sending a GET request to the API
    response = requests.get(url)

    # Checking if the request was successful (status code 200)
    if response.status_code == 200:
        # Parsing the JSON response
        data = response.json()
        whirlpools = []
        for wpool in data["whirlpools"]:
            symbolA = warn_undefined(wpool['tokenA']['symbol'], wpool['tokenA']['mint'])
            symbolB = warn_undefined(wpool['tokenB']['symbol'], wpool['tokenB']['mint'])
            whirlpools.append({
                "address": Pubkey.from_string(wpool['address']),
                "name": f"{symbolA}/{symbolB}({wpool['tickSpacing']})",
                "invertedName": f"{symbolB}/{symbolA}({wpool['tickSpacing']})",
                "symbolA": symbolA,
                "symbolB": symbolB,
                "mintA": Pubkey.from_string(wpool['tokenA']['mint']),
                "mintB": Pubkey.from_string(wpool['tokenB']['mint']),
                "tick_spacing": wpool['tickSpacing'],
                "price": wpool['price'],
                "usdTVL": wpool.get('tvl', 0),  # Using dictionary.get() to provide default value
                "usdVolumeDay": wpool.get('volume', {}).get('day', 0)  # Using dictionary.get() to provide default value
            })
        
        # Cache the data and its timestamp
        cached_data['data'] = whirlpools
        cached_data['timestamp'] = time.time()
        return whirlpools
    else:
        print("Failed to fetch data. Status code:", response.status_code)
        return None

def warn_undefined(s, mint):
  if len(s.strip()) > 8:
     return get_short_address_notation(s.strip(), 4)
  return (s.strip() or get_short_address_notation(mint.strip(), 4)) # use "||" to process "" as undefined

def get_short_address_notation(address, prefixSuffixLength= 5):
  if ( address is None ):
    return address
  
  return address[:prefixSuffixLength] + "..." + address[-prefixSuffixLength:]

'''
@func Get liquidity distribution of a specific whirlpools
@param  AsyncClient     connection
@param  Pubkey          whirlpool_pubkey
@return liquidity distributions
'''
async def get_liquidity_distribution_by_whirlpools_pubkey(connection: AsyncClient, whirlpool_pubkey: Pubkey):
    
    fetcher = AccountFetcher(connection)
    whirlpool = await fetcher.get_whirlpool(whirlpool_pubkey)
    finder = AccountFinder(connection)
    tick_arrays = await finder.find_tick_arrays_by_whirlpool(
        ORCA_WHIRLPOOL_PROGRAM_ID,
        whirlpool_pubkey,
    )

    liquidity_distribution = PoolUtil.get_liquidity_distribution(whirlpool, tick_arrays)
    return liquidity_distribution
   
'''
@func get position of whirlpools
'''
class PositionRelatedAccounts(NamedTuple):
    mint: Pubkey
    token_account: Pubkey
    position: Pubkey

async def get_positions_by_whrilpool_pubkey(connection: AsyncClient, wallet_pubkey: Pubkey):

    ctx = WhirlpoolContext(ORCA_WHIRLPOOL_PROGRAM_ID, connection, Keypair())

    # list all token accounts
    res = await ctx.connection.get_token_accounts_by_owner(
        wallet_pubkey,
        TokenAccountOpts(program_id=TOKEN_PROGRAM_ID, encoding="base64")
    )
    token_accounts = res.value

    candidates = []
    for token_account in token_accounts:
        pubkey = token_account.pubkey
        parsed = TokenUtil.deserialize_account(token_account.account.data)

        # maybe NFT
        if parsed.amount == 1:
            # derive position address
            position = PDAUtil.get_position(ORCA_WHIRLPOOL_PROGRAM_ID, parsed.mint).pubkey
            candidates.append(PositionRelatedAccounts(parsed.mint, pubkey, position))

    # make cache
    position_pubkeys = list(map(lambda c: c.position, candidates))
    fetched = await ctx.fetcher.list_positions(position_pubkeys, True)
    whirlpool_pubkeys = [fetched[i].whirlpool for i in range(len(fetched)) if fetched[i] is not None]
    await ctx.fetcher.list_whirlpools(whirlpool_pubkeys, True)

    positions = []
    for position, accounts in zip(fetched, candidates):
        if position is None:
            continue

        # fetch from cache
        whirlpool = await ctx.fetcher.get_whirlpool(position.whirlpool)
        # calc token amounts
        amounts = LiquidityMath.get_token_amounts_from_liquidity(
            position.liquidity,
            whirlpool.sqrt_price,
            PriceMath.tick_index_to_sqrt_price_x64(position.tick_lower_index),
            PriceMath.tick_index_to_sqrt_price_x64(position.tick_upper_index),
            False
        )
        # get status
        status = PositionUtil.get_position_status(
            whirlpool.tick_current_index,
            position.tick_lower_index,
            position.tick_upper_index
        )
        # append to prepare return value
        positions.append({
            "mint":             accounts.mint,
            "token_account":    accounts.token_account,
            "position_pubkey":  accounts.position,
            "whirlpool":        position.whirlpool,
            "token_a":          whirlpool.token_mint_a,
            "token_b":          whirlpool.token_mint_b,
            "liquidity":        position.liquidity,
            "token_amount_a":   amounts.token_a,
            "token_amount_b":   amounts.token_b,
            "status":           status
        })
    return positions
