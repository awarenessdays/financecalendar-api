#!/usr/bin/env python3
"""Generate the public README comparison from the canonical product-offer rows.

Examples:
  python3 scripts/sync-plan-comparison.py --readme /path/to/public/README.md
  python3 scripts/sync-plan-comparison.py --readme /path/to/public/README.md --offer offer.json --check
The optional JSON input may be a product offer or its plan_comparison object.
Without --offer, reads the public current offer; no API key or account is used.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import urllib.request

START = '<!-- fc-plan-comparison:start -->'
END = '<!-- fc-plan-comparison:end -->'
URL = 'https://www.financecalendar.com/wp-json/fc/v1/product-offer'


def comparison_text(comparison: dict) -> str:
    columns = comparison['columns']
    rows = comparison['rows']
    if len(columns) < 2 or not rows:
        raise ValueError('Canonical comparison has fewer than two plans or no rows')
    def markdown(value):
        return str(value).replace('|', '\\|').replace('\n', ' ')
    lines = ['| Feature | ' + ' | '.join(map(markdown, columns.values())) + ' |',
             '|' + ' --- |' * (len(columns) + 1)]
    for row in rows:
        if list(row['values']) != list(columns):
            raise ValueError('Comparison row columns differ from the canonical columns')
        lines.append('| ' + markdown(row['feature']) + ' | ' + ' | '.join(markdown(row['values'][key]) for key in columns) + ' |')
    result = '\n'.join(lines) + '\n'
    for row in rows:
        if row.get('note'):
            result += '\n' + row['feature'] + ': ' + row['note'] + '\n'
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--readme', type=Path, default=Path(__file__).resolve().parents[1] / 'README.md')
    parser.add_argument('--offer', type=Path)
    parser.add_argument('--check', action='store_true', help='Reject drift without rewriting README')
    args = parser.parse_args()
    if args.offer:
        offer = json.loads(args.offer.read_text())
    else:
        request = urllib.request.Request(URL, headers={'User-Agent': 'FinanceCalendar-comparison-sync/1.0', 'Cache-Control': 'no-cache'})
        with urllib.request.urlopen(request, timeout=30) as response:
            offer = json.load(response)
    comparison = offer.get('plan_comparison', offer)
    generated = START + '\n' + comparison_text(comparison).rstrip() + '\n' + END
    body = args.readme.read_text()
    if body.count(START) != 1 or body.count(END) != 1:
        raise ValueError('README must contain exactly one marked comparison region')
    start, end = body.index(START), body.index(END) + len(END)
    if body[start:end] != generated:
        if args.check:
            raise SystemExit('README comparison differs from the canonical product offer; rerun without --check.')
        args.readme.write_text(body[:start] + generated + body[end:])
    print('README comparison matches the canonical product offer.' if args.check else 'README comparison generated from the canonical product offer.')


if __name__ == '__main__':
    main()
