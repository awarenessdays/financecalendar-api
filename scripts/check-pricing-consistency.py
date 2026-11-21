#!/usr/bin/env python3
"""Verify access docs and require live Starter quotes on commercial surfaces."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import re
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OFFER_URL = 'https://www.financecalendar.com/wp-json/fc/v1/product-offer'
STARTER_URL = 'https://www.financecalendar.com/pricing/#starter'
PLAN_LIMITS = {'starter': (250, 5000), 'build': (100000, None), 'scale': (1000000, None)}
STABLE_PRICES = {'build': {'month': 999, 'year': 9590}, 'scale': {'month': 2900, 'year': 27840}}
CLIENT_SPECS = (
    'clients/node/test/fixtures/openapi.json',
    'clients/python/tests/fixtures/openapi.json',
)
STALE_COPY = re.compile(
    r'US\$4\.99/month|US\$53\.89/year|US\$(?:9|19)\.99/year|'
    r'Starter\s*(?:is\s+|costs\s+|from\s+|at\s+)?(?:\*\*)?(?:US)?\$\d+\.\d{2}|'
    r'(?<![0-9,])1,000(?: API)? requests (?:per day|per UTC day)|'
    r'(?<![0-9])25,000 (?:requests )?per (?:UTC )?calendar month|'
    r'2,000 keyless|free with attribution|finite free access is a bounded sample|finite JSON calendar scope',
    re.I,
)


def validate_offer(offer, *, live=False):
    assert offer['version'] == 2
    assert offer['production_api']['api_key_required'] is True
    assert offer['production_api']['access_scopes']['numerical_data_and_tools']['paid_plan_required'] is True
    free = offer['free_developer']
    assert free['available'] is True and free['daily_limit'] == 10 and free['monthly_limit'] == 100
    assert free['max_records_per_response'] == 20 and free['active_key_limit'] == 1
    assert free['allowed_routes'] == ['/fc/v1/calendar', '/fc/v1/today']
    assert free['ongoing'] is True and free['card_required'] is False and free['automatic_charge'] is False
    assert free['api_key_required'] is True and free['review_required'] is True and free['review_hours'] == 168
    assert offer['evaluation'] == {'available': False, 'retained_participants_honored': True}
    assert offer['sample']['max_records'] == 3 and offer['sample']['filtering'] is False and offer['sample']['pagination'] is False
    for key, (daily, monthly) in PLAN_LIMITS.items():
        plan = offer['plans'][key]
        assert plan['daily_limit'] == daily and plan['monthly_limit'] == monthly, key + ' quota drift'
    for key, expected in STABLE_PRICES.items():
        prices = offer['plans'][key]['prices']
        assert set(prices) == set(expected), key + ' billing interval drift'
        for interval, amount in expected.items():
            row = prices[interval]
            assert row['unit_amount'] == amount and row['currency'] == 'usd' and row['interval'] == interval, key + ' price drift'
    starter_prices = offer['plans']['starter']['prices']
    if live:
        assert set(starter_prices) == {'month', 'year'}, 'Live Starter must offer monthly and annual billing.'
        for interval, quote in starter_prices.items():
            assert quote['currency'] == 'usd' and quote['interval'] == interval
            assert type(quote['unit_amount']) is int and quote['unit_amount'] > 0
    else:
        assert starter_prices == {}, 'Repository snapshots must direct readers to the live Starter charge.'


def validate_snapshot(document):
    offer = document['x-product-offer']
    validate_offer(offer)
    assert document['x-product-offer-url'] == OFFER_URL
    assert OFFER_URL in document['info']['description'], 'OpenAPI readers need a live Starter quote link.'
    assert document['security'], 'Data routes must keep required credentials.'
    for path in ('/sample', '/product-offer', '/openapi'):
        assert document['paths'][path]['get']['security'] == [], path + ' must describe public inspection access'
    for key, (daily, monthly) in PLAN_LIMITS.items():
        quota = document['x-rate-limits'][key]
        assert quota['per_day'] == daily and quota['per_calendar_month'] == monthly, key + ' OpenAPI quota drift'
    assert not STALE_COPY.search(json.dumps(document, ensure_ascii=False)), 'OpenAPI contains a stale or pinned Starter quote.'


def validate_guides():
    guides = ('README.md', 'clients/node/README.md', 'clients/python/README.md')
    for name in guides:
        body = (ROOT / name).read_text()
        assert STARTER_URL in body and OFFER_URL in body, name + ' is missing a live Starter quote link.'
    paths = [ROOT / 'README.md']
    for folder in ('clients', 'integrations', 'examples', 'widget', 'docs', '.claude-plugin', '.agents'):
        paths.extend(p for p in (ROOT / folder).rglob('*') if p.is_file()
                     and p.suffix in {'.md', '.py', '.js', '.mjs', '.toml', '.json'}
                     and not set(p.relative_to(ROOT).parts).intersection(
                         {'node_modules', 'test', 'tests', 'fixtures', 'dist', 'build', '__pycache__', '.venv'}))
    for path in paths:
        assert not STALE_COPY.search(path.read_text()), str(path.relative_to(ROOT)) + ' has obsolete commercial copy'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live-offer', action='store_true')
    args = parser.parse_args()
    document = json.loads((ROOT / 'openapi.json').read_text())
    validate_snapshot(document)
    for path in CLIENT_SPECS:
        validate_snapshot(json.loads((ROOT / path).read_text())['body'])
    validate_guides()

    if args.live_offer:
        request = urllib.request.Request(OFFER_URL, headers={'User-Agent': 'FinanceCalendar-consistency-check/1.0', 'Cache-Control': 'no-cache'})
        with urllib.request.urlopen(request, timeout=30) as response:
            live = json.load(response)
        validate_offer(live, live=True)

    for mutate in (
        lambda x: x['plans']['starter'].update(daily_limit=1000),
        lambda x: x['plans']['starter']['prices'].update(year={'unit_amount': 999, 'currency': 'usd', 'interval': 'year'}),
        lambda x: x['free_developer'].update(monthly_limit=5000),
        lambda x: x['free_developer'].update(api_key_required=False),
    ):
        candidate = deepcopy(document['x-product-offer'])
        mutate(candidate)
        try:
            validate_offer(candidate)
        except AssertionError:
            continue
        raise AssertionError('An inaccurate access or pinned price mutation was accepted.')
    print('Pricing and access checks passed. Starter quotes link to the live offer.')


if __name__ == '__main__':
    main()
