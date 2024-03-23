
# Title: Orca CLMM Position Manager Script

## Concept
### Concentrated Liquidity Market Maker (CLMM)
- A Concentrated Liquidity Market Maker (CLMM) is a liquidity model that allows liquidity providers (LPs) to allocate their tokens within a selected price range where they will be actively used. Instead of distributing liquidity evenly across an infinite range as in traditional Automated Market Makers (AMMs), CLMMs allow for the pooled funds to be utilized more efficiently within the market or exchange.

- Traders can select a specific price range for their tokens, focusing on liquidity where they anticipate market activity. However, using concentrated liquidity market makers (CLMMs) can result in potential losses similar to those associated with active market-making within a traditional order book market.

### Why is it important to actively manage your positions?

In CLMMs, there is a need for constant engagement in the market. The LPs and traders must be active to keep their concentrated positions more secure and tight within the price range. They would have to closely monitor their positions and frequently adjust to set up new ranges once the price moves up to the set price boundaries.

Active management helps to reduce the chances of impermanent loss and zero fees. Also, it is less expensive to manage concentrated liquidity market makers (CLMMs). Unlike on Ethereum Virtual Machine, the execution fees cost less on Solana and do not have scalability issues.

Close-range liquidity supply earns more fees than liquidity spread out on a much larger scale. Concentrated ranges ensure effective liquidity deployment. However, to maintain the set position and supply liquidity requires active participation. 

## Aim
- open position
- close position
- collect fees
- trasfer rewars to owner wallet

## Dependencies
This library have been tested in the following environment.

* Python: 3.10.6
* solders: 0.18.1
* solana: 0.30.2
* anchorpy: 0.18.0

## Installation
```commandline
pip install -r requirements.txt
```

## Run

```commandline
python3 main.py
```
