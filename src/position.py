import json
from pathlib import Path
from typing import NamedTuple

from solana.rpc.async_api import AsyncClient
from solana.rpc.types import TokenAccountOpts
from solders.keypair import Keypair
from solders.pubkey import Pubkey

from orca_whirlpool.constants import ORCA_WHIRLPOOL_PROGRAM_ID
from orca_whirlpool.context import WhirlpoolContext
from orca_whirlpool.instruction import WhirlpoolIx, OpenPositionParams, CollectFeesParams, ClosePositionParams, CollectProtocolFeesParams, CollectRewardParams, DecreaseLiquidityParams, UpdateFeesAndRewardsParams
from orca_whirlpool.transaction import TransactionBuilder
from orca_whirlpool.utils import TokenUtil, DecimalUtil, PriceMath, PositionUtil, PDAUtil, TickUtil, LiquidityMath

from constants import *

gctx = None
WHIRLPOOL_PUBKEY = SOL_USDC_WHIRLPOOL_PUBKEY
TOKEN_PROGRAM_ID: Pubkey = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
"""Public key that identifies the SPL token program."""

class PositionRelatedAccounts(NamedTuple):
    mint: Pubkey
    token_account: Pubkey
    position: Pubkey

def get_context() -> WhirlpoolContext:
    global gctx
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

async def decrease_liquidity(tx: TransactionBuilder, execute: True):
    ctx = get_context()
    # decrease liquidity
    position_mint = Keypair()
    position_ata = TokenUtil.derive_ata(ctx.wallet.pubkey(), position_mint.pubkey())
    position_pda = PDAUtil.get_position(ctx.program_id, position_mint.pubkey())
    
    whirlpool = await ctx.fetcher.get_whirlpool(WHIRLPOOL_PUBKEY)
    
    # get ATA (considering WSOL)
    token_account_a = await TokenUtil.resolve_or_create_ata(ctx.connection, ctx.wallet.pubkey(), whirlpool.token_mint_a)
    token_account_b = await TokenUtil.resolve_or_create_ata(ctx.connection, ctx.wallet.pubkey(), whirlpool.token_mint_b)
    tx.add_instruction(token_account_a.instruction)
    tx.add_instruction(token_account_b.instruction)

    decimals_a = (await ctx.fetcher.get_token_mint(whirlpool.token_mint_a)).decimals  # SOL_DECIMAL
    decimals_b = (await ctx.fetcher.get_token_mint(whirlpool.token_mint_b)).decimals  # USDC_DECIMAL
    print("whirlpool token_mint_a", whirlpool.token_mint_a)
    print("whirlpool token_mint_b", whirlpool.token_mint_b)
    print("whirlpool tick_spacing", whirlpool.tick_spacing)
    print("whirlpool tick_current_index", whirlpool.tick_current_index)
    print("whirlpool sqrt_price", whirlpool.sqrt_price)
    price = PriceMath.sqrt_price_x64_to_price(whirlpool.sqrt_price, decimals_a, decimals_b)
    print("whirlpool price", DecimalUtil.to_fixed(price, decimals_b))

    # input
    price_lower = price / 2
    price_upper = price * 2
    tick_lower_index = PriceMath.price_to_initializable_tick_index(price_lower, decimals_a, decimals_b, whirlpool.tick_spacing)
    tick_upper_index = PriceMath.price_to_initializable_tick_index(price_upper, decimals_a, decimals_b, whirlpool.tick_spacing)
    tick_array_lower_start_tick_index = TickUtil.get_start_tick_index(tick_lower_index, whirlpool.tick_spacing)
    tick_array_upper_start_tick_index = TickUtil.get_start_tick_index(tick_upper_index, whirlpool.tick_spacing)
    tick_array_lower = PDAUtil.get_tick_array(ctx.program_id, WHIRLPOOL_PUBKEY, tick_array_lower_start_tick_index).pubkey
    tick_array_upper = PDAUtil.get_tick_array(ctx.program_id, WHIRLPOOL_PUBKEY, tick_array_upper_start_tick_index).pubkey

    decrease_liquidity_ix = WhirlpoolIx.decrease_liquidity(
        ctx.program_id,
        DecreaseLiquidityParams(
            liquidity_amount=0,
            token_min_a=0,
            token_min_b=0,
            whirlpool=WHIRLPOOL_PUBKEY,
            position_authority=ctx.wallet.pubkey(),
            position=position_pda.pubkey,
            position_token_account=position_ata,
            token_owner_account_a=token_account_a.pubkey,
            token_owner_account_b=token_account_b.pubkey,
            token_vault_a=whirlpool.token_vault_a,
            token_vault_b=whirlpool.token_vault_b,
            tick_array_lower=tick_array_lower,
            tick_array_upper=tick_array_upper,
        )
    )
    tx.add_instruction(decrease_liquidity_ix)
    if execute == True:
        tx.add_signer(ctx.wallet)

        # Execute transaction
        signature = await tx.build_and_execute()
        print("TX signature", signature)

async def update_fees_and_rewards(tx: TransactionBuilder, execute: True):
    ctx = get_context()
    whirlpool = await ctx.fetcher.get_whirlpool(WHIRLPOOL_PUBKEY)
    position_mint = Keypair()
    position_pda = PDAUtil.get_position(ctx.program_id, position_mint.pubkey())

    decimals_a = (await ctx.fetcher.get_token_mint(whirlpool.token_mint_a)).decimals  # SOL_DECIMAL
    decimals_b = (await ctx.fetcher.get_token_mint(whirlpool.token_mint_b)).decimals  # USDC_DECIMAL
    print("whirlpool token_mint_a", whirlpool.token_mint_a)
    print("whirlpool token_mint_b", whirlpool.token_mint_b)
    print("whirlpool tick_spacing", whirlpool.tick_spacing)
    print("whirlpool tick_current_index", whirlpool.tick_current_index)
    print("whirlpool sqrt_price", whirlpool.sqrt_price)
    price = PriceMath.sqrt_price_x64_to_price(whirlpool.sqrt_price, decimals_a, decimals_b)
    price_lower = price / 2
    price_upper = price * 2
    tick_lower_index = PriceMath.price_to_initializable_tick_index(price_lower, decimals_a, decimals_b, whirlpool.tick_spacing)
    tick_upper_index = PriceMath.price_to_initializable_tick_index(price_upper, decimals_a, decimals_b, whirlpool.tick_spacing)
    tick_array_lower_start_tick_index = TickUtil.get_start_tick_index(tick_lower_index, whirlpool.tick_spacing)
    tick_array_upper_start_tick_index = TickUtil.get_start_tick_index(tick_upper_index, whirlpool.tick_spacing)
    tick_array_lower = PDAUtil.get_tick_array(ctx.program_id, WHIRLPOOL_PUBKEY, tick_array_lower_start_tick_index).pubkey
    tick_array_upper = PDAUtil.get_tick_array(ctx.program_id, WHIRLPOOL_PUBKEY, tick_array_upper_start_tick_index).pubkey

    update_fees_and_rewards_ix = WhirlpoolIx.update_fees_and_rewards(
        ctx.program_id,
        UpdateFeesAndRewardsParams(
            whirlpool=WHIRLPOOL_PUBKEY,
            position=position_pda.pubkey,
            tick_array_lower=tick_array_lower,
            tick_array_upper=tick_array_upper,
        )
    )

    tx.add_instruction(update_fees_and_rewards_ix)
    if execute == True:
        # Build transaction
        # tx = TransactionBuilder(ctx.connection, ctx.wallet)
        tx.add_signer(ctx.wallet)

        # Execute transaction
        signature = await tx.build_and_execute()
        print("TX signature", signature)

async def collect_fees(tx: TransactionBuilder, execute: True):
    ctx = get_context()
    whirlpool = await ctx.fetcher.get_whirlpool(WHIRLPOOL_PUBKEY)
    whirlpools_config = await ctx.fetcher.get_whirlpools_config(WHIRLPOOL_PUBKEY)
    
    position_mint = Keypair()
    position_ata = TokenUtil.derive_ata(ctx.wallet.pubkey(), position_mint.pubkey())
    position_pda = PDAUtil.get_position(ctx.program_id, position_mint.pubkey())

    # get ATA (considering WSOL)
    token_account_a = await TokenUtil.resolve_or_create_ata(ctx.connection, ctx.wallet.pubkey(), whirlpool.token_mint_a)
    token_account_b = await TokenUtil.resolve_or_create_ata(ctx.connection, ctx.wallet.pubkey(), whirlpool.token_mint_b)

    tx.add_instruction(token_account_a.instruction)
    tx.add_instruction(token_account_b.instruction)

    collect_fees_ix = WhirlpoolIx.collect_fees(
        ctx.program_id,
        CollectFeesParams(
            whirlpool=WHIRLPOOL_PUBKEY,
            position_authority=ctx.wallet.pubkey(),
            position=position_pda.pubkey,
            position_token_account=position_ata,
            token_owner_account_a=token_account_a.pubkey,
            token_vault_a=whirlpool.token_vault_a,
            token_owner_account_b=token_account_b.pubkey,
            token_vault_b=whirlpool.token_vault_b,
        )
    )

    # collect_protocol_fees_ix = WhirlpoolIx.collect_protocol_fees(
    #     ctx.program_id,
    #     CollectProtocolFeesParams(
    #         whirlpool=WHIRLPOOL_PUBKEY,
    #         whirlpools_config=whirlpools_config,
    #         collect_protocol_fees_authority=ctx.wallet.pubkey(),
    #         token_vault_a=whirlpool.token_vault_a,
    #         token_vault_b=whirlpool.token_vault_b,
    #         token_destination_a=whirlpool.token_mint_a,
    #         token_destination_b=whirlpool.token_mint_b,
    #     )
    # )
    # add instructions
    tx.add_instruction(token_account_a.instruction)
    tx.add_instruction(token_account_b.instruction)
    tx.add_instruction(collect_fees_ix)
    # tx.add_instruction(collect_protocol_fees_ix)

    if execute == True:
        # Build transaction    
        tx.add_signer(ctx.wallet)
        # Execute transaction
        signature = await tx.build_and_execute()
        print("TX signature", signature)

async def collect_reward(tx: TransactionBuilder, execute: True):
    reward_index = 2
    ctx = get_context()
    whirlpool = await ctx.fetcher.get_whirlpool(WHIRLPOOL_PUBKEY)
    position_mint = Keypair()
    position_ata = TokenUtil.derive_ata(ctx.wallet.pubkey(), position_mint.pubkey())
    position_pda = PDAUtil.get_position(ctx.program_id, position_mint.pubkey())

    collect_reward_ix = WhirlpoolIx.collect_reward(
        ctx.program_id,
        CollectRewardParams(
            reward_index=reward_index,
            whirlpool=WHIRLPOOL_PUBKEY,
            position_authority=ctx.wallet.pubkey(),
            position=position_pda.pubkey,
            position_token_account=position_ata,
            reward_owner_account=ctx.wallet.pubkey(),
            reward_vault=ctx.wallet.pubkey(),
        )
    )

    tx.add_instruction(collect_reward_ix)

    if execute == True:
        # tx = TransactionBuilder(ctx.connection, ctx.wallet)
        tx.add_signer(ctx.wallet)

        # Execute transaction
        signature = await tx.build_and_execute()
        print("TX signature", signature)

async def open_position(upper: int, lower: int):
    """Open a position based on upper and lower parameters."""
    ctx = get_context()  # Create or get already created Whirlpool context

    # Fetch whirlpool details
    whirlpool = await ctx.fetcher.get_whirlpool(WHIRLPOOL_PUBKEY)
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
            whirlpool=WHIRLPOOL_PUBKEY,
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

async def close_position(tx: TransactionBuilder, execute: True):
    """Close a position."""
    print("Performing 'close' operation")
    ctx = get_context()  # Create or get already created Whirlpool context

    position_mint = Keypair()
    position_ata = TokenUtil.derive_ata(ctx.wallet.pubkey(), position_mint.pubkey())
    position_pda = PDAUtil.get_position(ctx.program_id, position_mint.pubkey())
    position = await ctx.fetcher.get_position(position_pda.pubkey)
    ctx.fetcher.get_latest_block_timestamp
    close_position_ix = WhirlpoolIx.close_position(
        ctx.program_id,
        ClosePositionParams(
            position_authority=ctx.wallet.pubkey(),
            receiver=ctx.wallet.pubkey(),
            position=Pubkey.from_string("FZeQDSjjs6oEFPNA4QSqWqdvaEKEFdQ7bkbBZo6CvyYr"),
            position_mint=Pubkey.from_string("FSgZwPBrxMuUApZxRnpwspxEQLTD3XsEKpqV7QVZ78St"),
            # position_mint=position.position_mint,
            position_token_account=Pubkey.from_string("HXaE8N9HCQZdAqie8xq5rVsCTm9atDSB7auASqmAxmMV"),
            # position_token_account=position_ata,
        )
    )
    tx.add_instruction(close_position_ix)
    if execute == True:
        # Build transaction
        # tx = TransactionBuilder(ctx.connection, ctx.wallet)
        tx.add_signer(ctx.wallet)

        # Execute transaction
        signature = await tx.build_and_execute()
        print("TX signature", signature)

async def list_position():
    ctx = get_context()

    wallet_path = ("wallet.json", "wallet_main.json")[APP_ENV == "main"]
    with Path(wallet_path).open() as f:
        keypair = Keypair.from_bytes(bytes(json.load(f)))
    # list all token accounts
    res = await ctx.connection.get_token_accounts_by_owner(
        keypair,
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

        print("POSITION")
        print("  mint:", accounts.mint)
        print("  token_account:", accounts.token_account)
        print("  position pubkey:", accounts.position)
        print("  whirlpool:", position.whirlpool)
        print("    token_a:", whirlpool.token_mint_a)
        print("    token_b:", whirlpool.token_mint_b)
        print("  liquidity:", position.liquidity)
        print("  token_a(u64):", amounts.token_a)
        print("  token_b(u64):", amounts.token_b)
        print("  status:", status)