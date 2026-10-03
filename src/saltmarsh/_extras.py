# SPDX-FileCopyrightText: 2026 Nye Warburton
# SPDX-License-Identifier: Apache-2.0
"""Helpers for optional dependencies."""

import importlib
from types import ModuleType


class MissingExtraError(ImportError):
    """Raised when a feature needs an optional extra that is missing or does not load."""


def require(module: str, extra: str) -> ModuleType:
    """Import `module`, or raise MissingExtraError naming the extra to install."""
    try:
        return importlib.import_module(module)
    except ModuleNotFoundError as exc:
        if exc.name is None or not (module == exc.name or module.startswith(exc.name + ".")):
            raise _broken(module, extra, exc) from exc
        raise MissingExtraError(
            f'{module!r} is not installed. Install it with: pip install "saltmarsh[{extra}]"'
        ) from exc
    except ImportError as exc:
        # Installed, but it failed to load (for example a missing system library).
        raise _broken(module, extra, exc) from exc


def _broken(module: str, extra: str, exc: ImportError) -> MissingExtraError:
    return MissingExtraError(
        f"{module!r} is installed but failed to import ({exc}). Reinstall with "
        f'pip install "saltmarsh[{extra}]"; some packages also need system libraries.'
    )
