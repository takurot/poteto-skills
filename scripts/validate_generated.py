#!/usr/bin/env python3
"""Validate generated poteto-skills checksums, host inventories, and the Codex marketplace."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from build_skills import DEFAULT_MARKETPLACE, DEFAULT_OUTPUT, verify_generated_output
from codex_plugins import marketplace_document


def verify_marketplace(output: Path, catalog: Path) -> None:
    try:
        recorded = json.loads(catalog.read_text(encoding="utf-8"))
        manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read the marketplace catalog {catalog}: {error}") from error
    if recorded != marketplace_document(manifest["codex_plugins"]):
        raise ValueError(f"{catalog}: marketplace catalog does not match {output}/manifest.json")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", nargs="?", type=Path, default=Path("skills"))
    parser.add_argument(
        "--marketplace",
        type=Path,
        help="Codex marketplace catalog to check "
        "(default: .agents/plugins/marketplace.json for the repository skills directory)",
    )
    args = parser.parse_args()
    output = args.output.resolve()
    catalog = args.marketplace
    if catalog is None and output == DEFAULT_OUTPUT.resolve():
        catalog = DEFAULT_MARKETPLACE
    try:
        verify_generated_output(output)
        if catalog is not None:
            verify_marketplace(output, catalog)
    except ValueError as error:
        parser.error(str(error))
    print(f"Validated Claude Code and Codex outputs in {args.output}")
    if catalog is not None:
        print(f"Validated the Codex marketplace catalog {catalog}")


if __name__ == "__main__":
    main()
