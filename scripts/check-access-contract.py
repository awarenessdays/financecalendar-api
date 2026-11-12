#!/usr/bin/env python3
"""Protect paid response schemas and keep current access guidance consistent."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PAID_USAGE_REF = {'$ref': '#/components/schemas/KeyUsage'}
PUBLIC_PATHS = {'/sample', '/product-offer', '/openapi'}


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def validate(document, baseline):
    schemas = document['components']['schemas']
    for name, expected in baseline['paid_schema_sha256'].items():
        assert digest(schemas[name]) == expected, 'Existing paid schema changed: ' + name
    assert document['security'], 'Production data must require credentials.'
    assert document['info']['license']['name'] == 'Finance Calendar API terms and source attribution', 'Current access must not promise unrestricted free data.'
    for path in PUBLIC_PATHS:
        assert document['paths'][path]['get']['security'] == [], path + ' is a public inspection route.'
    for path in ['/calendar', '/today', '/week', '/next', '/series', '/history', '/status']:
        operation = document['paths'][path]['get']
        assert operation.get('security', document['security']), 'Paid data authentication removed: ' + path
    assert 'x-free-api-access' not in document, 'Withdrawn signup discovery remains.'
    assert 'evaluation' not in document['x-product-offer'], 'Withdrawn offer remains.'
    encoded = json.dumps(document)
    assert not re.search(r'account/\?trial=1|optional limited (?:JSON |API )?evaluation', encoded, re.I), 'Withdrawn signup offer remains.'
    usage = document['paths']['/keys/me']['get']['responses']['200']['content']['application/json']['schema']
    assert usage == PAID_USAGE_REF, 'Paid KeyUsage response must retain its documented shape.'


def validate_current_guides():
    paths = [ROOT / 'README.md']
    for folder in ['clients', 'integrations', 'examples', 'widget']:
        paths.extend(p for p in (ROOT / folder).rglob('*') if p.is_file()
                     and p.suffix in {'.md', '.py', '.js'}
                     and not set(p.relative_to(ROOT).parts).intersection({'node_modules', 'test', 'tests', 'fixtures', '__pycache__', 'dist', 'build'}))
    for path in paths:
        assert not re.search(r'account/\?trial=1|optional (?:limited )?(?:API )?evaluation|finite (?:free access|evaluation)|evaluation key|first free request', path.read_text(), re.I), str(path.relative_to(ROOT)) + ' advertises withdrawn access.'


def main():
    document = json.loads((ROOT / 'openapi.json').read_text())
    baseline = json.loads((ROOT / 'scripts/fixtures/paid-openapi-compatibility.json').read_text())
    validate(document, baseline)
    validate_current_guides()
    for mutate in [
        lambda value: value['components']['schemas']['Event'].update({'description': 'unreviewed paid event change'}),
        lambda value: value.update({'security': []}),
        lambda value: value.update({'x-free-api-access': {'signup_url': 'withdrawn'}}),
    ]:
        candidate = deepcopy(document)
        mutate(candidate)
        try:
            validate(candidate, baseline)
        except AssertionError:
            continue
        raise AssertionError('An incompatible schema, authentication or signup mutation was accepted.')
    print('Paid schemas and authentication preserved; current guides contain no withdrawn signup offer; three incompatible mutations rejected.')


if __name__ == '__main__':
    main()
