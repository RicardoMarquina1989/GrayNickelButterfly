# Extract tasks and tickets from conversations
- Debugging
- Testing
- Storing Pool(json/txt/sqlite)
- close_position-Determination of parameters
- two issues on github:Several hardcoded keys/SqrtPrice of only one token
- Choose ORCA CLMM, Open Position, lower, upper ends - Note: PoolID, Token0, Token1 have to be gathered, as well as distribution with lower/upper ends
	- PoolID, Token0, Token1 are currently hardcoded, but not gathered
	- More Input:
		- there is only one clmm market in constants, but it is necessary to resolve the different markets/clmm pools otherwise i would need to check on the blockchain (SOL_USDC_WHIRLPOOL_PUBKEY = Pubkey.from_string("HJPjoWUrhoZzkNfRpHuieeFk9WcZWjwy6PBjZ81ngndJ"))
		- not sure what the best approach for that it, but i consider it mandatory to the tool, i can imagine the sdk is offering such function to get a list of current pools with pairs, ticks, space, sqrtprice
		- it must be clear, viewable what sort of token is in the pool, the address of the token, name, decimal
		- the distribution changes depending on the lower and upper end of the position
			- depending on the % of the size of already existing liquidiy and distance from current tick to upper/lower tick the distribution of each token changes, have you integrated that already?
	
- check amount of fees is missing or where is it hidden? :)
- the code is missing comments whats done where and why, it looks partially really like a block of monster code, maybe you can add some more infos/details
- i dont see a lot of checks for the functions (code quality), also not value wise, what happens if wrong values are added or a function crashes because of connection break or alike
- I would like to have the code in form of a lib/class or something, right now it looks a bit chaotic also because of the extra files in main directory, usually i like to place all the "extra" code in a directory, decide what methods/functions go into which file and then call them accordingly, i have usually files like: helper.py, utils.py ... you know organising it a bit, of course not all of those names might make sense here
	- i am aware i requested a "simple python script", but it got complex fast...i can also add a bit of money for this task if you want
- pairs, tick, space, sqrt price list
- viewable what sort of toke in in the pool
- the distribution changes depending on the lower and upper end of the position
- % of exisiting liquidity size
- code quality, error handing
- lib/class modulized folder structure
- orca UI vs console
- Rest Api + developed code
- input lower and uppend end as %?
</html>

# Current Status of tickets
It shows the status of tickets.
## MS 1 - Basic CLMM Setup, Python Interface Working with Orca CLMM Contract
- develop and test primary open_position script
- paid rpc url 
- initial readme
## MS2 - CLMM Functionality Completely Integrated, all requested functionality working 
- folder structure
- 
## MS3 - Documentation and stable code 
## MS4 - All bugs fixed, Project finished 
## MS N - All missing functions

# Future plan suggestions
