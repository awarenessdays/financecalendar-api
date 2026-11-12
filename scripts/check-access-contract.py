#!/usr/bin/env python3
"""Preserve paid access safeguards and check the additive ongoing Free contract."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import re
import runpy

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_PATHS = {'/sample', '/product-offer', '/openapi'}


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def validate(document, baseline):
    for name, expected in baseline['paid_schema_sha256'].items():
        assert digest(document['components']['schemas'][name]) == expected, 'Existing paid schema changed: ' + name
    assert document['security'], 'Production data must require credentials.'
    assert document['info']['license']['name'] == 'Finance Calendar API terms and source attribution'
    for path in PUBLIC_PATHS:
        assert document['paths'][path]['get']['security'] == [], path + ' is a public inspection route.'
    assert 'x-free-api-access' not in document, 'Withdrawn new-trial signup discovery remains.'
    assert document['x-product-offer']['evaluation'] == {'available': False, 'retained_participants_honored': True}
    assert document['x-product-offer']['free_developer']['available'] is True
    assert not re.search(r'account/\?trial=1|optional limited (?:JSON |API )?evaluation', json.dumps(document), re.I), 'Withdrawn new-trial signup offer remains.'


def validate_current_guides():
    paths = [ROOT / 'README.md']
    for folder in ['clients', 'integrations', 'examples', 'widget']:
        paths.extend(p for p in (ROOT / folder).rglob('*') if p.is_file()
                     and p.suffix in {'.md', '.py', '.js'}
                     and not set(p.relative_to(ROOT).parts).intersection({'node_modules', 'test', 'tests', 'fixtures', '__pycache__', 'dist', 'build'}))
    for path in paths:
        assert not re.search(r'account/\?trial=1|optional (?:limited )?(?:API )?evaluation|finite free access', path.read_text(), re.I), str(path.relative_to(ROOT)) + ' advertises withdrawn trial enrollment.'


def main():
    # Keep the earlier paid-only schema baseline immutable; the stricter Free
    # checker additionally protects retained trials and every route contract.
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
        raise AssertionError('An incompatible paid schema, authentication or signup mutation was accepted.')
    runpy.run_path(str(ROOT / 'scripts/check-trial-openapi.py'), run_name='__main__')
    print('Earlier paid safeguards preserved; current guides contain no withdrawn new-trial signup offer; three additional incompatible mutations rejected.')


if __name__ == '__main__':
    main()
