# Future Features

Those are features i can imagine to add to that tool, as soon as we are done with the first project. 

1. Creating django rest framework, where all the functionality is now accessable with an REST API, plus new calls like
	1. configure get
		1. public key
	2. confgure set
		1. private key
	3. swap, from token to token
	- swapping from one token to the other
  	- swapping all or defined tokens to one token (for instance all token to SOL or USDC)
   	- using jupiter and orca for the start is ok  
	5. autoswap, if token amount of token0 or token1 is not enough for position
    	- thats very important if the management has to be automatic, so that positions can be easily opened and closed
     	- it is important here as well to check/simulate if transactions are working and trying to get the cheapest possible TX 
	7. show current and past data/positions (from database)

2. Database
  
   This includes the structure, init sql file and fields for all data necessary for later financial analysis as  well as the program code to interface with the database. The database itself can run in a docker container. Database to use is postgresql. The functionality for database interactions shall include as well calculations for PnL of positions, fees ...
	1. Postgres database storing all information like
		1. existing positions
		2. past positions
		3. collected fees
		4. swapped tokens
5. Integration of other Dexes
   
   There are other CLMM Pools, which are interesting to integrate. However, to my knowledge at least RAY has no Python SDK, but python is the language we stick to.
	1. Raydium
	2. Meteor

6. Exploration and integration of other def/dex instruments like
	1. Kamino Finance
	2. MarginFi
	3. Solend

I think best order of those features is:

1. Django Integration
2. Database Support
3. Integration of additional Dexes
4. Then we check state and what makes sense next



