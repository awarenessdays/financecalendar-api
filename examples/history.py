#!/usr/bin/env python3
"""Complete revision-pinned archive export; commit only after traversal succeeds."""
import argparse
import hashlib
import json
from pathlib import Path

from financecalendar import Client


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", choices=("observations", "releases", "editions", "forecasts", "vintage-coverage"), default="observations")
    parser.add_argument("--metric", help="Exact metric discovered through the matching coverage endpoint")
    parser.add_argument("--from", dest="from_", help="Optional route-specific date within the plan window; omit for authorized default")
    parser.add_argument("--available-before", help="V2 only: exact source-availability cutoff in UTC; unknown clocks excluded")
    parser.add_argument("--output", type=Path, default=Path("history-export.json"))
    args = parser.parse_args()
    if args.kind == "vintage-coverage" and (args.from_ or args.available_before):
        parser.error("Coverage has no date/cutoff filters")
    if args.available_before and args.kind not in {"editions", "forecasts"}:
        parser.error("available-before requires editions or forecasts")
    defaults = {"observations": "gb-cpi-all-items-yoy", "releases": "gb-cpi-all-items-yoy",
                "editions": "us-gdp-real-qoq-saar", "forecasts": "eu-spf-hicp-annual-mean-p12m"}
    metric = args.metric or defaults.get(args.kind)
    params = {"metric_id": metric, "limit": 100}
    if args.from_: params["from_"] = args.from_
    if args.available_before: params["available_before"] = args.available_before
    with Client() as fc:
        rows = list(fc.iter_vintage_coverage(**params) if args.kind == "vintage-coverage"
                    else fc.iter_archive(kind=args.kind, **params))
    # No file is emitted until every page and revision check succeeds. Source
    # credit, target/issue distinction and exact decimal strings remain intact.
    encoded = (json.dumps(rows, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode()
    args.output.write_bytes(encoded)
    manifest = {"kind": args.kind, "metric_id": metric, "from": args.from_,
                "records": len(rows), "sha256": hashlib.sha256(encoded).hexdigest(),
                "verified_initial_records": sum(r.get("historical_first_print") is True for r in rows),
                "exact_availability_records": sum(r.get("available_at") is not None for r in rows)}
    args.output.with_suffix(args.output.suffix + ".manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
