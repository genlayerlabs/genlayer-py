# Setup

## Prerequisites

1. Python 3.12 or newer
2. [uv](https://docs.astral.sh/uv/)

## Dev Environment

```bash
git clone https://github.com/genlayerlabs/genlayer-py.git
cd genlayer-py
uv sync --group dev
```

`uv sync` creates `.venv/` from `uv.lock`; run tools through `uv run`. After changing dependencies in `pyproject.toml`,
run `uv lock` and commit `uv.lock`: CI runs `uv lock --check`

## Building

`uv build` writes the sdist and wheel to `dist/`, as `publish.yml` does

## Using a Local Checkout From Another Project

```bash
pip install -e path/to/genlayer-py --config-settings editable_mode=strict
```

An editable install picks up source changes without reinstalling; reinstall only after changing project metadata. In a
uv project use `uv add --editable path/to/genlayer-py` instead
