# Logging

The SDK logs to the `genlayer_py` logger, created in `genlayer_py/logging.py` and disabled by default, so a dependency
never prints into its host application

## Enabling It

From the application or a test, without touching the SDK:

```python
import logging

logger = logging.getLogger("genlayer_py")
logger.disabled = False
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(name)s - %(levelname)s - %(message)s"))
logger.addHandler(handler)
```

`uv run pytest -o log_cli=true --log-cli-level=DEBUG` shows the same output while testing, once the logger is enabled

## Adding Log Calls

1. Get the logger with `from genlayer_py.logging import logger`, never `logging.getLogger(__name__)`
2. Never log private keys or signed raw transactions
3. Do not commit a change to the default level or `disabled` flag in `genlayer_py/logging.py`
