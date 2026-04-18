#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Deprecated — shim that delegates to `hooks/modes.py`.

Kept for one release so any cached plugin config that still references
this path keeps working. `hooks/hooks.json` now points at `modes.py`
directly. Remove this file once you're sure no installer snapshot still
references it.
"""

from __future__ import annotations

import runpy
from pathlib import Path


def main() -> None:
    runpy.run_path(str(Path(__file__).with_name("modes.py")), run_name="__main__")


if __name__ == "__main__":
    main()
