from solana.rpc.async_api import AsyncClient

from orca_whirlpool.accounts import AccountFinder, AccountFetcher
from orca_whirlpool.constants import ORCA_WHIRLPOOL_PROGRAM_ID, ORCA_WHIRLPOOLS_CONFIG

'''
@func Gathering all pools or a pool information
@param  connection required
@param whirlpool_program_id
    optional: true,
    default: ORCA_WHIRLPOOL_PROGRAM_ID
@param whirlpool_config
    optional: true,
    default: ORCA_WHIRLPOOLS_CONFIG
@return 
'''
async def find_whirlpools(connection: AsyncClient, whirlpool_program_id=ORCA_WHIRLPOOL_PROGRAM_ID, whirlpool_config=ORCA_WHIRLPOOLS_CONFIG):
    
    finder = AccountFinder(connection)
    orca_supported_whirlpools = await finder.find_whirlpools_by_whirlpools_config(
        whirlpool_program_id,
        # ORCA_WHIRLPOOL_PROGRAM_ID,
        whirlpool_config,
    )
    
    return orca_supported_whirlpools