

# Commandline Options for ORCA Script
## Open Position

### Description
This is for setting up a position, in theory you want to give two amounts, BUT in practise you do not know the amount exactly before. Because, depending on the lower and upper end the % of amount differs. This seems also depend on how much other positions are in that range. So it *might* be that, one or two flags are not necessary.

This is why, i say here `--lp` which is the overall amount of liquidity and the flag `--check` which shall not create the position, but show the distribution necessary for each token0, token1. So first check, then create:

Slashes show a long and short option for argparse (https://stackoverflow.com/questions/28638813/how-to-make-a-short-and-long-version-of-a-required-argument-using-python-argpars)

Also not looked at is the situation of slippage and priority fee settings (this is important for getting a txid done). So there needs to be a flag for slippage and priority fee. Slippage ranges are `0.1` - `1.5%`, default should be `0.3%`. Priority fee i would set by default to `0`. 
flag for slippage `-s`, for priority fee `-S`. It is crucial, that it is checked if a transaction can be done with the settings. Otherwise there will be created bad transactions. For this there should be something like an automated simulation. And if the simulation worked automatically create the tx. If it failed, tell on the commandline. Of course this could be enhanced dramatically with cool algorithms, but this is out of scope of that tool.

Also i recognized that two types of functionality are completelly missing which is, increasing a position and only withdraw a certain amount from a position. For those i would like to add TBD amount of money to our current project, so you can add them. 

### CLI
-> *check*
long / short (argparse)
`--open-position / -o --lower --upper --pool --token0 --token1  --liquidity / --lp --check`

-> *create*
long / short (argparse)
`--open-position / -o --lower /-l  --upper/u  --pool --token0 / -t0 --token1 /-t1 --amount0 / -a0 --amount1 / -a1`


## Increase Position

Add token to already existing position

### CLI

TBD

## Withdraw Position

This is close to the feature of closing a position, but different, as only a certain amount is withdrawn and the NFT is *NOT* burned.

### CLI

TBD

## Pool Gathering

### Description

This is part before a position can be created. It must be possible to get a list of existing pools with address, token0,token1, fee, current ticks/price. Tokens must show address AND name. Address is also very important to excluse fake tokens with the same name. 


### CLI
`--show-pools `

`--show-pool \<address\>`

Would be nice to check for pools which have only USDC oder SOL/WSOL, but i this might be an extra, we can do as additional contract negotiation/money
## Close Position

### Description

Close a position. Normally also the corresponding NFT has to be burned. This should be done by default, but
also possible NOT to burn the NFT but instead:

1. Keeping the NFT in the wallet
2. Transfering the NFT to a different wallet

## CLI

To close a position
`--close-position \addr\`

Close all positions, no address is necessary, but an extra flag has to be given to circumvent accidently deletion. Flag like `--force`

`--close-all-positions`

## Check Position

### Description
Show all or one position, with pool, token, amount, current state of pool like tiicks, if in range or not. 

### CLI
Show one position only with address
long / short (argparse)
`--show-position address / -p`

Show all positions
long / short (argparse)
`--show-positions / -P`

## Check fees

### Description

Check how much fees have been gathered. Output should be at least token0, token1 and what kind of token it is (name) + address and current value of the fees. Value should be gatherable with the sqrt price, if not an external api like coinmarketcap/molaris or coingecko can be used. This might be already out of scope of that tool. As we would need further discussion which api to integrate and further testing not agreed beforehand.

### Cli Options

one position
long / short

`--check-fees / -c`

all known positions	
long / short
`--check-all-fees  / -C`
## Get Fees / Transfer fees

### Description

Get the generate fees from the position/pool.

Goal is to  transfer the fees to the owner of a wallet. After the fees have been gathered to the wallet of the wallet which created the position.

*Collect Fees* -> fees will go to wallet which created position -> now transfer to a predefined wallet address. Consider it as a situation with 2 involved parties. Where one party is creating the position and the fees are stored in a different wallet. This enables at least three interesting scenarios (just fyi)

1. Makes it possible to 3rd parties openening positions 
2. Still deliver them the fees
3. For the person who owns both addresses one wallet where only the fees are going and one for creating the positions

### CLI Options

one position, no transfer to other wallet, the fees are normally gathered to the wallet which created the position 
long / short (argparse)
`--get-fees / -f`

one position, transfer to other wallet, fees are gathered and afterwards transfered to a defined wallet
long / short (argparse)
`--get-fees / -f --to-wallet / -w addr`


get fees from all positions, no transfer to other wallet, the fees are normally gathered to the wallet which created the position 

long / short (argparse)

`--get-all-fees / -F`

get fees from all positions, transfer to other wallet, fees are gathered and afterwards transfered to a defined wallet

long / short (argparse)

`--get-all-fees / -F --to-wallet / -w`



