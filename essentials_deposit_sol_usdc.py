import asyncio
import json
import os
from dotenv import load_dotenv
from decimal import Decimal
from pathlib import Path
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.keypair import Keypair

from orca_whirlpool.context import WhirlpoolContext
from orca_whirlpool.utils import DecimalUtil, PriceMath, PDAUtil, TokenUtil, TickUtil
from orca_whirlpool.types import Percentage
from orca_whirlpool.constants import ORCA_WHIRLPOOL_PROGRAM_ID
from orca_whirlpool.instruction import WhirlpoolIx, OpenPositionParams, IncreaseLiquidityParams
from orca_whirlpool.transaction import TransactionBuilder
from orca_whirlpool.quote import QuoteBuilder, IncreaseLiquidityQuoteParams


load_dotenv()
RPC_ENDPOINT_URL = os.getenv("RPC_ENDPOINT_URL")
SAMO_USDC_WHIRLPOOL_PUBKEY = Pubkey.from_string("9vqYJjDUFecLL2xPUC4Rc7hyCtZ6iJ4mDiVZX7aFXoAe")


async def main():
    # read wallet
    # - how to create: solana-keygen new -o wallet.json
    # - need some USDC and SAMO
    with Path("wallet.json").open() as f:
        keypair = Keypair.from_bytes(bytes(json.load(f)))
    print("wallet pubkey", keypair.pubkey())
    

    # create client
    connection = AsyncClient(RPC_ENDPOINT_URL)
    ctx = WhirlpoolContext(ORCA_WHIRLPOOL_PROGRAM_ID, connection, keypair)

    # get whirlpool
    whirlpool_pubkey = SAMO_USDC_WHIRLPOOL_PUBKEY
    # whirlpool = await ctx.fetcher.get_whirlpool(whirlpool_pubkey)
    # decimals_a = (await ctx.fetcher.get_token_mint(whirlpool.token_mint_a)).decimals  # SAMO_DECIMAL
    # decimals_b = (await ctx.fetcher.get_token_mint(whirlpool.token_mint_b)).decimals  # USDC_DECIMAL
    # print("whirlpool token_mint_a", whirlpool.token_mint_a)
    # print("whirlpool token_mint_b", whirlpool.token_mint_b)
    # print("whirlpool tick_spacing", whirlpool.tick_spacing)
    # print("whirlpool tick_current_index", whirlpool.tick_current_index)
    # print("whirlpool sqrt_price", whirlpool.sqrt_price)
    # price = PriceMath.sqrt_price_x64_to_price(whirlpool.sqrt_price, decimals_a, decimals_b)
    # print("whirlpool price", DecimalUtil.to_fixed(price, decimals_b))

    # input
    # input_token = whirlpool.token_mint_b  # USDC
    # input_amount = DecimalUtil.to_u64(Decimal("0.01"), decimals_b)  # USDC
    # acceptable_slippage = Percentage.from_fraction(1, 100)
    # price_lower = price / 2
    # price_upper = price * 2
    # tick_lower_index = PriceMath.price_to_initializable_tick_index(price_lower, decimals_a, decimals_b, whirlpool.tick_spacing)
    # tick_upper_index = PriceMath.price_to_initializable_tick_index(price_upper, decimals_a, decimals_b, whirlpool.tick_spacing)

    
    # get ATA (considering WSOL)
    # token_account_a = await TokenUtil.resolve_or_create_ata(ctx.connection, ctx.wallet.public_key, whirlpool.token_mint_a, quote.token_max_a)
    # token_account_b = await TokenUtil.resolve_or_create_ata(ctx.connection, ctx.wallet.public_key, whirlpool.token_mint_b, quote.token_max_b)
    # print("token_account_a", token_account_a.pubkey)
    # print("token_account_b", token_account_b.pubkey)

    # build transaction
    tx = TransactionBuilder(ctx.connection, ctx.wallet)

    # WSOL considring
    # tx.add_instruction(token_account_a.instruction)
    # tx.add_instruction(token_account_b.instruction)
    print("ctx.wallet", ctx.wallet)
    print("ctx.wallet.pubkey", ctx.wallet.pubkey())
    
    # open position
    position_mint = Keypair()
    position_ata = TokenUtil.derive_ata(ctx.wallet.pubkey(), position_mint.pubkey())
    position_pda = PDAUtil.get_position(ctx.program_id, position_mint.pubkey())
    print("position_mint: ", position_mint)
    print("position_ata: ", position_ata)
    print("position_pda: ", position_pda)
    print("funder: ", ctx.wallet.pubkey())
    print("owner: ", ctx.wallet.pubkey())
    
    open_position_ix = WhirlpoolIx.open_position(
        ctx.program_id,
        OpenPositionParams(
            whirlpool=whirlpool_pubkey,
            # tick_lower_index=tick_lower_index,
            # tick_upper_index=tick_upper_index,
            tick_lower_index=10,
            tick_upper_index=30,
            position_pda=position_pda,
            position_mint=position_mint.pubkey(),
            position_token_account=position_ata,
            funder=ctx.wallet.pubkey(),
            owner=ctx.wallet.pubkey(),
        )
    )
    tx.add_instruction(open_position_ix)
    tx.add_signer(position_mint)

    # increase liquidity
    # tick_array_lower = PDAUtil.get_tick_array(ctx.program_id, whirlpool_pubkey, TickUtil.get_start_tick_index(tick_lower_index, whirlpool.tick_spacing)).pubkey
    # tick_array_upper = PDAUtil.get_tick_array(ctx.program_id, whirlpool_pubkey, TickUtil.get_start_tick_index(tick_upper_index, whirlpool.tick_spacing)).pubkey
    # increase_liquidity_ix = WhirlpoolIx.increase_liquidity(
    #     ctx.program_id,
    #     IncreaseLiquidityParams(
    #         whirlpool=whirlpool_pubkey,
    #         position=position_pda.pubkey,
    #         position_token_account=position_ata,
    #         position_authority=ctx.wallet.public_key,
    #         liquidity_amount=quote.liquidity,
    #         token_max_a=quote.token_max_a,
    #         token_max_b=quote.token_max_b,
    #         token_owner_account_a=token_account_a.pubkey,
    #         token_owner_account_b=token_account_b.pubkey,
    #         token_vault_a=whirlpool.token_vault_a,
    #         token_vault_b=whirlpool.token_vault_b,
    #         tick_array_lower=tick_array_lower,
    #         tick_array_upper=tick_array_upper,
    #     )
    # )
    # tx.add_instruction(increase_liquidity_ix)

    # execute
    signature = await tx.build_and_execute()
    print("TX signature", signature)

asyncio.run(main())