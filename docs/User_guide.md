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
- `--lower, -l`: Lower end of the position.
- `--upper, -u`: Upper end of the position.
- `--pool, -p`: Address of the liquidity pool.
<!-- - `--token0, -t0`: Address of token0.
- `--token1, -t1`: Address of token1. -->
- `--amount0, -a0`: Amount of token0.
- `--amount1, -a1`: Amount of token1.
<!-- - `--liquidity, --lp`: Overall amount of liquidity. -->
- `--check`: Check distribution necessary for each token0, token1.
#### Optional
- `--slippage, -s`: Slippage for the transaction (default: 0.3%).
- `--priority_fee, -pf`: Priority fee for the transaction (default: 0).


### 2. Check Fees

#### Description
The `check-fees` command allows users to check the fees gathered from positions.
#### Usage
```bash
$ orca check-fees [options]
```
#### Options:
- `--check_fees, -c`: Show fees for a specific position.
- `--check_all_fees, -C`: Show fees for all known positions.

#### Optional
- `--verbose, -v`: Enable verbose mode for detailed output.

### 3. Get Fees / Transfer Fees

#### Description

The `get-fees` command allows you to retrieve the fees generated from positions. Optionally, you can transfer these fees to a specified wallet address.

#### Usage
```bash
$ orca get-fees [options]
```
#### Options:
- `--get_fees, -f`: Get fees from one position.
- `--get_all_fees, -F`: Get fees from all positions.

- `--to-wallet,-w <addr>`: Transfer fees to specified wallet address.

#### Optional
- `--verbose, -v`: Enable verbose mode for detailed output.
#### Examples
- Get fees from a specific position:

```bash
$ orca check-fees [options]
```

- Get fees from all positions and transfer them to a specified wallet:
```bash
$ orca get-fees --get-all-fees --to-wallet <wallet_address>
```
#### Note
- Use the `--to-wallet` option to transfer the gathered fees to a wallet address.
- If not specified, the fees will remain in the wallet that created the position.


### 3. Increase Position

#### Description

The `increase-position` command allows you to add tokens to an existing position.

#### Usage

TBD

### 4. Withdraw Position

#### Description

The `withdraw-position` command allows you to withdraw a certain amount from a position without burning the NFT.

#### Usage

TBD

### 5. Close Position

#### Description

The `close-position` command allows you to close a position within a liquidity pool. By default, this command will also burn the corresponding NFT. However, you have the option to keep the NFT in the wallet or transfer it to a different wallet.

#### Usage
```bash
$ orca close-position <addr> [options]
```
#### Arguments:
- `<addr>`: Address of the position to be closed.

#### Options:
- `--slippage`: Slippage.
- `--priority_fee`: Priority fee in lamport.
- `--force`: Close all positions without specifying an address. Use this flag to circumvent accidental deletion.
- `--keep-nft`: Keep the NFT in the wallet instead of burning it.
- `--transfer-nft <wallet_address>`: Transfer the NFT to a different wallet address.

#### Examples
- Close a specific position and burn the NFT:

```bash
$ orca close-position <position_address>
```

- Close all positions and burn the NFTs (use with caution):

```bash
$ orca close-position --force
```

- Close a specific position and keep the NFT in the wallet:
```bash
$ orca close-position <position_address> --keep-nft
```

- Close a specific position and transfer the NFT to another wallet:

```bash
$ orca close-position <position_address> --transfer-nft <wallet_address>
```

#### Note
- Use the `--force` flag carefully to avoid accidental deletion of positions.
- The `--keep-nft` and `--transfer-nft` options provide flexibility in managing NFTs associated with closed positions.

### 6. Pool Gathering

#### Description

The `pool-gathering` command enables you to gather information about liquidity pools. You can retrieve details such as pool addresses, token pairs, fees, and current ticks/prices.

#### Usage
```bash
$ orca pool-gathering [options]
```

#### Options:
- `--show-pools`: Show all available pools along with their details.
- `--show-pool <address>`: Show detailed information about the pool with the specified address.

#### Examples
- Show all available pools:

```bash
$ orca pool-gathering --show-pools
```

- Show detailed information about a specific pool:

```bash
$ orca pool-gathering --show-pool <pool_address>
```

#### Note
- Use the `--show-pools` option to list all available pools and their details.
- The `--show-pool` option allows you to retrieve detailed information about a specific pool by providing its address.

#### Optional
- `-v, --verbose`: Enable verbose mode for detailed output.

### 6. Check Position

#### Description

The `check-position` command provides information about one or all positions, including pool details, token amounts, and current state.

#### Usage
```bash
$ orca check-position [options]
```

#### Options:
- `--show_position, -p`: Show information for a specific position by its address.

- `--show_positions, -P`: Show information for all positions.

- `--show_wallet_positions,-w <address>`: Show information for all positions of the specified wallet.
#### Optional
- `-v, --verbose`: Enable verbose mode for detailed output.

## Additional Information

### Installation

To install ORCA Script CLI, you can use pip:

```bash
$ pip install orca-cli
```

### Requirements
Python 3.10
Dependencies specified in requirements.txt

### License
This project is licensed under the MIT License. See the LICENSE file for details.

### Contribution
Contributions are welcome! Please follow the guidelines outlined in CONTRIBUTING.md.

### Support
For support or inquiries, please contact support@orca.com.