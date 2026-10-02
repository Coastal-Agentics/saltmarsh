# SPDX-FileCopyrightText: 2026 Coastal Agentics
# SPDX-License-Identifier: Apache-2.0
"""Provenance cards: where each asset came from and under which license.

Every asset records an SPDX license, and building a card runs the license gate
on each one, so a card that holds a refused asset cannot be created.
"""

from dataclasses import dataclass, field

from saltmarsh.data.license_gate import check_license


@dataclass(frozen=True)
class Asset:
    """One input or output: a dataset, motion clip, model or robot model."""

    name: str
    license: str
    source: str = ""

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("asset name is required")
        object.__setattr__(self, "license", check_license(self.license))


@dataclass(frozen=True)
class ProvenanceCard:
    """A minimal provenance card. Fields will grow; the license rule will not."""

    name: str
    assets: tuple[Asset, ...]
    notes: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("card name is required")
        if not self.assets:
            raise ValueError("a provenance card needs at least one asset")
        for asset in self.assets:
            if not isinstance(asset, Asset):
                raise TypeError(f"expected Asset, got {type(asset).__name__}")

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "assets": [
                {"name": a.name, "license": a.license, "source": a.source} for a in self.assets
            ],
            "notes": dict(self.notes),
        }
