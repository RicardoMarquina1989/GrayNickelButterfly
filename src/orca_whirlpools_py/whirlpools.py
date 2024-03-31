from orca_whirlpool.accounts import AccountFinder, AccountFetcher
from orca_whirlpool.constants import ORCA_WHIRLPOOL_PROGRAM_ID, ORCA_WHIRLPOOLS_CONFIG


async def find_whirlpools(connection):
    
    finder = AccountFinder(connection)
    orca_supported_whirlpools = await finder.find_whirlpools_by_whirlpools_config(
        ORCA_WHIRLPOOL_PROGRAM_ID,
        ORCA_WHIRLPOOLS_CONFIG,
    )
    
    return orca_supported_whirlpools