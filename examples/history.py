#!/usr/bin/env python3
"""Export a complete, revision-consistent historical metric with a SHA-256 manifest."""
import argparse
import hashlib
import json
from pathlib import Path

from financecalendar import Client


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metric", default="gb-cpi-all-items-yoy")
    parser.add_argument("--from", dest="from_", help="Optional reference-period start within your plan window; omit for authorized history")
    parser.add_argument("--output", type=Path, default=Path("history-export.json"))
    args = parser.parse_args()
    with Client() as fc:
        # Buffer before writing: a cursor/revision error cannot leave an export
        # that looks complete. Values remain decimal strings, without floats.
        rows = list(fc.iter_archive(kind="observations", metric_id=args.metric,
                                    from_=args.from_, limit=100))
    encoded = (json.dumps(rows, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode()
    args.output.write_bytes(encoded)
    manifest = {"metric_id": args.metric, "from": args.from_, "records": len(rows),
                "sha256": hashlib.sha256(encoded).hexdigest(),
                "first_period": rows[0]["reference_period"] if rows else None,
                "last_period": rows[-1]["reference_period"] if rows else None,
                "source": "Finance Calendar historical observations",
                "historical_first_print_claimed": False}
    args.output.with_suffix(args.output.suffix + ".manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
