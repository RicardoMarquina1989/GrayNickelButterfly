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
  return s.strip() or get_short_address_notation(mint, 4) # use "||" to process "" as undefined

def get_short_address_notation(address, prefixSuffixLength= 5):
  if ( address is None ):
    return address
  
  return address[:prefixSuffixLength] + "..." + address[:-prefixSuffixLength]
