import asyncio

from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.keypair import Keypair



async def main():
    connection = AsyncClient(RPC_ENDPOINT_URL)
    
asyncio.run(main())