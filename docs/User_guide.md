# ORCA Script CLI

ORCA Script CLI is a command-line interface tool designed to facilitate various operations related to managing positions, checking fees, and interacting with liquidity pools in decentralized finance (DeFi) environments.

## Commands

### 1. Open Position

#### Description
The `open-position` command allows you to open a new position within a liquidity pool.
#### Usage
```bash
$ orca open-position [options]
```
#### Options:
- --lower, -l: Lower end of the position.
- --upper, -u: Upper end of the position.
- --pool: Address of the liquidity pool.
- --token0, -t0: Address of token0.
- --token1, -t1: Address of token1.
- --amount0, -a0: Amount of token0.
- --amount1, -a1: Amount of token1.
- --liquidity, --lp: Overall amount of liquidity.
- --check: Check distribution necessary for each token0, token1.

### 6. Increase Position

#### Description

The `increase-position` command allows you to add tokens to an existing position.

#### Usage

TBD

### 7. Withdraw Position

#### Description

The `withdraw-position` command allows you to withdraw a certain amount from a position without burning the NFT.

#### Usage

TBD

### Additional Information

#### Installation

To install ORCA Script CLI, you can use pip:

```bash
$ pip install orca-cli
```

Requirements
Python 3.x
Dependencies specified in requirements.txt
License
This project is licensed under the MIT License. See the LICENSE file for details.

Contribution
Contributions are welcome! Please follow the guidelines outlined in CONTRIBUTING.md.

Support
For support or inquiries, please contact support@orca.com.