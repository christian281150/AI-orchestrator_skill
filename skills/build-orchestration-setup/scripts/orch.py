#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Entry point: python tools/orch.py <command>. Standard library only, Python 3.11+."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from orchestrator.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
