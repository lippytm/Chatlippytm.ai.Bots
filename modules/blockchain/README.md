# Blockchain Module (Placeholder)

This module is a placeholder for future blockchain-based AI integrations.

## Planned Integrations

- **Solidity smart contracts** that trigger AI model inference on-chain
- **IPFS-backed model storage** for decentralized AI asset hosting
- **Web3.js / ethers.js** JavaScript bindings for blockchain + AI pipelines
- **Hyperledger Fabric** chaincode templates for enterprise AI workflows

## Current Status

`enabled: false` in `config/config.yaml` — this module is scaffolded but not yet active.

## Getting Started (Future)

Once implemented, setup will involve:

1. Install a local blockchain node (e.g., Hardhat, Ganache):
   ```bash
   npm install --global hardhat
   npx hardhat node
   ```

2. Compile and deploy example contracts:
   ```bash
   npx hardhat compile
   npx hardhat run scripts/deploy.js --network localhost
   ```

3. Enable this module in `config/config.yaml`:
   ```yaml
   modules:
     blockchain:
       enabled: true
   ```

## Contributing

If you'd like to contribute blockchain integrations, please:

1. Open an issue describing your proposed integration.
2. Follow the module template established by the Python and JavaScript modules.
3. Add a corresponding entry in `config/extensions.json`.
4. Update `config/config.yaml` to include the new provider settings.
5. Submit a pull request with tests and documentation.
