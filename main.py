import argparse
import asyncio
import os
import json
from dotenv import load_dotenv
from pathlib import Path
from typing import NamedTuple
from solana.rpc.async_api import AsyncClient
from solana.rpc.types import TokenAccountOpts
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from spl.token.constants import TOKEN_PROGRAM_ID

from orca_whirlpool.constants import ORCA_WHIRLPOOL_PROGRAM_ID
from orca_whirlpool.context import WhirlpoolContext
from orca_whirlpool.utils import TokenUtil, DecimalUtil, LiquidityMath, PriceMath, PDAUtil, PositionUtil, TickUtil
from orca_whirlpool.types import Percentage
from orca_whirlpool.constants import ORCA_WHIRLPOOL_PROGRAM_ID
from orca_whirlpool.instruction import WhirlpoolIx, OpenPositionParams, InitializePoolParams, IncreaseLiquidityParams
from orca_whirlpool.transaction import TransactionBuilder
from orca_whirlpool.quote import QuoteBuilder, IncreaseLiquidityQuoteParams

load_dotenv()
RPC_ENDPOINT_URL = os.getenv("RPC_ENDPOINT_URL")
MY_WALLET_PUBKEY = Pubkey.from_string("r21Gamwd9DtyjHeGywsneoQYR39C1VDwrw7tWxHAwh6")
SOL_USDC_WHIRLPOOL_PUBKEY = Pubkey.from_string("HJPjoWUrhoZzkNfRpHuieeFk9WcZWjwy6PBjZ81ngndJ")

class PositionRelatedAccounts(NamedTuple):
    mint: Pubkey
    token_account: Pubkey
    position: Pubkey

def main():
    parser = argparse.ArgumentParser(description="Script for performing various operations.")
    parser.add_argument("operation", choices=["open", "close", "collect"], help="Operation to perform")
    parser.add_argument("--upper", type=float, help="Upper parameter for 'open' operation")
    parser.add_argument("--lower", type=float, help="Lower parameter for 'open' operation")
    
    args = parser.parse_args()

    if args.operation == "open":
        if args.upper is None or args.lower is None:
            parser.error("For 'open' operation, both upper and lower parameters are required.")
        else:
            asyncio.run(open_position(args.upper, args.lower))
    elif args.operation == "close":
        close_position()
    elif args.operation == "collect":
        collect_operation()
    elif args.operation == "list":
        asyncio.run(list_position())
    else:
        parser.error("Invalid operation")

async def open_position(upper, lower):
    print(f"Performing 'open' operation with upper={upper} and lower={lower}")
    # read wallet
    # - how to create: solana-keygen new -o wallet.json
    # - need some USDC and SOL
    with Path("wallet.json").open() as f:
        keypair = Keypair.from_bytes(bytes(json.load(f)))
    print("wallet pubkey", keypair.pubkey())
    print("wallet prive", keypair)

    # create client
    connection = AsyncClient(RPC_ENDPOINT_URL)
    ctx = WhirlpoolContext(ORCA_WHIRLPOOL_PROGRAM_ID, connection, keypair)

    # get whirlpool
    whirlpool_pubkey = SOL_USDC_WHIRLPOOL_PUBKEY
    whirlpool = await ctx.fetcher.get_whirlpool(whirlpool_pubkey)
    
    # Not found whirlpool
    if whirlpool is None:
        # Current SOL/USDC price
        desiredMarketPrice = Decimal(189)
        # Invert due to token mint ordering
        actualPrice = Decimal(1).div(desiredMarketPrice)
        # Shift by 64 bits
        initSqrtPrice = DecimalUtil.to_u64(Decimal("0.01"), actualPrice)

        whirlpoolPda = PDAUtil.get_whirlpool(whirlpool_pubkey, )
        # initialize pool
        open_position_ix = WhirlpoolIx.initialize_pool(
            ctx.program_id,
            InitializePoolParams(
                tick_spacing=128,
                initial_sqrt_price=initSqrtPrice,
                whirlpool_pda=whirlpool,
                whirlpools_config=tick_upper_index,
                token_mint_a="position_pda",
                position_mint=position_mint.pubkey(),
                position_token_account=position_ata,
                funder=ctx.wallet.pubkey(),
                owner=ctx.wallet.pubkey(),
            )
        )
        tx.add_instruction(open_position_ix)
        
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
    input_amount = DecimalUtil.to_u64(Decimal("0.01"), decimals_b)  # USDC
    acceptable_slippage = Percentage.from_fraction(1, 100)
    price_lower = price / 2
    price_upper = price * 2
    tick_lower_index = PriceMath.price_to_initializable_tick_index(price_lower, decimals_a, decimals_b, whirlpool.tick_spacing)
    tick_upper_index = PriceMath.price_to_initializable_tick_index(price_upper, decimals_a, decimals_b, whirlpool.tick_spacing)

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
    # tick_array_lower_start_tick_index = TickUtil.get_start_tick_index(tick_lower_index, whirlpool.tick_spacing)
    # tick_array_upper_start_tick_index = TickUtil.get_start_tick_index(tick_upper_index, whirlpool.tick_spacing)
    # tick_array_lower = PDAUtil.get_tick_array(ctx.program_id, whirlpool_pubkey, tick_array_lower_start_tick_index).pubkey
    # tick_array_upper = PDAUtil.get_tick_array(ctx.program_id, whirlpool_pubkey, tick_array_upper_start_tick_index).pubkey
    # increase_liquidity_ix = WhirlpoolIx.increase_liquidity(
    #     ctx.program_id,
    #     IncreaseLiquidityParams(
    #         whirlpool=whirlpool_pubkey,
    #         position=position_pda.pubkey,
    #         position_token_account=position_ata,
    #         position_authority=ctx.wallet.pubkey(),
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

async def list_position():
    print("Performing 'list' operation")
    connection = AsyncClient(RPC_ENDPOINT_URL)
    ctx = WhirlpoolContext(ORCA_WHIRLPOOL_PROGRAM_ID, connection, Keypair())

    # read wallet
    # - how to create: solana-keygen new -o wallet.json
    # - need some USDC and SAMO
    # with Path("wallet.json").open() as f:
    #     keypair = Keypair.from_bytes(bytes(json.load(f)))
    # print("wallet pubkey", keypair.pubkey())
    # MY_WALLET_PUBKEY = keypair.pubkey()
    # list all token accounts
    res = await ctx.connection.get_token_accounts_by_owner(
        MY_WALLET_PUBKEY,
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

def close_position():
    print("Performing 'close' operation")

def collect_operation():
    print("Performing 'collect' operation")

if __name__ == "__main__":
    main()
