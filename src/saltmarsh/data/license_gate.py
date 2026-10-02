# SPDX-FileCopyrightText: 2026 Coastal Agentics
# SPDX-License-Identifier: Apache-2.0
"""License gate for datasets, motion clips, models and other assets.

The gate fails closed. An asset passes only if its SPDX license expression is
built from licenses on the allowlist. Non-commercial (NC) and no-derivatives
(ND) licenses are always refused, for example CC-BY-NC-4.0, CC-BY-NC-SA-4.0,
CC-BY-ND-4.0 and CC-BY-NC-ND-4.0. Anything unknown, empty or unparseable
(NOASSERTION, LicenseRef-*, WITH exceptions, parentheses) is also refused.

Supported expressions: a single SPDX id, or ids joined by `AND` (every
license must pass) or by `OR` (at least one must pass). Mixing `AND` and
`OR` is refused.
"""

import re

#: Licenses an asset may carry. Saltmarsh publishes code and models under
#: Apache-2.0 and datasets under CC-BY-4.0; the rest are permissive inputs.
ALLOWED_LICENSES = frozenset(
    {
        "Apache-2.0",
        "MIT",
        "BSD-2-Clause",
        "BSD-3-Clause",
        "CC0-1.0",
        "CC-BY-4.0",
        "CDLA-Permissive-2.0",
    }
)

# NC or ND as a hyphen-separated component of the id, e.g. CC-BY-NC-SA-4.0.
_NC_ND = re.compile(r"(^|-)(NC|ND)(-|$)", re.IGNORECASE)
_SPDX_ID = re.compile(r"^[A-Za-z0-9.+-]+$")


class LicenseBlockedError(ValueError):
    """Raised when an asset's license is not allowed."""


def _check_id(license_id: str) -> None:
    if not _SPDX_ID.match(license_id):
        raise LicenseBlockedError(f"{license_id!r} is not a valid SPDX license id")
    if _NC_ND.search(license_id):
        raise LicenseBlockedError(
            f"{license_id} is a non-commercial or no-derivatives license and is refused"
        )
    if license_id not in ALLOWED_LICENSES:
        raise LicenseBlockedError(f"{license_id} is not on the allowlist")


def check_license(expression: str | None) -> str:
    """Return the normalized expression if it passes; raise LicenseBlockedError if not."""
    if not isinstance(expression, str) or not expression.strip():
        raise LicenseBlockedError("no license recorded; an SPDX license is required")
    tokens = expression.split()
    if any(t in ("(", ")") or "(" in t or ")" in t for t in tokens) or "WITH" in tokens:
        raise LicenseBlockedError(f"unsupported license expression: {expression!r}")
    operators = set(tokens[1::2])
    ids = tokens[0::2]
    if len(tokens) % 2 == 0 or not operators <= {"AND", "OR"} or len(operators) > 1:
        raise LicenseBlockedError(f"unsupported license expression: {expression!r}")
    if operators == {"OR"}:
        errors = []
        for license_id in ids:
            try:
                _check_id(license_id)
                break
            except LicenseBlockedError as exc:
                errors.append(str(exc))
        else:
            raise LicenseBlockedError("; ".join(errors))
    else:
        for license_id in ids:
            _check_id(license_id)
    return " ".join(tokens)


def is_allowed(expression: str | None) -> bool:
    """True if `expression` passes the gate."""
    try:
        check_license(expression)
    except LicenseBlockedError:
        return False
    return True
