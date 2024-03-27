import argparse
import asyncio
import os
import json
from dotenv import load_dotenv
from pathlib import Path
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.keypair import Keypair

from orca_whirlpool.constants import ORCA_WHIRLPOOL_PROGRAM_ID
from orca_whirlpool.context import WhirlpoolContext
from orca_whirlpool.utils import TokenUtil, DecimalUtil, PriceMath, PDAUtil
from orca_whirlpool.instruction import WhirlpoolIx, OpenPositionParams
from orca_whirlpool.transaction import TransactionBuilder

load_dotenv()
RPC_ENDPOINT_URL = os.getenv("RPC_ENDPOINT_URL")
APP_ENV = os.getenv("APP_ENV")
SOL_USDC_WHIRLPOOL_PUBKEY = Pubkey.from_string("HJPjoWUrhoZzkNfRpHuieeFk9WcZWjwy6PBjZ81ngndJ")

def main():
    # prepare argument parser
    parser = argparse.ArgumentParser(description="Script for performing various operations.")
    parser.add_argument("operation", choices=["open", "close", "collect"], help="Operation to perform")
    parser.add_argument("--upper", type=int, help="Upper parameter for 'open' operation")
    parser.add_argument("--lower", type=int, help="Lower parameter for 'open' operation")
    
    args = parser.parse_args()

    if args.operation == "open":
        if args.upper is None or args.lower is None:
            parser.error("For 'open' operation, both upper and lower parameters are required.")
        else:
            asyncio.run(open_position(upper=args.upper, lower=args.lower))
    elif args.operation == "close":
        close_position()
    elif args.operation == "collect":
        collect_operation()
    else:
        parser.error("Invalid operation")

async def open_position(upper:int, lower:int):
    # read wallet
    keypair = read_wallet()

    # create client
    connection = AsyncClient(RPC_ENDPOINT_URL)
    ctx = WhirlpoolContext(ORCA_WHIRLPOOL_PROGRAM_ID, connection, keypair)

    # get whirlpool
    whirlpool_pubkey = SOL_USDC_WHIRLPOOL_PUBKEY
    whirlpool = await ctx.fetcher.get_whirlpool(whirlpool_pubkey)
    decimals_a = (await ctx.fetcher.get_token_mint(whirlpool.token_mint_a)).decimals  # SOL_DECIMAL
    decimals_b = (await ctx.fetcher.get_token_mint(whirlpool.token_mint_b)).decimals  # USDC_DECIMAL
    print("whirlpool token_mint_a", whirlpool.token_mint_a)
    print("whirlpool token_mint_b", whirlpool.token_mint_b)
    print("whirlpool tick_spacing", whirlpool.tick_spacing)
    print("whirlpool tick_current_index", whirlpool.tick_current_index)
    print("whirlpool sqrt_price", whirlpool.sqrt_price)
    price = PriceMath.sqrt_price_x64_to_price(whirlpool.sqrt_price, decimals_a, decimals_b)
    print("whirlpool price", DecimalUtil.to_fixed(price, decimals_b))

    
    tick_lower_index = PriceMath.price_to_initializable_tick_index(lower, decimals_a, decimals_b, whirlpool.tick_spacing)
    print("tick_lower_index", tick_lower_index)
    tick_upper_index = PriceMath.price_to_initializable_tick_index(upper, decimals_a, decimals_b, whirlpool.tick_spacing)
    print("tick_upper_index", tick_upper_index)
    
    # build transaction
    tx = TransactionBuilder(ctx.connection, ctx.wallet)

    # open position
    position_mint = Keypair()
    position_ata = TokenUtil.derive_ata(ctx.wallet.pubkey(), position_mint.pubkey())
    position_pda = PDAUtil.get_position(ctx.program_id, position_mint.pubkey())
    open_position_ix = WhirlpoolIx.open_position(
        ctx.program_id,
        OpenPositionParams(
            whirlpool=whirlpool_pubkey,
            tick_lower_index=tick_lower_index,
            tick_upper_index=tick_upper_index,
            position_pda=position_pda,
            position_mint=position_mint.pubkey(),
            position_token_account=position_ata,
            funder=ctx.wallet.pubkey(),
            owner=ctx.wallet.pubkey(),
        )
    )
    tx.add_instruction(open_position_ix)
    tx.add_signer(position_mint)

    # execute
    signature = await tx.build_and_execute()
    print("TX signature", signature)

def close_position():
    print("Performing 'close' operation")

def collect_operation():
    print("Performing 'collect' operation")

# read wallet function
def read_wallet() -> Keypair:
    # read wallet
    # - how to create: solana-keygen new -o wallet.json
    # - need some USDC and SOL
    wallet_path = ("wallet.json", "wallet_main.json") [APP_ENV == "main"] 
    with Path(wallet_path).open() as f:
        keypair = Keypair.from_bytes(bytes(json.load(f)))
    print("wallet pubkey", keypair.pubkey())
    return keypair

if __name__ == "__main__":
    main()
