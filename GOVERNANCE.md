# Governance

Saltmarsh is a company-led open-source project. Coastal Agentics started it and maintains it.

## Roles

- **Lead maintainer:** Coastal Agentics. It sets direction, reviews and merges changes, and makes releases.
- **Final decision:** the project lead at Coastal Agentics ([@NyeGuy](https://github.com/NyeGuy)) makes the final call when consensus is not reached. This applies until the project has outside maintainers.
- **Contributors:** anyone who opens an issue or pull request.

## How decisions are made

- Most decisions use lazy consensus. A proposal is made in an issue or pull request, and it goes ahead if no maintainer objects within a reasonable time.
- Significant decisions are recorded as ADRs in `docs/adr/`. These include packaging, dependencies, licensing and the safety contract.
- Any maintainer can block a change that weakens a safety check in `eval` or the license gate in `data`. Such a change needs an ADR.

## Contributions

- All contributions are under Apache-2.0. Each commit must carry a Developer Certificate of Origin sign-off (`git commit -s`), which adds a `Signed-off-by:` line. There is no CLA.
- New files must carry SPDX license information so that `reuse lint` passes.

## Name

The "Saltmarsh" name is used by Coastal Agentics for this project. Apache-2.0 does not grant rights to use the name (section 6 of the license).

## Changes to this document

This document will change once people outside Coastal Agentics maintain parts of the project. At that point, a neutral foundation home will be considered. Changes to governance are made by pull request and recorded in an ADR.
