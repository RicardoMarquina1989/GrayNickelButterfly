import asyncio

from orca_whirlpools_py.whirlpools import find_whirlpools
async def main():
    # get all whirlpools
    # The result are equivalent with when you access to https://www.orca.so/pools?mintvl=0
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
    
asyncio.run(main())