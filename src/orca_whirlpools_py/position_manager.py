import sys
import base58
from decimal import Decimal
from construct import Struct, Int64ul, Int32ul, Int8ul, Bytes

from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.signature import Signature

from solana.rpc.async_api import AsyncClient
from solana.rpc.types import TokenAccountOpts
from solana.rpc.core import TransactionExpiredBlockheightExceededError

# from spl.token.layouts import ACCOUNT_LAYOUT as SPL_ACCOUNT_LAYOUT
from spl.token.constants import TOKEN_PROGRAM_ID

from orca_whirlpool.types import Percentage
from orca_whirlpool.context import WhirlpoolContext
from orca_whirlpool.instruction import WhirlpoolIx, OpenPositionParams, CollectFeesParams, ClosePositionParams, CollectProtocolFeesParams, CollectRewardParams, DecreaseLiquidityParams, UpdateFeesAndRewardsParams, IncreaseLiquidityParams
from orca_whirlpool.transaction import TransactionBuilder
from orca_whirlpool.utils import TokenUtil, TickArrayUtil, DecimalUtil, PriceMath, PositionUtil, PDAUtil, TickUtil, LiquidityMath
from orca_whirlpool.quote import QuoteBuilder, IncreaseLiquidityQuoteParams, DecreaseLiquidityQuoteParams, CollectFeesQuoteParams, CollectRewardsQuoteParams

from solana.rpc.api import Client

SOL_TOKEN_MINT_ADDRESS = 'So11111111111111111111111111111111111111112'
SPL_ACCOUNT_LAYOUT = Struct(
    "mint"               / Bytes(32),
    "owner"              / Bytes(32),
    "amount"             / Int64ul,
    "delegate_option"     / Int32ul,
    "delegate"           / Bytes(32),
    "state"              / Int8ul,
    "is_native_option"     / Int32ul,
    "is_native"           / Int64ul,
    "delegated_amount"    / Int64ul,
    "close_authority_option" / Int32ul,
    "close_authority"     / Bytes(32),
)

'''
@func       Check balance of the token in the wallet
            When the balance is insufficient, exit the program
@return Bool
    True:   Sufficient,
    False:  Insufficient
'''
async def check_sufficient(ctx, token_mint_address, token_decimals, deposit_amount, token_fake_symbol):
    solana_client = ctx.connection

    balance = 0
    
    if str(token_mint_address) == SOL_TOKEN_MINT_ADDRESS:
        res = await solana_client.get_balance(ctx.wallet.pubkey())
        balance = res.value
    else:
        res = await solana_client.get_token_accounts_by_owner(ctx.wallet.pubkey(),TokenAccountOpts(mint=token_mint_address))
        if len(res.value) > 0:
            decoded_data = SPL_ACCOUNT_LAYOUT.parse(res.value[0].account.data)
            balance = decoded_data.amount/10**token_decimals
        else:
            balance = 0

    if deposit_amount > balance:
        print(f"Insufficient Balance of Token{token_fake_symbol}: {balance}")
        sys.exit()
    
    return deposit_amount >= balance, balance

"""
@func:      Open a position     based on upper and lower parameters.
@param:     WhirlpoolContext    ctx
@param:     int                 priority_fee unit-lamport
@return:    
"""
async def open_position(ctx: WhirlpoolContext, whirlpool_pubkey: Pubkey, 
                        upper: float, lower: float, amount0: float=0, amount1: float=0,
                        slippage:float=0.3, priority_fee: int = 0, check: bool = False) -> Signature:
    # get whirlpool
    whirlpool, price = await get_whirlpool_and_show_info(ctx=ctx, whirlpool_pubkey=whirlpool_pubkey)
    decimals_a = (await ctx.fetcher.get_token_mint(whirlpool.token_mint_a)).decimals
    decimals_b = (await ctx.fetcher.get_token_mint(whirlpool.token_mint_b)).decimals

    # input
    is_amount0_empty = amount0 is None or amount0 <= 0
    input_token = whirlpool.token_mint_b if is_amount0_empty else whirlpool.token_mint_a
    deposit_amount = amount1 if is_amount0_empty else amount0
    deposit_decimals = decimals_b if is_amount0_empty else decimals_a
    input_amount = DecimalUtil.to_u64(Decimal(deposit_amount), deposit_decimals)

    real_amount0 = 0
    real_amount1 = 0
    
    if is_amount0_empty: 
        real_amount1 = amount1
        real_amount0 = Decimal(amount1) / price
    else:
        real_amount0 = amount0
        real_amount1 = Decimal(amount0) * price

    await check_sufficient(ctx, whirlpool.token_mint_a, decimals_a, real_amount0, 'A')
    await check_sufficient(ctx, whirlpool.token_mint_b, decimals_b, real_amount1, 'B')
    
    acceptable_slippage = Percentage.from_fraction(int(slippage*100), 100)
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

    if check: 
        print('End of checking.')
        return None
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
    
    print('{:>20} {}'.format("slippage:", slippage))
    print('{:>20} {}'.format("priority_fee:", priority_fee))
    
    print('Executing transactions...')
    
    try:
        signature = await tx.build_and_execute()
        await print_transaction_res_text(signature, ctx.connection)
        return signature
    except TransactionExpiredBlockheightExceededError as e:
        # Handle the specific error
        print("Transaction expired due to block height exceeded:", e)
        return None
        # Perform any necessary cleanup or retries if needed
    except Exception as e:
        # Handle other exceptions
        print("An unexpected error occurred:", e)
        # Perform appropriate actions, like logging, retrying, or exiting gracefully
        return None

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

    try:
        # Execute transaction
        signature = await tx.build_and_execute()
        await print_transaction_res_text(signature, ctx.connection)
        return signature
    except TransactionExpiredBlockheightExceededError as e:
        # Handle the specific error
        print("Transaction expired due to block height exceeded:", e)
        return None
        # Perform any necessary cleanup or retries if needed
    except Exception as e:
        # Handle other exceptions
        print("An unexpected error occurred:", e)
        # Perform appropriate actions, like logging, retrying, or exiting gracefully
        return None

"""
@func:      Add liquidity to the specified position(select position address)
@param:     WhirlpoolContext    ctx
@param:     Pubkey              position_pubkey
@param:     int                 priority_fee unit-lamport
@return:    
"""
async def add_liquidity(ctx: WhirlpoolContext, position_pubkey: Pubkey, deposit_amount: float, slippage:float=0.3, priority_fee: int = 0):

    position_pda = PDAUtil.get_position(ctx.program_id, position_pubkey).pubkey
    position = await ctx.fetcher.get_position(position_pda, True)
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
    slippage *= 100
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
    
    print('{:<80}'.format("Build and execute transaction..."))
    try:
        # execute
        signature = await tx.build_and_execute()
        await print_transaction_res_text(signature, ctx.connection)
    except TransactionExpiredBlockheightExceededError as e:
        # Handle the specific error
        print("Transaction expired due to block height exceeded:", e)
        # Perform any necessary cleanup or retries if needed
    except Exception as e:
        # Handle other exceptions
        print("An unexpected error occurred:", e)

'''
@func: Harvest fees from a specific position
@author: 
'''
async def harvest_position_fees(ctx: WhirlpoolContext, position_pubkey: Pubkey):
    # get position
    position_pda = PDAUtil.get_position(ctx.program_id, position_pubkey).pubkey
    position = await ctx.fetcher.get_position(position_pda, True)
    whirlpool_pubkey = position.whirlpool
    # get whirlpool
    whirlpool, price = await get_whirlpool_and_show_info(ctx=ctx, whirlpool_pubkey=whirlpool_pubkey)
    
    # Execute transaction
    print('{:<80}'.format("Building and Executing transactions to collect fees of the position..."))
    try:
        await build_execute_collect_fees_reward_transactions(ctx=ctx, position=position, whirlpool=whirlpool)
    except TransactionExpiredBlockheightExceededError as e:
        # Handle the specific error
        print("Transaction expired due to block height exceeded:", e)
        # Perform any necessary cleanup or retries if needed
    except Exception as e:
        # Handle other exceptions
        print("An unexpected error occurred:", e)
        # Perform appropriate actions, like logging, retrying, or exiting gracefully
  

async def build_execute_collect_fees_reward_transactions(ctx: WhirlpoolContext, whirlpool, position):
    # For building quotes
    ta_lower_start_index = TickUtil.get_start_tick_index(position.tick_lower_index, whirlpool.tick_spacing)
    ta_upper_start_index = TickUtil.get_start_tick_index(position.tick_upper_index, whirlpool.tick_spacing)
    ta_lower_pubkey = PDAUtil.get_tick_array(ctx.program_id, position.whirlpool, ta_lower_start_index).pubkey
    ta_upper_pubkey = PDAUtil.get_tick_array(ctx.program_id, position.whirlpool, ta_upper_start_index).pubkey
    ta_lower = await ctx.fetcher.get_tick_array(ta_lower_pubkey)
    ta_upper = await ctx.fetcher.get_tick_array(ta_upper_pubkey)
    tick_lower = TickArrayUtil.get_tick_from_array(ta_lower, position.tick_lower_index, whirlpool.tick_spacing)
    tick_upper = TickArrayUtil.get_tick_from_array(ta_upper, position.tick_upper_index, whirlpool.tick_spacing)
    
    # position info
    position_mint = position.position_mint
    position_ata = TokenUtil.derive_ata(ctx.wallet.pubkey(), position_mint)
    position_pda = PDAUtil.get_position(ctx.program_id, position_mint).pubkey
    print('{:*^80}'.format("Position"))
    print('{:>20} {}'.format("name:", position.pubkey))
    print('{:>20} {}'.format("address:", position.position_mint))
    print('{:>20} {}'.format("liquidity:", position.liquidity))
    print('{:*^80}'.format(""))

    # ------------ Update_fees_and_rewards if liquidity is greather than 0  -------------
    if position.liquidity > 0:
        tick_array_lower_start_tick_index = TickUtil.get_start_tick_index(position.tick_lower_index, whirlpool.tick_spacing)
        tick_array_upper_start_tick_index = TickUtil.get_start_tick_index(position.tick_upper_index, whirlpool.tick_spacing)
        tick_array_lower = PDAUtil.get_tick_array(ctx.program_id, position.whirlpool, tick_array_lower_start_tick_index).pubkey
        tick_array_upper = PDAUtil.get_tick_array(ctx.program_id, position.whirlpool, tick_array_upper_start_tick_index).pubkey
        update_fees_and_rewards_ix = WhirlpoolIx.update_fees_and_rewards(
            ctx.program_id,
            UpdateFeesAndRewardsParams(
                whirlpool=position.whirlpool,
                position=position_pda,
                tick_array_lower=tick_array_lower,
                tick_array_upper=tick_array_upper,
            )
        )
        # Build transaction
        tx = TransactionBuilder(ctx.connection, ctx.wallet)
        tx.add_instruction(update_fees_and_rewards_ix)    
        tx.add_signer(ctx.wallet)
        # Execute transaction
        print("Initiating updates for fees and rewards transactions. Please wait....")
        signature = await tx.build_and_execute()
        await print_transaction_res_text(signature, ctx.connection)
    # ----------- End Update_fees_and_rewards --------------
    
    # get ATA (considering WSOL)
    token_account_a = await TokenUtil.resolve_or_create_ata(ctx.connection, ctx.wallet.pubkey(), whirlpool.token_mint_a)
    token_account_b = await TokenUtil.resolve_or_create_ata(ctx.connection, ctx.wallet.pubkey(), whirlpool.token_mint_b)
    
    # ----------Start collect_fees ---------------
    # get quote
    quote = QuoteBuilder.collect_fees(CollectFeesQuoteParams(
        whirlpool=whirlpool,
        position=position,
        tick_lower=tick_lower,
        tick_upper=tick_upper,
    ))
    print('{:*^80}'.format("Quote-Collect"))
    print('{:>20} {}'.format("fee_a_estimated:", quote.fee_a))
    print('{:>20} {}'.format("fee_b_estimated:", quote.fee_b))
    
    if quote.fee_a != 0 or quote.fee_b != 0: 
        collect_fees_ix = WhirlpoolIx.collect_fees(
            ctx.program_id,
            CollectFeesParams(
                whirlpool=whirlpool.pubkey,
                position=position_pda,
                position_authority=ctx.wallet.pubkey(),
                position_token_account=position_ata,
                token_owner_account_a=token_account_a.pubkey,
                token_vault_a=whirlpool.token_vault_a,
                token_owner_account_b=token_account_b.pubkey,
                token_vault_b=whirlpool.token_vault_b,
            )
        )
        tx = TransactionBuilder(ctx.connection, ctx.wallet)
        tx.set_compute_unit_limit(200000)
        # add priority fees (+ 1000 lamports)
        tx.set_compute_unit_price(int(1000 * 10**6 / 200000))
        # Add instructions
        tx.add_instruction(token_account_a.instruction)
        tx.add_instruction(token_account_b.instruction)
        tx.add_instruction(collect_fees_ix)
        tx.add_signer(ctx.wallet)
        # Execute transaction
        print("Processing fees collection transactions. Please wait...")
        signature = await tx.build_and_execute()
        await print_transaction_res_text(signature, ctx.connection)
    # ----------- End collect_fees --------------

    # ----------Start collect_rewards ---------------
    # quote rewards
    quote_rewards = QuoteBuilder.collect_rewards(CollectRewardsQuoteParams(
        whirlpool=whirlpool,
        position=position,
        tick_lower=tick_lower,
        tick_upper=tick_upper,
    ))

    print('{:*^80}'.format("Quote-Reward"))
    print('{:>20} {}'.format("Reward1:", quote_rewards.rewards[0]))
    print('{:>20} {}'.format("Reward2:", quote_rewards.rewards[1]))
    print('{:>20} {}'.format("Reward3:", quote_rewards.rewards[2]))
    # update
    latest_block_timestamp = await ctx.fetcher.get_latest_block_timestamp()
    print('{:>20} {}'.format("latest:", latest_block_timestamp))
    print('{:>20} {}'.format("whirlpool timestamp:", whirlpool.reward_last_updated_timestamp))
    
    def is_not_empty(val):
        if val != None and val != 0: return True
        return False
    
    result = all(is_not_empty(x) for x in quote_rewards.rewards)

    if result is True:
        quote_rewards2 = QuoteBuilder.collect_rewards(CollectRewardsQuoteParams(
            whirlpool=whirlpool,
            position=position,
            tick_lower=tick_lower,
            tick_upper=tick_upper,
            latest_block_timestamp=latest_block_timestamp.timestamp,
        ))
        print('{:*^80}'.format("Quote-Reward2"))
        print('{:>20} {}'.format("Reward1:", quote_rewards2.rewards[0]))
        print('{:>20} {}'.format("Reward2:", quote_rewards2.rewards[1]))
        print('{:>20} {}'.format("Reward3:", quote_rewards2.rewards[2]))

        reward_token_mint = whirlpool.reward_infos[0].mint
        reward_owner_account = TokenUtil.derive_ata(ctx.wallet.pubkey(), reward_token_mint)
    
        collect_reward_ix = WhirlpoolIx.collect_reward(
            ctx.program_id,
            CollectRewardParams(
                reward_index=0,
                whirlpool=whirlpool.pubkey,
                position_authority=ctx.wallet.pubkey(),
                position=position_pda,
                position_token_account=position_ata,
                reward_owner_account=reward_owner_account,
                reward_vault=whirlpool.reward_infos[0].vault,
            )
        )
        tx = TransactionBuilder(ctx.connection, ctx.wallet)
        # Add instructions
        tx.add_instruction(collect_reward_ix)
        tx.add_signer(ctx.wallet)
        # Execute transaction
        print("Initiating the process to collect rewards. Please wait...")
        
        try:
            signature = await tx.build_and_execute()
            await print_transaction_res_text(signature, ctx.connection)
        except TransactionExpiredBlockheightExceededError as e:
            # Handle the specific error
            print("Transaction expired due to block height exceeded:", e)
            # Perform any necessary cleanup or retries if needed
        except Exception as e:
            # Handle other exceptions
            print("An unexpected error occurred:", e)
    else:
        print('{:<80}'.format("There aren't any rewards"))
    # ----------- End collect_rewards --------------
'''
@func: Harvest fees and rewards of the whirlpool
    In other words, it iterates harvesting position by position
'''
async def harvest_whirlpool_fees(ctx: WhirlpoolContext, whirlpool_pubkey: Pubkey):
    print("Harvest fees and reward of the positions of the whirlpool")
    whirlpool, price = await get_whirlpool_and_show_info(ctx=ctx, whirlpool_pubkey=whirlpool_pubkey)

    # list all token accounts
    res = await ctx.connection.get_token_accounts_by_owner(
        ctx.wallet.pubkey(),
        TokenAccountOpts(program_id=TOKEN_PROGRAM_ID, encoding="base64")
    )
    token_accounts = res.value
    
    for token_account in token_accounts:
        parsed = TokenUtil.deserialize_account(token_account.account.data)

        # maybe NFT
        if parsed.amount == 1:
            # derive position address
            position_pubkey = PDAUtil.get_position(ctx.program_id, parsed.mint).pubkey
            position = await ctx.fetcher.get_position(position_pubkey)
            if position.whirlpool == whirlpool_pubkey:
                try:
                    await build_execute_collect_fees_reward_transactions(ctx=ctx, position=position, whirlpool=whirlpool)
                except TransactionExpiredBlockheightExceededError as e:
                    # Handle the specific error
                    print("Transaction expired due to block height exceeded:", e)
                    # Perform any necessary cleanup or retries if needed
                except Exception as e:
                    # Handle other exceptions
                    print("Transaction failed:", e)
                    # Perform appropriate actions, like logging, retrying, or exiting gracefully
                
'''
@func: Harvest fees and rewars of all positions of wallet. 
'''
async def harvest_wallet_fees(ctx: WhirlpoolContext):
    # list all token accounts
    res = await ctx.connection.get_token_accounts_by_owner(
        ctx.wallet.pubkey(),
        TokenAccountOpts(program_id=TOKEN_PROGRAM_ID, encoding="base64")
    )

    token_accounts = res.value
    whirlpool_pubkeys = []
    for token_account in token_accounts:
        parsed = TokenUtil.deserialize_account(token_account.account.data)

        # maybe NFT
        if parsed.amount == 1:
            # derive position address
            position_pubkey = PDAUtil.get_position(ctx.program_id, parsed.mint).pubkey
            position = await ctx.fetcher.get_position(position_pubkey)
            whirlpool_pubkeys.append(position.whirlpool)

    unique_whirlpool_pubkeys = list(set(whirlpool_pubkeys))
    if len(unique_whirlpool_pubkeys) > 0:
        print("Harvesting fees and rewards whirlpool by whirlpool")
        for whirlpool_pubkey in unique_whirlpool_pubkeys:
            await harvest_whirlpool_fees(ctx=ctx, whirlpool_pubkey=whirlpool_pubkey)

'''
Getting whirlpool and show the full info.
'''
async def get_whirlpool_and_show_info(ctx: WhirlpoolContext, whirlpool_pubkey: Pubkey):
    # get whirlpool
    print('{:<80}'.format("Getting whirlpool info..."))
    whirlpool = await ctx.fetcher.get_whirlpool(whirlpool_pubkey)
    if whirlpool is None:
        return

    # To log progress status
    decimals_a = (await ctx.fetcher.get_token_mint(whirlpool.token_mint_a)).decimals
    decimals_b = (await ctx.fetcher.get_token_mint(whirlpool.token_mint_b)).decimals
    price = PriceMath.sqrt_price_x64_to_price(whirlpool.sqrt_price, decimals_a, decimals_b)
    print('{:*^80}'.format("Whirlpool"))
    print('{:>20} {}'.format("whirlpool:", whirlpool.pubkey))
    print('{:>20} {}'.format("token_mint_a:", whirlpool.token_mint_a))
    print('{:>20} {}'.format("token_mint_b:", whirlpool.token_mint_b))
    print('{:>20} {}'.format("tick_spacing:", whirlpool.tick_spacing))
    print('{:>20} {}'.format("tick_current_index:", whirlpool.tick_current_index))
    print('{:>20} {}'.format("sqrt_price:", whirlpool.sqrt_price))
    print('{:>20} {}'.format("price:", DecimalUtil.to_fixed(price, decimals_b)))

    return whirlpool, price

'''
@func: Check fees and rewards of a specific position
'''
async def check_position_fees(ctx: WhirlpoolContext, position_pubkey: Pubkey):
    # get position
    position_pda = PDAUtil.get_position(ctx.program_id, position_pubkey).pubkey
    position = await ctx.fetcher.get_position(position_pda, True)
    whirlpool_pubkey = position.whirlpool
    # get whirlpool
    whirlpool, price = await get_whirlpool_and_show_info(ctx=ctx, whirlpool_pubkey=whirlpool_pubkey)
    
    # Execute transaction
    print('{:<80}'.format("Checking fees and rewards of the position..."))
    await check_fees_rewards_of_position(ctx=ctx, position=position, whirlpool=whirlpool)

'''
@func: Check fees and rewards of position-only 
@caller: check_position_fees
'''
async def check_fees_rewards_of_position(ctx: WhirlpoolContext, whirlpool, position):
    # For building quotes
    ta_lower_start_index = TickUtil.get_start_tick_index(position.tick_lower_index, whirlpool.tick_spacing)
    ta_upper_start_index = TickUtil.get_start_tick_index(position.tick_upper_index, whirlpool.tick_spacing)
    ta_lower_pubkey = PDAUtil.get_tick_array(ctx.program_id, position.whirlpool, ta_lower_start_index).pubkey
    ta_upper_pubkey = PDAUtil.get_tick_array(ctx.program_id, position.whirlpool, ta_upper_start_index).pubkey
    ta_lower = await ctx.fetcher.get_tick_array(ta_lower_pubkey)
    ta_upper = await ctx.fetcher.get_tick_array(ta_upper_pubkey)
    tick_lower = TickArrayUtil.get_tick_from_array(ta_lower, position.tick_lower_index, whirlpool.tick_spacing)
    tick_upper = TickArrayUtil.get_tick_from_array(ta_upper, position.tick_upper_index, whirlpool.tick_spacing)
    
    # position info
    print('{:*^80}'.format("Position"))
    print('{:>20} {}'.format("name:", position.pubkey))
    print('{:>20} {}'.format("address:", position.position_mint))
    print('{:>20} {}'.format("liquidity:", position.liquidity))
    
   # get quote
    quote = QuoteBuilder.collect_fees(CollectFeesQuoteParams(
        whirlpool=whirlpool,
        position=position,
        tick_lower=tick_lower,
        tick_upper=tick_upper,
    ))
    print('{:*^80}'.format("Quote-Collect"))
    print('{:>20} {}'.format("fee_a_estimated:", quote.fee_a))
    print('{:>20} {}'.format("fee_b_estimated:", quote.fee_b))

    # quote rewards
    quote_rewards = QuoteBuilder.collect_rewards(CollectRewardsQuoteParams(
        whirlpool=whirlpool,
        position=position,
        tick_lower=tick_lower,
        tick_upper=tick_upper,
    ))

    print('{:*^80}'.format("Quote-Reward"))
    print('{:>20} {}'.format("Reward1:", quote_rewards.rewards[0]))
    print('{:>20} {}'.format("Reward2:", quote_rewards.rewards[1]))
    print('{:>20} {}'.format("Reward3:", quote_rewards.rewards[2]))
    # update
    latest_block_timestamp = await ctx.fetcher.get_latest_block_timestamp()
    print('{:>20} {}'.format("latest:", latest_block_timestamp))
    print('{:>20} {}'.format("whirlpool timestamp:", whirlpool.reward_last_updated_timestamp))
    
    def is_not_empty(val):
        if val != None and val != 0: return True
        return False
    
    result = all(is_not_empty(x) for x in quote_rewards.rewards)

    if result is True:
        quote_rewards2 = QuoteBuilder.collect_rewards(CollectRewardsQuoteParams(
            whirlpool=whirlpool,
            position=position,
            tick_lower=tick_lower,
            tick_upper=tick_upper,
            latest_block_timestamp=latest_block_timestamp.timestamp,
        ))
        print('{:*^80}'.format("Quote-Reward2"))
        print('{:>20} {}'.format("Reward1:", quote_rewards2.rewards[0]))
        print('{:>20} {}'.format("Reward2:", quote_rewards2.rewards[1]))
        print('{:>20} {}'.format("Reward3:", quote_rewards2.rewards[2]))
    else:
        print('{:<80}'.format("There aren't any rewards"))

'''
@func: Check fees and rewards of the whirlpool
    In other words, it iterates checking position by position
'''
async def check_whirlpool_fees(ctx: WhirlpoolContext, whirlpool_pubkey: Pubkey):
    print("Check fees and reward of the positions of the whirlpool")
    whirlpool, price = await get_whirlpool_and_show_info(ctx=ctx, whirlpool_pubkey=whirlpool_pubkey)

    # list all token accounts
    res = await ctx.connection.get_token_accounts_by_owner(
        ctx.wallet.pubkey(),
        TokenAccountOpts(program_id=TOKEN_PROGRAM_ID, encoding="base64")
    )
    token_accounts = res.value
    
    for token_account in token_accounts:
        parsed = TokenUtil.deserialize_account(token_account.account.data)

        # maybe NFT
        if parsed.amount == 1:
            # derive position address
            position_pubkey = PDAUtil.get_position(ctx.program_id, parsed.mint).pubkey
            position = await ctx.fetcher.get_position(position_pubkey)
            if position.whirlpool == whirlpool_pubkey:
                await check_fees_rewards_of_position(ctx=ctx, position=position, whirlpool=whirlpool)
                
'''
@func: Check fees and rewars of all positions of wallet. 
'''
async def check_wallet_fees(ctx: WhirlpoolContext):
    # list all token accounts
    res = await ctx.connection.get_token_accounts_by_owner(
        ctx.wallet.pubkey(),
        TokenAccountOpts(program_id=TOKEN_PROGRAM_ID, encoding="base64")
    )

    token_accounts = res.value
    whirlpool_pubkeys = []
    for token_account in token_accounts:
        parsed = TokenUtil.deserialize_account(token_account.account.data)

        # maybe NFT
        if parsed.amount == 1:
            # derive position address
            position_pubkey = PDAUtil.get_position(ctx.program_id, parsed.mint).pubkey
            position = await ctx.fetcher.get_position(position_pubkey)
            whirlpool_pubkeys.append(position.whirlpool)

    unique_whirlpool_pubkeys = list(set(whirlpool_pubkeys))
    if len(unique_whirlpool_pubkeys) > 0:
        print("Checking fees and rewards of the whirlpool by whirlpool")
        for whirlpool_pubkey in unique_whirlpool_pubkeys:
            await check_whirlpool_fees(ctx=ctx, whirlpool_pubkey=whirlpool_pubkey)

"""
@func: Close a position.
"""
async def close_position(ctx: WhirlpoolContext, position_pubkey: Pubkey, slippage:int=30, priority_fee: int = 0):
    print("Position closing...")
    whirlpool, position = await withdraw_liquidity(ctx=ctx, position_pubkey=position_pubkey, slippage=slippage, priority_fee=priority_fee)
    
    if whirlpool is None or position is None: 
        print(f'Position(f{position_pubkey}) does not exist')
        return

    # collect fees and rewards
    try:
        await build_execute_collect_fees_reward_transactions(ctx, whirlpool=whirlpool, position=position)
    except TransactionExpiredBlockheightExceededError as e:
        # Handle the specific error
        print("Transaction expired due to block height exceeded:", e)
        return
    except Exception as e:
        # Handle other exceptions
        print("An unexpected error occurred:", e)
        return
    

    position_pda = PDAUtil.get_position(ctx.program_id, position_pubkey).pubkey
    position = await ctx.fetcher.get_position(position_pda, True)
    position_ata = TokenUtil.derive_ata(ctx.wallet.pubkey(), position.position_mint)
    ctx.fetcher.get_latest_block_timestamp
    
    # close position
    # build transaction
    tx = TransactionBuilder(ctx.connection, ctx.wallet)
    
    close_position_ix = WhirlpoolIx.close_position(
        ctx.program_id,
        ClosePositionParams(
            position_authority=ctx.wallet.pubkey(),
            receiver=ctx.wallet.pubkey(),
            position=position_pda,
            position_mint=position.position_mint,
            position_token_account=position_ata,
        )
    )
    tx.add_instruction(close_position_ix)
    tx.add_signer(ctx.wallet)
    if priority_fee is not None:
        tx.set_compute_unit_limit(200000)
        # add priority fees (+ 1000 lamports)
        # tx.set_compute_unit_price(int(1000 * 10**6 / 200000))
        tx.set_compute_unit_price(int(priority_fee * 10**6 / 200000))
    # Execute transaction
    print("Closing position process. Please wait...")
    
    try:
        signature = await tx.build_and_execute()
        await print_transaction_res_text(signature, ctx.connection)
    except TransactionExpiredBlockheightExceededError as e:
        # Handle the specific error
        print("Transaction expired due to block height exceeded:", e)
        # Perform any necessary cleanup or retries if needed
    except Exception as e:
        # Handle other exceptions
        print("An unexpected error occurred:", e)

'''
Decrease liquidity
'''
async def withdraw_liquidity(ctx: WhirlpoolContext, position_pubkey: Pubkey, slippage:float=0.3, priority_fee: int = 0):
    
    position_pda = PDAUtil.get_position(ctx.program_id, position_pubkey).pubkey
    position = await ctx.fetcher.get_position(position_pda, True)
    
    if position is None:
        return (None, None)
    
    position_ata = TokenUtil.derive_ata(ctx.wallet.pubkey(), position_pubkey)
    
    whirlpool, price = await get_whirlpool_and_show_info(ctx=ctx, whirlpool_pubkey=position.whirlpool)

    if position.liquidity == 0:
        print('Ballance of the position is zero.')
        return (whirlpool, position)
    
    token_account_a = await TokenUtil.resolve_or_create_ata(ctx.connection, ctx.wallet.pubkey(), whirlpool.token_mint_a)
    token_account_b = await TokenUtil.resolve_or_create_ata(ctx.connection, ctx.wallet.pubkey(), whirlpool.token_mint_b)
    
    tick_array_lower_start_tick_index = TickUtil.get_start_tick_index(position.tick_lower_index, whirlpool.tick_spacing)
    tick_array_upper_start_tick_index = TickUtil.get_start_tick_index(position.tick_upper_index, whirlpool.tick_spacing)
    tick_array_lower = PDAUtil.get_tick_array(ctx.program_id, position.whirlpool, tick_array_lower_start_tick_index).pubkey
    tick_array_upper = PDAUtil.get_tick_array(ctx.program_id, position.whirlpool, tick_array_upper_start_tick_index).pubkey
    slippage *= 100
    acceptable_slippage = Percentage.from_fraction(int(slippage), 100)
    
    # get quote
    quote = QuoteBuilder.decrease_liquidity_by_liquidity(DecreaseLiquidityQuoteParams(
        liquidity=position.liquidity,
        sqrt_price=whirlpool.sqrt_price,
        tick_current_index=whirlpool.tick_current_index,
        tick_lower_index=position.tick_lower_index,
        tick_upper_index=position.tick_upper_index,
        slippage_tolerance=acceptable_slippage
    ))
    print("liquidity", quote.liquidity)
    print("est_token_a", quote.token_est_a)
    print("est_token_b", quote.token_est_b)
    print("min_token_a", quote.token_min_a)
    print("min_token_b", quote.token_min_b)
    
    decrease_liquidity_ix = WhirlpoolIx.decrease_liquidity(
        ctx.program_id,
        DecreaseLiquidityParams(
            liquidity_amount=position.liquidity,
            token_min_a=quote.token_min_a,
            token_min_b=quote.token_min_b,
            whirlpool=position.whirlpool,
            position_authority=ctx.wallet.pubkey(),
            position=position_pda,
            position_token_account=position_ata,
            token_owner_account_a=token_account_a.pubkey,
            token_owner_account_b=token_account_b.pubkey,
            token_vault_a=whirlpool.token_vault_a,
            token_vault_b=whirlpool.token_vault_b,
            tick_array_lower=tick_array_lower,
            tick_array_upper=tick_array_upper,
        )
    )
    tx = TransactionBuilder(ctx.connection, ctx.wallet)
    if priority_fee is not None:
        tx.set_compute_unit_limit(200000)
        # add priority fees (+ 1000 lamports)
        # tx.set_compute_unit_price(int(1000 * 10**6 / 200000))
        tx.set_compute_unit_price(int(priority_fee * 10**6 / 200000))

    tx.add_instruction(token_account_a.instruction)
    tx.add_instruction(token_account_b.instruction)
    tx.add_instruction(decrease_liquidity_ix)
    tx.add_signer(ctx.wallet)

    # Execute transaction
    print("Executing withdraw transaction...")

    try:
        signature = await tx.build_and_execute()
        await print_transaction_res_text(signature, ctx.connection)
        return (whirlpool, position)
    except TransactionExpiredBlockheightExceededError as e:
        # Handle the specific error
        print("Transaction expired due to block height exceeded:", e)
        return (None, None)
        # Perform any necessary cleanup or retries if needed
    except Exception as e:
        # Handle other exceptions
        print("An unexpected error occurred:", e)
        # Perform appropriate actions, like logging, retrying, or exiting gracefully
        return (None, None)
    

'''
Check GetSignatureStatusesResp from Signature
'''
async def get_transaction_status(tx_signature: Signature, async_client: AsyncClient):
    signatures = [tx_signature]
    resp = await async_client.get_signature_statuses(signatures,search_transaction_history=True)
    resp_json = resp.value
    
    '''
    A JSON object with the following fields:
    confirmationStatus
        The transaction's cluster confirmation status. It can either be processed, confirmed, or finalized
    confirmations
        The number of confirmations a transaction has received. If the transaction is finalized (i.e., confirmed at the highest level of commitment), the value will be null
    err
        Error code if the transaction failed or null if the transaction succeeds
    slot
        The slot number in which the transaction was confirmed
    status
        The processing status of the transaction. It returns Ok if the transaction was successful and Err if the transaction failed with TransactionError
    '''
    
    # return {key: resp_json[0][key] for key in ['confirmationStatus', 'confirmations', 'err', 'slot', 'status']}
    return {
        'err':                  resp_json[0].err,
        'slot':                 resp_json[0].slot,
        'status':               resp_json[0].status,
        'confirmations':        resp_json[0].confirmations,
        'confirmation_status':   resp_json[0].confirmation_status
    }

'''
Just convert from GetSignatureStatusesResp to string
'''
def convert_transaction_status2str(transaction):
    # Extracting individual fields
    confirmation_status = str(transaction.get('confirmation_status'))
    confirmations = transaction.get('confirmations')
    err = transaction.get('err')

    # Generating xx
    xx = "Success" if err is None else "Fail"

    # Generating zz
    zz = str(confirmations) if confirmations is not None else "MAX Confirmations"

    # Generating yy
    converted = f"{xx} | {confirmation_status} {zz}"
    
    return converted

'''
@todo: Get transaction status as human readable string from Signature instance.
'''
async def get_transaction_res_text(tx_signature: Signature, async_client: AsyncClient):
    if tx_signature is None:
        return ''
    
    transaction_status = await get_transaction_status(tx_signature, async_client)
    converted = convert_transaction_status2str(transaction_status)

    return converted

'''
@todo: Print transaction status as human readable string from Signature instance after transaction was executed.
'''
async def print_transaction_res_text(tx_signature: Signature, async_client: AsyncClient):
    if tx_signature is None: return
    
    print('{:-^40}'.format("Transaction Result"))
    print('TX signature:', tx_signature)
    print(f"https://solscan.io/tx/{tx_signature}")

    res_text = await get_transaction_res_text(tx_signature, async_client)
    if res_text != None:
        print(res_text)

def validate_solana_address(address):
    # Check length
    if len(address) != 44:
        return False
    # Character set
    try:
        base58.b58decode(address.encode())
    except:
        return False
    # Prefix
    # if not address.startswith("G"):
    #     return False
    return True