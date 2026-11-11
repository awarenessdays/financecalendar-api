#!/usr/bin/env python3
"""Verify the finite-trial OpenAPI addition preserves the reviewed paid contract.

The fixture records semantic hashes of the public spec immediately before the
additive trial response branch. Only the explicitly documented extension points
are removed for comparison; every other contract field remains hash-protected.
No network access or third-party dependencies are required.
"""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRIAL_SCHEMAS = {'TrialStatus', 'TrialKeyUsage', 'TrialAccessError'}
DATA_ROUTES = ('/calendar', '/today', '/week')
TRIAL_REF = {'$ref': '#/components/schemas/TrialStatus'}
PAID_USAGE_REF = {'$ref': '#/components/schemas/KeyUsage'}
TRIAL_USAGE_REF = {'$ref': '#/components/schemas/TrialKeyUsage'}


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def without_trial_addition(document):
    """Remove only reviewed additive branches and their scoped explanations."""
    result = deepcopy(document)
    for name in TRIAL_SCHEMAS:
        result['components']['schemas'].pop(name, None)
    for path in DATA_ROUTES:
        operation = result['paths'][path]['get']
        operation['responses']['200']['content']['application/json']['schema']['properties'].pop('trial', None)
        # Previously these 403 responses were absent or had descriptions only.
        forbidden = operation['responses'].get('403')
        if forbidden is not None:
            forbidden.pop('content', None)
            forbidden.pop('description', None)
            if not forbidden:
                operation['responses'].pop('403')
    for path, method in [(path, 'get') for path in DATA_ROUTES] + [('/keys/me', 'get'), ('/keys', 'post')]:
        result['paths'][path][method].pop('description', None)
    usage = result['paths']['/keys/me']['get']['responses']['200']
    usage['content']['application/json']['schema'] = deepcopy(PAID_USAGE_REF)
    usage.pop('description', None)
    for path in result['paths'].values():
        for operation in path.values():
            if isinstance(operation, dict):
                operation.get('responses', {}).get('402', {}).pop('description', None)
    result.pop('x-free-api-access', None)
    return result


def validate(document, baseline):
    schemas = document['components']['schemas']
    check(set(schemas) == set(baseline['paid_schema_sha256']) | TRIAL_SCHEMAS, 'Only the three reviewed trial schemas may be added.')
    for name, expected in baseline['paid_schema_sha256'].items():
        check(digest(schemas[name]) == expected, 'Existing paid schema changed: ' + name)
    check(digest(schemas['KeyUsage']) == baseline['paid_schema_sha256']['KeyUsage'], 'Paid KeyUsage must remain unchanged.')
    check(digest(schemas['Event']) == baseline['paid_schema_sha256']['Event'], 'Paid Event must remain unchanged.')
    check(digest(without_trial_addition(document)) == baseline['contract_without_trial_sha256'], 'A path, security rule or contract field outside the additive trial branch changed.')

    status = schemas['TrialStatus']
    check(set(status['required']) >= {'state', 'total_limit', 'used', 'remaining', 'duration_seconds', 'started_at', 'expires_at', 'upgrade_url'}, 'Trial status must expose its budget and lifecycle.')
    for field, value in [('total_limit', 25), ('duration_seconds', 172800), ('event_limit', 10)]:
        check(status['properties'][field]['const'] == value, 'Incorrect trial limit: ' + field)
    for field in ['started_at', 'expires_at']:
        check(set(status['properties'][field]['type']) == {'string', 'null'} and status['properties'][field]['format'] == 'date-time', 'Trial clocks must be nullable before first use.')
    check(schemas['TrialKeyUsage']['required'] == ['trial'] and schemas['TrialKeyUsage']['properties']['trial'] == TRIAL_REF, 'Trial usage must document its distinct trial envelope.')
    check(set(schemas['TrialAccessError']['required']) == {'code', 'error'} and schemas['TrialAccessError']['properties']['trial'] == TRIAL_REF, 'Trial errors must retain their explicit error and optional trial status.')

    for path in DATA_ROUTES:
        operation = document['paths'][path]['get']
        schema = operation['responses']['200']['content']['application/json']['schema']
        check(schema['properties']['trial'] == TRIAL_REF and 'trial' not in schema.get('required', []), 'Trial metadata is optional for paid data responses: ' + path)
        check(operation['responses']['403']['content']['application/json']['schema'] == {'$ref': '#/components/schemas/TrialAccessError'}, 'Trial access failures need the documented error branch: ' + path)
    usage = document['paths']['/keys/me']['get']['responses']['200']['content']['application/json']['schema']
    check(usage == {'oneOf': [PAID_USAGE_REF, TRIAL_USAGE_REF]}, 'Usage must support the unchanged paid shape or the distinct trial shape.')
    access = document['x-free-api-access']
    check(access['total_requests'] == 25 and access['duration_seconds'] == 172800 and access['max_events_per_response'] == 10, 'Discovery metadata must match the trial response contract.')
    check(access['api_key_required'] is True and access['verified_email_required'] is True and access['card_required'] is False and access['automatic_charge'] is False, 'Trial access and billing facts are inconsistent.')
    check(document['info']['license']['name'] == 'Finance Calendar API terms and source attribution', 'The API label must not promise unrestricted free data.')


def main():
    document = json.loads((ROOT / 'openapi.json').read_text())
    baseline = json.loads((ROOT / 'scripts/fixtures/trial-openapi-compatibility.json').read_text())
    validate(document, baseline)
    # Prove the compatibility check detects changes outside the new branch.
    mutations = [
        lambda value: value['components']['schemas']['Event'].update({'description': 'unreviewed paid event change'}),
        lambda value: value.update({'security': []}),
        lambda value: value['paths']['/keys/me']['get']['responses']['200']['content']['application/json'].update({'schema': {'$ref': '#/components/schemas/TrialKeyUsage'}}),
    ]
    for mutate in mutations:
        candidate = deepcopy(document)
        mutate(candidate)
        try:
            validate(candidate, baseline)
        except AssertionError:
            continue
        raise AssertionError('The compatibility check accepted an unreviewed contract mutation.')
    print('Trial OpenAPI addition verified: existing paid schemas, paths and security preserved; three incompatible mutations rejected.')


if __name__ == '__main__':
    main()
