import argparse
import asyncio

from solders.pubkey import Pubkey

from orca_whirlpools_py.whirlpools import find_whirlpools, get_liquidity_distribution_by_whirlpools_pubkey, get_positions_by_wallet_pubkey
from orca_whirlpools_py.position_manager import open_position, add_liquidity, harvest_position_fees, harvest_whirlpool_fees, harvest_wallet_fees, get_whirlpool_and_show_info, check_position_fees, check_fees_rewards_of_position, check_whirlpool_fees, check_wallet_fees, close_position, withdraw_liquidity
from orca_whirlpools_py.positions import find_positions

from utils import get_context

'''    Sample command lines
- Open a position with deposit
python main.py open-position -u 250 -l 100 -wp HJPjoWUrhoZzkNfRpHuieeFk9WcZWjwy6PBjZ81ngndJ -a1 0.1 -c

- Gatheing pools
python main.py gather-pool -a

'''
# Implement functionality for opening a position
async def cli_open_position(args):
    # Implement functionality for opening a position
    at_least_one_arg_provided(args.amount0, args.amount1)
    ctx = get_context()
    whirlpool_pubkey = Pubkey.from_string(args.whirlpool)
    await open_position(ctx=ctx, whirlpool_pubkey=whirlpool_pubkey, upper=args.upper, lower=args.lower, slippage=args.slippage, priority_fee=args.priority_fee, amount0=args.amount0, amount1=args.amount1, check=args.check)

async def cli_increase_position(args):
    # Implement functionality for increasing a position
    pass

async def cli_withdraw_position(args):
    # Implement functionality for withdrawing a position
    pass

async def cli_pool_gathering(args):
    # Implement functionality for gathering pool information
    # The result are equivalent with when you access to https://www.orca.so/pools?mintvl=0
    if args.pool is not None:
        print("Gathering a specific pool is not supported yet, Sorry.")
        return
    # get all whirlpools
    if args.all:
        orca_supported_whirlpools = await find_whirlpools()
        # To show the result
        print('{:<43} {:<20} {:<8} {:<25} {:<45} {:<45} {:<4}'.format('address', 'name', 'usdTVL', 'price', 'mintA', 'mintB', 'tick_spacing'))
        for p in orca_supported_whirlpools:
            address = str(p.get("address", ""))
            name = p.get("name", "")
            price = p.get("price", 0)
            formatedPrice = "${:,.2f}".format(price)
            usdTVL = p.get("usdTVL", 0)
            formatedUsdTVL = "${:,.2f}".format(usdTVL)
            mintA = str(p.get("mintA", ""))
            mintB = str(p.get("mintB", ""))
            tick_spacing = p.get("tick_spacing", "")
            print('{:<43} {:<20} {:<8} {:<25} {:<45} {:<45} {:<4}'.format(address, name, formatedUsdTVL, formatedPrice, mintA, mintB, tick_spacing))
            
        print('{:<43} {:<20} {:<8} {:<25} {:<45} {:<45} {:<4}'.format('address', 'name', 'usdTVL', 'price', 'mintA', 'mintB', 'tick_spacing'))

        print(len(orca_supported_whirlpools), "whirlpools found")
    

async def cli_close_position(args):
    # Implement functionality for closing a position
    pass

async def cli_check_position(args):
    # Implement functionality for checking a position
    pass

async def cli_check_fees(args):
    # Implement functionality for checking fees
    pass

async def cli_get_fees(args):
    # Implement functionality for getting fees
    pass

def at_least_one_arg_provided(amount0, amount1):
    if (amount0 is None or amount0==0) and (amount1 is None or amount1 == 0):
        raise argparse.ArgumentTypeError('At least one of --amount0 or --amount1 is required.')
    
"""Main function to parse arguments and execute operations."""
async def main():
    parser = argparse.ArgumentParser(description='ORCA Script CLI')
    subparsers = parser.add_subparsers(title='subcommands', dest='subcommand')

    # Subparser for 'open-position' command
    open_position_parser = subparsers.add_parser('open-position', help='Open a position and deposit')
    open_position_parser.add_argument('--lower', '-l', required=True, type=float, help='Lower end')
    open_position_parser.add_argument('--upper', '-u', required=True, type=float, help='Upper end')
    open_position_parser.add_argument('--whirlpool', '-wp', required=True, help='Pool address')
    open_position_parser.add_argument('--slippage', '-s', default=0.3, help='Slippage')
    open_position_parser.add_argument('--priority_fee', '-pf', default=0, help='Priority fee, unit: lamport, example: 1000')
    # open_position_parser.add_argument('--token0', '-t0', required=True, help='Token0 address')
    # open_position_parser.add_argument('--token1', '-t1', required=True, help='Token1 address')
    # Add the arguments with custom required function
    open_position_parser.add_argument('--amount0', '-a0', required=False, type=float, help='Amount of token0')
    open_position_parser.add_argument('--amount1', '-a1', required=False, type=float, help='Amount of token1')
    # open_position_parser.add_argument('--liquidity', '-lp', required=False, type=float, help='Overall amount of liquidity')  
    open_position_parser.add_argument("--check", '-c', action="store_true", help="Flag to indicate whether to perform a check")


    # Subparser for 'increase-position' command - TBD

    # Subparser for 'withdraw-position' command - TBD

    # Subparser for 'gather-pool' command
    pool_gathering_parser = subparsers.add_parser('gather-pool', help='Gather pool information')
    pool_gathering_parser.add_argument('--all', '-a', action='store_true', help='Show all pools')
    pool_gathering_parser.add_argument('--pool', '-p', metavar='<address>', help='Show pool with specified address')

    # Subparser for 'close-position' command - TBD

    # Subparser for 'check-position' command
    check_position_parser = subparsers.add_parser('check-position', help='Check position')
    check_position_parser.add_argument('--show-position', '-p', metavar='address', help='Show position with specified address')
    check_position_parser.add_argument('--show-positions', '-P', action='store_true', help='Show all positions')

    # Subparser for 'check-fees' command
    check_fees_parser = subparsers.add_parser('check-fees', help='Check fees')
    check_fees_parser.add_argument('--check-fees', '-c', action='store_true', help='Check fees for one position')
    check_fees_parser.add_argument('--check-all-fees', '-C', action='store_true', help='Check fees for all positions')

    # Subparser for 'get-fees' command
    get_fees_parser = subparsers.add_parser('get-fees', help='Get fees')
    get_fees_parser.add_argument('--get-fees', '-f', action='store_true', help='Get fees from one position')
    get_fees_parser.add_argument('--get-all-fees', '-F', action='store_true', help='Get fees from all positions')
    get_fees_parser.add_argument('--to-wallet', '-w', metavar='addr', help='Transfer fees to specified wallet address')

    args = parser.parse_args()

    if args.subcommand == 'open-position':
        await cli_open_position(args)
    elif args.subcommand == 'gather-pool':
        await cli_pool_gathering(args)
    # Add more elif blocks for other subcommands
    else:
        parser.error("Invalid operation")

if __name__ == "__main__":
    asyncio.run(main())