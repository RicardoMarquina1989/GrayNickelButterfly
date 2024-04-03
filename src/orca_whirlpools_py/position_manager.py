from decimal import Decimal

from solders.keypair import Keypair
from solders.pubkey import Pubkey

from orca_whirlpool.types import Percentage
from orca_whirlpool.context import WhirlpoolContext
from orca_whirlpool.instruction import WhirlpoolIx, OpenPositionParams, CollectFeesParams, ClosePositionParams, CollectProtocolFeesParams, CollectRewardParams, DecreaseLiquidityParams, UpdateFeesAndRewardsParams, IncreaseLiquidityParams
from orca_whirlpool.transaction import TransactionBuilder
from orca_whirlpool.utils import TokenUtil, DecimalUtil, PriceMath, PositionUtil, PDAUtil, TickUtil, LiquidityMath
from orca_whirlpool.quote import QuoteBuilder, IncreaseLiquidityQuoteParams

def rand_pubkey() -> Pubkey:
    return Keypair().pubkey()


"""
@func:      Open a position     based on upper and lower parameters.
@param:     WhirlpoolContext    ctx
@param:     int                 priority_fee unit-lamport
@return:    
"""
async def open_position(ctx: WhirlpoolContext, whirlpool_pubkey: Pubkey, 
                        upper: float, lower: float, deposit_amount: float,
                        slippage:int=30, priority_fee: int = 0):
    
    # get whirlpool
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

    # input
    input_token = whirlpool.token_mint_b  # USDC
    input_amount = DecimalUtil.to_u64(Decimal(deposit_amount), decimals_b)  # USDC
    acceptable_slippage = Percentage.from_fraction(int(slippage), 100)
    # price_lower = price / 2
    # price_upper = price * 2
    tick_lower_index = PriceMath.price_to_initializable_tick_index(Decimal(lower), decimals_a, decimals_b, whirlpool.tick_spacing)
    tick_upper_index = PriceMath.price_to_initializable_tick_index(Decimal(upper), decimals_a, decimals_b, whirlpool.tick_spacing)

    # get quote
    quote = QuoteBuilder.increase_liquidity_by_input_token(IncreaseLiquidityQuoteParams(
        input_token_mint=input_token,
        input_token_amount=input_amount,
        token_mint_a=whirlpool.token_mint_a,
        token_mint_b=whirlpool.token_mint_b,
        sqrt_price=whirlpool.sqrt_price,
        tick_current_index=whirlpool.tick_current_index,
        tick_lower_index=tick_lower_index,
        tick_upper_index=tick_upper_index,
        slippage_tolerance=acceptable_slippage,
    ))
    print("liquidity", quote.liquidity)
    print("est_token_a", quote.token_est_a)
    print("est_token_b", quote.token_est_b)
    print("max_token_a", quote.token_max_a)
    print("max_token_a", quote.token_max_b)

    # get ATA (considering WSOL)
    token_account_a = await TokenUtil.resolve_or_create_ata(ctx.connection, ctx.wallet.pubkey(), whirlpool.token_mint_a, quote.token_max_a)
    token_account_b = await TokenUtil.resolve_or_create_ata(ctx.connection, ctx.wallet.pubkey(), whirlpool.token_mint_b, quote.token_max_b)
    print("token_account_a", token_account_a.pubkey)
    print("token_account_b", token_account_b.pubkey)

    # build transaction
    tx = TransactionBuilder(ctx.connection, ctx.wallet)

    # WSOL considring
    tx.add_instruction(token_account_a.instruction)
    tx.add_instruction(token_account_b.instruction)

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

    # increase liquidity
    tick_array_lower_start_tick_index = TickUtil.get_start_tick_index(tick_lower_index, whirlpool.tick_spacing)
    tick_array_upper_start_tick_index = TickUtil.get_start_tick_index(tick_upper_index, whirlpool.tick_spacing)
    tick_array_lower = PDAUtil.get_tick_array(ctx.program_id, whirlpool_pubkey, tick_array_lower_start_tick_index).pubkey
    tick_array_upper = PDAUtil.get_tick_array(ctx.program_id, whirlpool_pubkey, tick_array_upper_start_tick_index).pubkey
    increase_liquidity_ix = WhirlpoolIx.increase_liquidity(
        ctx.program_id,
        IncreaseLiquidityParams(
            whirlpool=whirlpool_pubkey,
            position=position_pda.pubkey,
            position_token_account=position_ata,
            position_authority=ctx.wallet.pubkey(),
            liquidity_amount=quote.liquidity,
            token_max_a=quote.token_max_a,
            token_max_b=quote.token_max_b,
            token_owner_account_a=token_account_a.pubkey,
            token_owner_account_b=token_account_b.pubkey,
            token_vault_a=whirlpool.token_vault_a,
            token_vault_b=whirlpool.token_vault_b,
            tick_array_lower=tick_array_lower,
            tick_array_upper=tick_array_upper,
        )
    )
    tx.add_instruction(increase_liquidity_ix)
    if priority_fee is not None:
        tx.set_compute_unit_limit(200000)
        # add priority fees (+ 1000 lamports)
        # tx.set_compute_unit_price(int(1000 * 10**6 / 200000))
        tx.set_compute_unit_price(int(priority_fee * 10**6 / 200000))
    # execute
    signature = await tx.build_and_execute()
    print("TX signature", signature)

"""
@func: Open a position based on upper and lower parameters.
    But it doesn't increase liquidity
@param ctx
@param whirlpool_pubkey
"""
async def open_position_only(ctx:WhirlpoolContext, whirlpool_pubkey: Pubkey, upper: float, lower: float):
    # Fetch whirlpool details
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
    tick_lower_index = PriceMath.price_to_initializable_tick_index(Decimal(lower), decimals_a, decimals_b, whirlpool.tick_spacing)
    tick_upper_index = PriceMath.price_to_initializable_tick_index(Decimal(upper), decimals_a, decimals_b, whirlpool.tick_spacing)
    
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

"""
@func:      Add liquidity to the specified position(select position address)
@param:     WhirlpoolContext    ctx
@param:     Pubkey              position_pubkey
@param:     int                 priority_fee unit-lamport
@return:    
"""
async def add_liquidity(ctx: WhirlpoolContext, position_pubkey: Pubkey, deposit_amount: float, slippage:int=30, priority_fee: int = 0):
    output = {}
    position_pda = PDAUtil.get_position(ctx.program_id, position_pubkey).pubkey
    position = await ctx.fetcher.get_position(position_pda, True)
    # print(position)
    whirlpool_pubkey = position.whirlpool
    # get whirlpool
    print('{:<80}'.format("Getting whirlpool info..."))        
    whirlpool = await ctx.fetcher.get_whirlpool(whirlpool_pubkey)
    decimals_a = (await ctx.fetcher.get_token_mint(whirlpool.token_mint_a)).decimals  # SOL_DECIMAL
    decimals_b = (await ctx.fetcher.get_token_mint(whirlpool.token_mint_b)).decimals  # USDC_DECIMAL
    price = PriceMath.sqrt_price_x64_to_price(whirlpool.sqrt_price, decimals_a, decimals_b)
    print('{:*^80}'.format("Whirlpool"))
    print('{:>20} {}'.format("whirlpool:", position.whirlpool))
    print('{:>20} {}'.format("token_mint_a:", whirlpool.token_mint_a))
    print('{:>20} {}'.format("token_mint_b:", whirlpool.token_mint_b))
    print('{:>20} {}'.format("tick_spacing:", whirlpool.tick_spacing))
    print('{:>20} {}'.format("tick_current_index:", whirlpool.tick_current_index))
    print('{:>20} {}'.format("sqrt_price:", whirlpool.sqrt_price))
    print('{:>20} {}'.format("price:", DecimalUtil.to_fixed(price, decimals_b)))

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
    print('{:*^80}'.format("Position"))
    print('{:>20} {}'.format("name:", position.pubkey))
    print('{:>20} {}'.format("address:", position.position_mint))
    print('{:>20} {}'.format("liquidity:", position.liquidity))
    print('{:>20} {}'.format("a_amount(u64):", amounts.token_a))
    print('{:>20} {}'.format("b_amount(u64):", amounts.token_b))
    print('{:>20} {}'.format("status:", status))

    # input
    input_token = whirlpool.token_mint_b  # USDC
    input_amount = DecimalUtil.to_u64(Decimal(deposit_amount), decimals_b)  # USDC
    acceptable_slippage = Percentage.from_fraction(int(slippage), 100)
    # price_lower = price / 2
    # price_upper = price * 2
    print('{:<80}'.format("Building a quote for increasing liquidity..."))        
    # get quote
    quote = QuoteBuilder.increase_liquidity_by_input_token(IncreaseLiquidityQuoteParams(
        input_token_mint=input_token,
        input_token_amount=input_amount,
        token_mint_a=whirlpool.token_mint_a,
        token_mint_b=whirlpool.token_mint_b,
        sqrt_price=whirlpool.sqrt_price,
        tick_current_index=whirlpool.tick_current_index,
        tick_lower_index=position.tick_lower_index,
        tick_upper_index=position.tick_upper_index,
        slippage_tolerance=acceptable_slippage,
    ))
    print('{:*^80}'.format("Quote"))
    print('{:>20} {}'.format("liquidity:", quote.liquidity))
    print('{:>20} {}'.format("est_token_a:", quote.token_est_a))
    print('{:>20} {}'.format("est_token_b:", quote.token_est_b))
    print('{:>20} {}'.format("max_token_a:", quote.token_max_a))
    print('{:>20} {}'.format("token_max_b:", quote.token_max_b))
    
    # get ATA (considering WSOL)
    token_account_a = await TokenUtil.resolve_or_create_ata(ctx.connection, ctx.wallet.pubkey(), whirlpool.token_mint_a, quote.token_max_a)
    token_account_b = await TokenUtil.resolve_or_create_ata(ctx.connection, ctx.wallet.pubkey(), whirlpool.token_mint_b, quote.token_max_b)
    print('{:>20} {}'.format("token_account_a:", token_account_a.pubkey))
    print('{:>20} {}'.format("token_account_b:", token_account_b.pubkey))

    # build transaction
    tx = TransactionBuilder(ctx.connection, ctx.wallet)

    # WSOL considring
    tx.add_instruction(token_account_a.instruction)
    tx.add_instruction(token_account_b.instruction)

    # increase liquidity
    tick_array_lower_start_tick_index = TickUtil.get_start_tick_index(position.tick_lower_index, whirlpool.tick_spacing)
    tick_array_upper_start_tick_index = TickUtil.get_start_tick_index(position.tick_upper_index, whirlpool.tick_spacing)
    tick_array_lower = PDAUtil.get_tick_array(ctx.program_id, whirlpool_pubkey, tick_array_lower_start_tick_index).pubkey
    tick_array_upper = PDAUtil.get_tick_array(ctx.program_id, whirlpool_pubkey, tick_array_upper_start_tick_index).pubkey
    position_ata = TokenUtil.derive_ata(ctx.wallet.pubkey(), position.position_mint)
    increase_liquidity_ix = WhirlpoolIx.increase_liquidity(
        ctx.program_id,
        IncreaseLiquidityParams(
            whirlpool=whirlpool_pubkey,
            position=position_pda,
            position_token_account=position_ata,
            position_authority=ctx.wallet.pubkey(),
            liquidity_amount=quote.liquidity,
            token_max_a=quote.token_max_a,
            token_max_b=quote.token_max_b,
            token_owner_account_a=token_account_a.pubkey,
            token_owner_account_b=token_account_b.pubkey,
            token_vault_a=whirlpool.token_vault_a,
            token_vault_b=whirlpool.token_vault_b,
            tick_array_lower=tick_array_lower,
            tick_array_upper=tick_array_upper,
        )
    )
    tx.add_instruction(increase_liquidity_ix)

    if priority_fee is not None:
        tx.set_compute_unit_limit(200000)
        # add priority fees (+ 1000 lamports)
        # tx.set_compute_unit_price(int(1000 * 10**6 / 200000))
        tx.set_compute_unit_price(int(priority_fee * 10**6 / 200000))
    # execute
    print('{:<80}'.format("Build and execute transaction..."))
    signature = await tx.build_and_execute()
    print('{:>20} {}'.format("TX signature:", signature))
