# Key Points for Maintainers:

## Project Overview:

- ORCA CLMM Position Manager.
- Implements functionalities like opening, closing positions, checking fees, and collecting fees.
- Built in Python using libraries such as anchorpy, solana, solders.
- Command-line tool with no other frontend required.
## Workflow Expectations:

- Updates expected every 24 hours with progress summaries.
- Research topics and results to be shared.
- Code to be uploaded to a private git repository.
- Payment milestones defined in advance, no upfront payment.

## Functionality Missing for MS2:

- Need to gather PoolID, Token0, Token1 dynamically.
- Distribution changes based on lower and upper ends of the position.
- Check amount of fees earned.
- Code lacks comments and quality checks.
- Code organization needs improvement, preferably into a lib/class structure.
- Additional fees may be offered for complex tasks.

## Future Features and Suggestions:

- Integration with Django REST framework for API access.
- Implementation of a PostgreSQL database for storing position data, fees, etc.
- Integration with other CLMM pools like Raydium, Meteor.
- Exploration and integration of other DeFi/Dex instruments like Kamino Finance, MarginFi, Solend.

## RPC Endpoints:

- Use private RPC endpoints provided for reduced errors but cross-check with public endpoints.

# Key Points for Potential Developers:

## Requirements:

- In-depth understanding of Solana blockchain, Solana IDLs, Instructions, and Accounts.
- Proficiency in Python, particularly with anchorpy, solana, and solders libraries.
- Must understand project goals and implementation thoroughly.

## Responsibilities:

- Implement missing functionalities for MS2.
- Improve code quality, including comments and error handling.
- Organize code into a more structured form, preferably a lib/class structure.
- Potential future tasks include database integration, integration with other DeFi/Dex instruments.

## Workflow and Payment:

- Provide regular updates and share research findings.
- Upload code to a private git repository.
- Payment milestones defined; no upfront payment.

## Additional Notes:

- Consideration of future features and suggestions for project enhancements.
- Use provided private RPC endpoints but verify with public ones.