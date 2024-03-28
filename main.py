import argparse
import asyncio

from orca_whirlpool.transaction import TransactionBuilder

from position import get_context, list_position, update_fees_and_rewards, collect_fees, collect_reward, open_position, close_position, collect_fees

async def main():
    """Main function to parse arguments and execute operations."""
    parser = argparse.ArgumentParser(description="Script for performing various operations.")
    parser.add_argument("operation", choices=["open", "close", "collect", "list"], help="Operation to perform")
    parser.add_argument("--upper", type=int, help="Upper parameter for 'open' operation")
    parser.add_argument("--lower", type=int, help="Lower parameter for 'open' operation")
    args = parser.parse_args()

    # Build transaction
    ctx = get_context()
    tx = TransactionBuilder(ctx.connection, ctx.wallet)
    
    if args.operation == "open":
        if args.upper is None or args.lower is None:
            parser.error("For 'open' operation, both upper and lower parameters are required.")
        else:
            await open_position(upper=args.upper, lower=args.lower)
    elif args.operation == "close":
        # call functions one by one to close the position
        # await decrease_liquidity(tx, False)
        # await update_fees_and_rewards(tx, False)
        # collect
        # await collect_fees(tx, False)
        # await collect_reward(tx, False)
        await close_position(tx, True)
    elif args.operation == "collect":
        update_fees_and_rewards(tx, False)
        collect_fees(tx, False)
        collect_reward(tx, True)
    elif args.operation == "list":
        await list_position()
    else:
        parser.error("Invalid operation")

if __name__ == "__main__":
    asyncio.run(main())
