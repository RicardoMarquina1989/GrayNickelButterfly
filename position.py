import json
from pathlib import Path

from dotenv import load_dotenv
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair
from solders.pubkey import Pubkey

from orca_whirlpool.constants import ORCA_WHIRLPOOL_PROGRAM_ID
from orca_whirlpool.context import WhirlpoolContext
from orca_whirlpool.instruction import WhirlpoolIx, OpenPositionParams, CollectFeesParams, ClosePositionParams, CollectProtocolFeesParams, CollectRewardParams
from orca_whirlpool.transaction import TransactionBuilder
from orca_whirlpool.utils import TokenUtil, DecimalUtil, PriceMath, PDAUtil

from constants import *

gctx = None
def get_context() -> WhirlpoolContext:
    if gctx is not None:
        return gctx
    
    """Read wallet from file and return the keypair."""
    wallet_path = ("wallet.json", "wallet_main.json")[APP_ENV == "main"]
    with Path(wallet_path).open() as f:
        keypair = Keypair.from_bytes(bytes(json.load(f)))
    print("wallet pubkey", keypair.pubkey())

    connection = AsyncClient(RPC_ENDPOINT_URL)  # Create Solana RPC client
    ctx = WhirlpoolContext(ORCA_WHIRLPOOL_PROGRAM_ID, connection, keypair)  # Create Whirlpool context
    gctx = ctx
    return gctx

def rand_pubkey() -> Pubkey:
    return Keypair().pubkey()

def collect_operation():
    """Perform 'collect' operation."""
    print("Collecting fees")

    program_id = rand_pubkey()
    whirlpool = rand_pubkey()
    position_authority = rand_pubkey()
    position = rand_pubkey()
    position_token_account = rand_pubkey()
    token_owner_account_a = rand_pubkey()
    token_vault_a = rand_pubkey()
    token_owner_account_b = rand_pubkey()
    token_vault_b = rand_pubkey()

    result = WhirlpoolIx.collect_fees(
        program_id,
        CollectFeesParams(
            whirlpool=whirlpool,
            position_authority=position_authority,
            position=position,
            position_token_account=position_token_account,
            token_owner_account_a=token_owner_account_a,
            token_vault_a=token_vault_a,
            token_owner_account_b=token_owner_account_b,
            token_vault_b=token_vault_b,
        )
    )
    print("Collect Fee Result=> ", result)

    program_id = rand_pubkey()
    whirlpools_config = rand_pubkey()
    whirlpool = rand_pubkey()
    collect_protocol_fees_authority = rand_pubkey()
    token_vault_a = rand_pubkey()
    token_vault_b = rand_pubkey()
    token_destination_a = rand_pubkey()
    token_destination_b = rand_pubkey()

    result = WhirlpoolIx.collect_protocol_fees(
        program_id,
        CollectProtocolFeesParams(
            whirlpools_config=whirlpools_config,
            whirlpool=whirlpool,
            collect_protocol_fees_authority=collect_protocol_fees_authority,
            token_vault_a=token_vault_a,
            token_vault_b=token_vault_b,
            token_destination_a=token_destination_a,
            token_destination_b=token_destination_b,
        )
    )


async def open_position(upper: int, lower: int):
    """Open a position based on upper and lower parameters."""
    ctx = get_context()  # Create or get already created Whirlpool context

    # Fetch whirlpool details
    whirlpool_pubkey = SOL_USDC_WHIRLPOOL_PUBKEY
    whirlpool = await ctx.fetcher.get_whirlpool(whirlpool_pubkey)
    decimals_a = (await ctx.fetcher.get_token_mint(whirlpool.token_mint_a)).decimals
    decimals_b = (await ctx.fetcher.get_token_mint(whirlpool.token_mint_b)).decimals
    price = PriceMath.sqrt_price_x64_to_price(whirlpool.sqrt_price, decimals_a, decimals_b)
    print("whirlpool token_mint_a", whirlpool.token_mint_a)
    print("whirlpool token_mint_b", whirlpool.token_mint_b)
    print("whirlpool tick_spacing", whirlpool.tick_spacing)
    print("whirlpool tick_current_index", whirlpool.tick_current_index)
    print("whirlpool sqrt_price", whirlpool.sqrt_price)
    price = PriceMath.sqrt_price_x64_to_price(whirlpool.sqrt_price, decimals_a, decimals_b)
    print("whirlpool price", DecimalUtil.to_fixed(price, decimals_b))
    # Calculate tick indices
    tick_lower_index = PriceMath.price_to_initializable_tick_index(lower, decimals_a, decimals_b, whirlpool.tick_spacing)
    tick_upper_index = PriceMath.price_to_initializable_tick_index(upper, decimals_a, decimals_b, whirlpool.tick_spacing)
    
    # Build transaction
    tx = TransactionBuilder(ctx.connection, ctx.wallet)

    # Open position
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

    # Execute transaction
    signature = await tx.build_and_execute()
    print("TX signature", signature)


def close_position():
    """Close a position."""
    print("Performing 'close' operation")
    ctx = get_context()  # Create or get already created Whirlpool context
    program_id = rand_pubkey()
    position_authority = rand_pubkey()
    receiver = rand_pubkey()
    position = rand_pubkey()
    position_mint = rand_pubkey()
    position_token_account = rand_pubkey()

    result = WhirlpoolIx.close_position(
        program_id,
        ClosePositionParams(
            position_authority=position_authority,
            receiver=receiver,
            position=position,
            position_mint=position_mint,
            position_token_account=position_token_account,
        )
    )
