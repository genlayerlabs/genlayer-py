# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Setup
- Install dependencies: `uv sync --group dev`

### Testing
- Run all tests: `uv run pytest`
- Run specific test file: `uv run pytest tests/unit/test_client.py`
- Run e2e tests: `uv run pytest tests/e2e/`
- Run with verbose output: `uv run pytest -v`

### Build
- Build distribution: `uv build`

### Release
- Semantic version release: `./scripts/semantic-version-release.sh`
- Verify upstream: `./scripts/verify-upstream.sh`

## Architecture Overview

GenLayerPY is a Python SDK for interacting with the GenLayer blockchain protocol. The codebase follows a modular architecture:

### Core Components

1. **Client Layer** (`genlayer_py/client/`)
   - `GenLayerClient`: Main client class that wraps web3.py functionality
   - `create_client()`: Factory function for client instantiation
   - Handles consensus smart contract initialization automatically

2. **Chain Configuration** (`genlayer_py/chains/`)
   - Pre-configured chain objects (localnet, studionet, testnet_asimov, testnet_bradbury)
   - Each chain includes RPC URLs, contract addresses, and consensus parameters
   - Consensus contracts: CONSENSUS_MAIN and CONSENSUS_DATA with their ABIs

3. **Account Management** (`genlayer_py/accounts/`)
   - Account creation and private key generation
   - Integration with eth_account for signing operations

4. **Transaction Handling** (`genlayer_py/transactions/`)
   - Transaction creation, signing, and submission
   - Support for contract interactions (read/write operations)
   - Built-in transaction receipt waiting with status checking

5. **ABI and Encoding** (`genlayer_py/abi/`)
   - Calldata encoding/decoding utilities
   - Transaction ABI handling
   - Consensus-specific encoding for GenLayer protocol

6. **Contract Utilities** (`genlayer_py/contracts/`)
   - Contract interaction helpers
   - State status management (accepted, finalized)

### Key Design Patterns

- **Chain Abstraction**: All network configurations are encapsulated in chain objects
- **Web3.py Integration**: Built on top of web3.py for Ethereum compatibility
- **Consensus Integration**: Automatic initialization of consensus smart contracts
- **Type Safety**: Comprehensive type definitions in `genlayer_py/types/`

### Testing Structure

- **Unit Tests** (`tests/unit/`): Component-level testing for individual modules
- **E2E Tests** (`tests/e2e/`): Full integration tests against different networks
- **Test Configuration**: `conftest.py` sets up project root in Python path

### Entry Points

Main SDK exports from `genlayer_py/__init__.py`:
- `create_client()`: Primary client factory
- `create_account()`, `generate_private_key()`: Account utilities
- All chain configurations via wildcard import

### Development Workflow

1. The SDK is distributed via PyPI as `genlayer-py`
2. Supports Python 3.12+ with web3.py as the core dependency
3. Uses setuptools for packaging with automatic JSON ABI inclusion
4. Semantic versioning with automated release scripts