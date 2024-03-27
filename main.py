import argparse
import asyncio

from position import open_position, close_position, collect_operation

async def main():
    """Main function to parse arguments and execute operations."""
    parser = argparse.ArgumentParser(description="Script for performing various operations.")
    parser.add_argument("operation", choices=["open", "close", "collect"], help="Operation to perform")
    parser.add_argument("--upper", type=int, help="Upper parameter for 'open' operation")
    parser.add_argument("--lower", type=int, help="Lower parameter for 'open' operation")
    args = parser.parse_args()

    if args.operation == "open":
        if args.upper is None or args.lower is None:
            parser.error("For 'open' operation, both upper and lower parameters are required.")
        else:
            await open_position(upper=args.upper, lower=args.lower)
    elif args.operation == "close":
        close_position()
    elif args.operation == "collect":
        collect_operation()
    else:
        parser.error("Invalid operation")

if __name__ == "__main__":
    asyncio.run(main())
