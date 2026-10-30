#!/usr/bin/env python3
"""S-03 selftest: verify topic-layers.json against topics-snapshot.json.

Checks (spec: docs/specs/shared/S-03-reference-architecture-layers.md, YED-126):
  1. every topic id in the snapshot is mapped, and the map holds no extras
  2. every layer id (and secondary) is one of the ten layers defined in
     reference-architecture.md
  3. every duplicate_of points at a real topic id (not itself)
It also prints per-layer counts. This is an offline check only — it never
touches the Supabase topic table; applying layers via spine_client is a
separate, human-approved step.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

EXPECTED_LAYERS = [
    "model", "environment", "harness", "factory", "data-retrieval",
    "evals-observability", "identity-governance", "gtm-distribution",
    "domain-applications", "market-context",
]

REFS = Path(__file__).resolve().parents[1] / "references"


def load_layer_ids(path: Path) -> list[str]:
    """Layer ids are the ### headings of reference-architecture.md."""
    text = path.read_text()
    return re.findall(r"^### ([a-z][a-z-]*)$", text, re.M)


def run_checks(snapshot_path: Path, map_path: Path, arch_path: Path):
    errors: list[str] = []
    snapshot = json.loads(snapshot_path.read_text())
    topic_map = json.loads(map_path.read_text())

    snapshot_ids = [t["id"] for t in snapshot["topics"]]
    snapshot_set = set(snapshot_ids)
    if len(snapshot_set) != len(snapshot_ids):
        errors.append("snapshot contains duplicate topic ids")

    # 1. coverage: every snapshot id mapped, no extras
    unmapped = [tid for tid in snapshot_ids if tid not in topic_map]
    if unmapped:
        errors.append(f"{len(unmapped)} snapshot id(s) not mapped, e.g. {unmapped[:3]}")
    extras = sorted(set(topic_map) - snapshot_set)
    if extras:
        errors.append(f"{len(extras)} map id(s) not in snapshot, e.g. {extras[:3]}")

    # 2. layer ids valid — the md must define exactly the expected set
    arch_ids = load_layer_ids(arch_path)
    if sorted(arch_ids) != sorted(EXPECTED_LAYERS):
        errors.append(f"reference-architecture.md defines {sorted(arch_ids)}, expected {sorted(EXPECTED_LAYERS)}")
    valid = set(arch_ids)
    for tid, entry in topic_map.items():
        if entry.get("layer") not in valid:
            errors.append(f"{tid}: invalid layer {entry.get('layer')!r}")
        secondary = entry.get("secondary")
        if secondary is not None and secondary not in valid:
            errors.append(f"{tid}: invalid secondary {secondary!r}")

    # 3. duplicate_of points at a real topic id, never itself
    for tid, entry in topic_map.items():
        dup = entry.get("duplicate_of")
        if dup is not None and dup not in snapshot_set:
            errors.append(f"{tid}: duplicate_of {dup!r} is not a real topic id")
        if dup == tid:
            errors.append(f"{tid}: duplicate_of points at itself")

    counts = Counter(e["layer"] for e in topic_map.values())
    return errors, counts, len(snapshot_ids)


def main() -> int:
    if "--selftest" not in sys.argv:
        print(__doc__.strip())
        print("\nrun with --selftest to verify")
        return 0

    errors, counts, total = run_checks(
        REFS / "topics-snapshot.json", REFS / "topic-layers.json",
        REFS / "reference-architecture.md",
    )

    print(f"topics in snapshot: {total}")
    print(f"entries in topic-layers.json: {sum(counts.values())}")
    print("per-layer counts (primary):")
    for layer in EXPECTED_LAYERS:
        print(f"  {layer:22s} {counts.get(layer, 0)}")

    if errors:
        print(f"\nFAIL: {len(errors)} error(s)")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"\nPASS: every snapshot id is mapped, all layer ids valid, "
          f"all duplicate_of targets real ({len(EXPECTED_LAYERS)}/{len(EXPECTED_LAYERS)} checks ok)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
