import asyncio

from orca_whirlpools_py.whirlpools import find_whirlpools

async def main():
    # get all whirlpools
    # The result are equivalent with when you access to https://www.orca.so/pools?mintvl=0
    orca_supported_whirlpools = await find_whirlpools()
    
    # To show the result
    print("address\tname\tprice\tusdTVL\tmintA\tmintB\ttick_spacing")
    for p in orca_supported_whirlpools:
        address = str(p.get("address", ""))
        name = p.get("name", "")
        price = p.get("price", 0)
        usdTVL = '$' + str(p.get("usdTVL", 0))
        mintA = str(p.get("mintA", ""))
        mintB = str(p.get("mintB", ""))
        tick_spacing = p.get("tick_spacing", "")
        print(f"{address}\t{name}\t{price}\t{usdTVL}\t{mintA}\t{mintB}\t{tick_spacing}")
        
    print("address\tname\tprice\tusdTVL\tmintA\tmintB\ttick_spacing")

    print(len(orca_supported_whirlpools), "whirlpools found")
    
asyncio.run(main())