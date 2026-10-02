# SPDX-FileCopyrightText: 2026 Coastal Agentics
# SPDX-License-Identifier: Apache-2.0
"""Helpers for optional dependencies."""

import importlib
from types import ModuleType


class MissingExtraError(ImportError):
    """Raised when a feature needs an optional extra that is not installed."""


def require(module: str, extra: str) -> ModuleType:
    """Import `module`, or raise MissingExtraError naming the extra to install."""
    try:
        return importlib.import_module(module)
    except ImportError as exc:
        raise MissingExtraError(
            f'{module!r} is not installed. Install it with: pip install "saltmarsh[{extra}]"'
        ) from exc
