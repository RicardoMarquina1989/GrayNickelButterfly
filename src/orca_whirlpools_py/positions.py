import requests
import time

from solders.pubkey import Pubkey

# Global variable to hold cached data and its timestamp
cached_data = {
    'data': None,
    'timestamp': None
}

# Expiration time in seconds (15 minutes)
expiration_time = 15 * 60  

async def find_positions():
    global cached_data
    
    # If data is already cached and not expired, return it
    if cached_data['data'] and (time.time() - cached_data['timestamp'] < expiration_time):
        return cached_data['data']
    
    url = "https://api.mainnet.orca.so/v1/token/list"

    # Sending a GET request to the API
    response = requests.get(url)
    # get whirlpool
    # whirlpool = await ctx.fetcher.get_whirlpool(whirlpool_pubkey)
    # decimals_a = (await ctx.fetcher.get_token_mint(whirlpool.token_mint_a)).decimals  # SOL_DECIMAL
    # decimals_b = (await ctx.fetcher.get_token_mint(whirlpool.token_mint_b)).decimals  # USDC_DECIMAL
    # get token name

    # Checking if the request was successful (status code 200)
    if response.status_code == 200:
        # Parsing the JSON response
        data = response.json()
        tokens = []
        for token in data["tokens"]:
            tokens.append({
                "mint": Pubkey.from_string(token['mint']),
                "symbol": warn_undefined(token['symbol'], token['mint']),
                "name": warn_undefined(token['name'], token['mint']),
                "decimals": token['decimals'],
                "logoURI": token.get('logoURI', ''),
                "coingecko_id": token.get('coingeckoId', ''),
                "pool_token": token['poolToken'],
            })
        
        # Cache the data and its timestamp
        cached_data['data'] = tokens
        cached_data['timestamp'] = time.time()
        return tokens
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