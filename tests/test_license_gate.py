# SPDX-FileCopyrightText: 2026 Coastal Agentics
# SPDX-License-Identifier: Apache-2.0
import pytest

from saltmarsh.data import Asset, LicenseBlockedError, ProvenanceCard, check_license, is_allowed
from saltmarsh.data.lerobot_io import load_lerobot_dataset


@pytest.mark.parametrize(
    "spdx",
    ["Apache-2.0", "MIT", "BSD-3-Clause", "CC0-1.0", "CC-BY-4.0", "CDLA-Permissive-2.0"],
)
def test_allowed(spdx):
    assert check_license(spdx) == spdx


@pytest.mark.parametrize(
    "spdx",
    [
        "CC-BY-NC-4.0",
        "CC-BY-NC-SA-4.0",
        "CC-BY-NC-ND-4.0",
        "CC-BY-ND-4.0",
        "CC-BY-NC-3.0",
        "CC-BY-NC-SA-2.0-FR",
        "CC-BY-ND-2.5",
        "cc-by-nc-4.0",
    ],
)
def test_nc_and_nd_are_refused(spdx):
    with pytest.raises(LicenseBlockedError, match="non-commercial or no-derivatives"):
        check_license(spdx)


@pytest.mark.parametrize(
    "spdx",
    [None, "", "   ", "NOASSERTION", "LicenseRef-custom", "GPL-3.0-only", "CC-BY-SA-4.0"],
)
def test_unknown_or_missing_fails_closed(spdx):
    assert not is_allowed(spdx)


def test_expressions():
    assert is_allowed("MIT OR Apache-2.0")
    assert is_allowed("CC-BY-NC-4.0 OR CC-BY-4.0")  # the permissive option can be chosen
    assert not is_allowed("CC-BY-NC-4.0 OR CC-BY-ND-4.0")
    assert is_allowed("MIT AND CC-BY-4.0")
    assert not is_allowed("MIT AND CC-BY-NC-4.0")  # every part must pass
    assert not is_allowed("MIT AND Apache-2.0 OR CC0-1.0")  # mixed operators
    assert not is_allowed("(MIT OR Apache-2.0)")
    assert not is_allowed("Apache-2.0 WITH LLVM-exception")
    assert not is_allowed("MIT OR")


def test_provenance_card_runs_the_gate():
    card = ProvenanceCard(name="demo", assets=(Asset("clip", "CC-BY-4.0", "own capture"),))
    assert card.to_dict()["assets"][0]["license"] == "CC-BY-4.0"
    with pytest.raises(LicenseBlockedError):
        Asset("lafan1", "CC-BY-NC-ND-4.0")
    with pytest.raises(ValueError):
        ProvenanceCard(name="empty", assets=())


def test_dataset_loader_checks_license_before_importing_lerobot():
    with pytest.raises(LicenseBlockedError):
        load_lerobot_dataset("someone/some-dataset", license="CC-BY-NC-4.0")
