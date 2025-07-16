# Contributing to GenLayerPY SDK

We're thrilled that you're interested in contributing to the GenLayerPY SDK! This document will guide you through the contribution process.

## What is the GenLayerPY SDK?

The GenLayerPY SDK is a Python library designed for developers building decentralized applications (Dapps) on the GenLayer protocol. It provides a comprehensive set of tools to interact with the GenLayer network, including client creation, transaction handling, event subscriptions, and more, all while leveraging the power of web3.py as the underlying blockchain client.

## How You Can Contribute?

Contributions to the GenLayerPY SDK are welcome in several forms:

### Testing the SDK and Providing Feedback

Help us make the SDK better by testing and giving feedback:

- Start by installing the SDK in your Dapp using the command:
  ```sh
  $ pip install genlayer-py
  ```
- Try out the SDK features and tell us what you think through our [feedback form](https://docs.google.com/forms/d/e/1FAIpQLSckZhe1WENv4ZtkMyrQSAun3bpOcQaa-21Ha8Zd174as-pltw/viewform?usp=sharing) or on our [Discord Channel](https://discord.gg/8Jm4v89VAu).
- If you find any issues, please report them on our [GitHub issues page](https://github.com/yeagerai/genlayer-py/issues).

### Sharing New Ideas and Use Cases

Have ideas for new features or use cases? We're eager to hear them! But first:

- Ensure you have the SDK installed to explore existing use cases.
- After familiarizing yourself with the SDK, contribute your unique use case and share your ideas in our [Discord channel](https://discord.gg/8Jm4v89VAu).

### Bug fixing and Feature development

#### 1. Set yourself up to start coding

- **1.1. Pick an issue**: Select one from the project GitHub repository [issue list](https://github.com/yeagerai/genlayer-py/issues) and assign it to yourself.

- **1.2. Create a branch**: create the branch that you will work on by using the link provided in the issue details page (right panel at the bottom - section "Development")

- **1.3. Setup the SDK locally**: clone the repository

   ```sh
   $ git clone https://github.com/yeagerai/genlayer-py.git
   ```

- **1.4. Add the package to your project locally**: to add the package locally, use the command:
  - **Option 1:** Install the package in regular mode
      ```sh
      $ pip install path/to/genlayer-py
      ```
  - **Option 2:** Install the package in editable mode

      ```sh
      $ pip install -e path/to/genlayer-py --config-settings editable_mode=strict
      ```
   This will allow you to use the package in your project without publishing it. With option 1 you need to re-install the package on every changes you make and with option 2 you only need to perform a re-installation if you change the project metadata. You can find more information in the pip [documentation](https://pip.pypa.io/en/stable/topics/local-project-installs/)


#### 2. Submit your solution

- **2.1. Black Formatter on Save File**: Configure IDE extensions to format your code with [Black](https://github.com/psf/black/) before submitting it.
- **2.2. Code solution**: implement the solution in the code.
- **2.3. Pull Request**: Submit your changes through a pull request (PR). Fill the entire PR template and set the PR title as a valid conventional commit.
- **2.4. Check PR and issue linking**: if the issue and the PR are not linked, you can do it manually in the right panel of the Pull Request details page.  
- **2.5. Peer Review**: One or more core contributors will review your PR. They may suggest changes or improvements.
- **2.6. Approval and Merge**: After approval from the reviewers, you can merge your PR with a squash and merge type of action.

## Commit Standards and Versioning

This project uses [Conventional Commits](https://www.conventionalcommits.org/) and automated semantic versioning. **You do not need to manually update version numbers** - they are automatically handled based on your commit messages.

### Standard Commit Message Format

All commit messages must follow the conventional commit format:

```text
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

#### Commit Types

- **feat**: A new feature (triggers a **minor** version bump, e.g., 1.0.0 → 1.1.0)
- **fix**: A bug fix (triggers a **patch** version bump, e.g., 1.0.0 → 1.0.1)
- **perf**: A code change that improves performance (triggers a **patch** version bump)
- **build**: Changes to build system or external dependencies
- **chore**: Other changes that don't modify src or test files
- **ci**: Changes to CI/CD configuration files and scripts
- **docs**: Documentation only changes
- **style**: Changes that don't affect code meaning (white-space, formatting, etc.)
- **refactor**: A code change that neither fixes a bug nor adds a feature
- **test**: Adding missing tests or correcting existing tests
- **revert**: Reverts a previous commit (no version bump)

#### Breaking Changes

To trigger a **major** version bump (e.g., 1.0.0 → 2.0.0), include `BREAKING CHANGE:` in the commit footer or add `!` after the type:

```text
feat!: remove deprecated API endpoint

BREAKING CHANGE: The old /api/v1/users endpoint has been removed. Use /api/v2/users instead.
```

#### Examples

```bash
# Minor version bump (new feature)
feat: add user authentication support

# Patch version bump (bug fix)
fix: resolve memory leak in connection pool

# Patch version bump (performance improvement)
perf: optimize database query performance

# No version bump (documentation)
docs: update API documentation

# Major version bump (breaking change)
feat!: redesign user authentication API

BREAKING CHANGE: The authentication flow has been completely redesigned. 
Existing integrations will need to be updated to use the new OAuth2 flow.
```

### Standard PR Titles

PR titles should follow the same conventional commit format as they will be used for the squash merge commit:

- ✅ `feat: add support for custom validators`
- ✅ `fix: resolve connection timeout issues`
- ✅ `docs: update contributing guidelines`
- ❌ `Add new feature`
- ❌ `Bug fixes`
- ❌ `Update docs`

### Version Update Cases

The project uses automated semantic versioning based on commit messages:

| Commit Type | Version Impact | Example |
|-------------|---------------|---------|
| `feat:` | **Minor** version bump | 1.0.0 → 1.1.0 |
| `fix:`, `perf:` | **Patch** version bump | 1.0.0 → 1.0.1 |
| `feat!:`, `fix!:`, or `BREAKING CHANGE:` | **Major** version bump | 1.0.0 → 2.0.0 |
| `docs:`, `style:`, `refactor:`, `test:`, `chore:`, `build:`, `ci:` | **No** version bump | Version stays the same |

**Important**: Never manually edit version numbers in `pyproject.toml` or other files. The release automation will handle all version updates automatically when PRs are merged to the main branch.

## Logging Configuration

The GenLayerPY SDK uses a dedicated logger (`"genlayer_py"`) that is disabled by default to prevent unwanted log output when used as a dependency in other projects.

### For SDK Users

#### Enable Logs for Development in Your Application
```python
import logging

# Enable debug logging with console output
logger = logging.getLogger("genlayer_py")
logger.disabled = False
logger.setLevel(logging.DEBUG) # setup the logging level

# Add console handler to see output
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(name)s - %(levelname)s - %(message)s'))
logger.addHandler(console_handler)
```


### For SDK Developers

When developing the SDK, you can enable logging by modifying `genlayer_py/logging.py`:

```python
# For development, change the setup_logger function:
def setup_logger() -> logging.Logger:
    logger = logging.getLogger("genlayer_py")
    
    # Enable logging for development
    logger.setLevel(logging.DEBUG)
    logger.disabled = False
    
    # Add console handler for development
    if not logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter('%(name)s - %(levelname)s - %(message)s')
        )
        logger.addHandler(console_handler)
    
    return logger
```

**Note**: Remember to revert logging changes before submitting PRs to maintain the default silent behavior.

### Improving Documentation

To contribute to our docs, visit our [Documentation Repository](https://github.com/yeagerai/genlayer-docs) to create new issues or contribute to existing issues.

## Community

Connect with the GenLayer community to discuss, collaborate, and share insights:

- **[Discord Channel](https://discord.gg/8Jm4v89VAu)**: Our primary hub for discussions, support, and announcements.
- **[Telegram Group](https://t.me/genlayer)**: For more informal chats and quick updates.

Your continuous feedback drives better product development. Please engage with us regularly to test, discuss, and improve the GenLayerPY SDK.