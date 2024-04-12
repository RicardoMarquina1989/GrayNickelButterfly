# Future Features

Those are features i can imagine to add to that tool, as soon as we are done with the first project. 

1. Creating django rest framework, where all the functionality is now accessable with an REST API, plus new calls. Rest API interaction at beginning can be done with Insomnia, please deliver examples for.
	1. configure get
		1. public key
	2. confgure set
		1. private key
	3. swap, from token to token
	- swapping from one token to the other
  	- swapping all or defined tokens to one token (for instance all token to SOL or USDC)
   	- using jupiter and orca for the start is ok  
	4. autoswap, if token amount of token0 or token1 is not enough for position
    	- thats very important if the management has to be automatic, so that positions can be easily opened and closed
     	- it is important here as well to check/simulate if transactions are working and trying to get the cheapest possible TX 
	5. show current and past data/positions (from database)
 	6. Of course all the other functionality integrated in the first project for the commandline client
	- check-pos, check-fees, open-position ...
	7. Transfer to wallet
 	8. Token, Pools must be also human readable, instead of addresses only
  	9. Amounts must be human read-able, instead of long decimals only 

2. Database (Postgresdb)
  
   This includes the structure, init sql file and fields for all data necessary for later financial analysis as  well as the program code to interface with the database. The database itself can run in a docker container. Database to use is postgresql. The functionality for database interactions shall include as well calculations for PnL of positions, fees ...
	1. Postgres database storing all information like
		1. existing positions
		2. past positions
		3. collected fees
		4. swapped tokens
	2. PnL over one position
 	3. PnL over all positions
  	4. With and without fees
 
3. Integration of other Dexes
   
   There are other CLMM Pools, which are interesting to integrate. However, to my knowledge at least RAY has no Python SDK, but python is the language we stick to.
	1. Raydium
	2. Meteor

4. Exploration and integration of other def/dex instruments like
	1. Kamino Finance
	2. MarginFi
	3. Solend

5. Integration of creating orders at CEX/DEX.
- Drift, Jupider, OKX
- Orders must - where possible - have limit, market, stop-loss and take-profit options
- DEX needs wallet deposit/withdraw of created accoutns
- CEX need usually an api key
Functionality:
- Authorize against DEX
- Create Order
- Withdraw / Deposit Token
- Close a position
- Close all positions
- Watch position, if still available
- Functionality to show all PnL and give a summary
- Set Take-profit, Stop-Loss of order
- Create positions with timer (start or end, only end, only start or both)
- Watch position and close on a certain condition

6. Possible Add-on Email / Telegramm integration 
If position is opened/closed or tokens are swapped send:
- email
- telegram
- interval, addresses and id configure-able with API
Send daily overview of token holdings, positions, PnL

### High Level Project Parts

I think best order of those features is:

1. Django and Feature integration
2. Database Support
3. Integration of DEX/CEX
4. Integration of additional Dex CLMM
5. Then we check state and what makes sense next



