#!/usr/bin/env python3
"""Protect paid/trial contracts while verifying the additive Free Developer scope."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from approved_contract_additions import prior_schema, prior_parameters, prior_response, validate_properties

ROOT = Path(__file__).resolve().parents[1]
FREE_REFS = {
    name: {'$ref': '#/components/schemas/' + name}
    for name in ('FreeDeveloperCalendarResponse', 'FreeDeveloperKeyUsage', 'FreeDeveloperError')
}
FREE_EVENT_FIELDS = {
    'id', 'series_code', 'name', 'country', 'category', 'impact', 'date',
    'release_at_utc', 'time_precision', 'all_day', 'status', 'source_url',
    'source_name', 'url', 'source_license', 'source_rights', 'figures_available', 'result_available',
}


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def retained_schema(schema, path, method, status):
    """Unwrap only the precisely authorized Free alternative for this response."""
    allowed = None
    if method == 'get' and status == '200':
        if path in ('/calendar', '/today'):
            allowed = FREE_REFS['FreeDeveloperCalendarResponse']
        elif path == '/keys/me':
            allowed = FREE_REFS['FreeDeveloperKeyUsage']
    if status == '403' or (status == '429' and path in ('/calendar', '/today')):
        allowed = FREE_REFS['FreeDeveloperError']
    if allowed is not None and isinstance(schema, dict) and set(schema) == {'anyOf'}:
        choices = schema['anyOf']
        if len(choices) == 2 and choices.count(allowed) == 1:
            schema = next(choice for choice in choices if choice != allowed)
    # The serving-only trial presenter now retains its error as a singleton union.
    # This is the same schema; no other wrapper or paid branch is normalized.
    trial_error = {'$ref': '#/components/schemas/TrialAccessError'}
    if path in ('/calendar', '/today', '/week') and method == 'get' and status == '403':
        if schema == {'oneOf': [trial_error]}:
            return trial_error
    return prior_response(path, method, status, schema)


def validate(document, baseline):
    schemas = document['components']['schemas']
    for name, expected in baseline['paid_schema_sha256'].items():
        assert digest(prior_schema(name, schemas[name])) == expected, 'Paid schema changed: ' + name
    for name, expected in baseline['trial_schema_sha256'].items():
        assert digest(schemas[name]) == expected, 'Retained trial schema changed: ' + name
    assert digest(document['security']) == baseline['global_security_sha256'], 'Global authentication changed'
    assert digest(document['components']['securitySchemes']) == baseline['security_schemes_sha256'], 'Authentication mechanisms changed'
    for path, operations in baseline['route_security'].items():
        assert path in document['paths'], 'Existing route removed: ' + path
        for method, expected in operations.items():
            assert document['paths'][path][method].get('security', document['security']) == expected, 'Route security changed: ' + path
    for path, operations in baseline['operation_contracts'].items():
        for method, contract in operations.items():
            operation = document['paths'][path][method]
            for key in ('operationId', 'parameters', 'requestBody'):
                value = prior_parameters(path, method, operation.get(key)) if key == 'parameters' else operation.get(key)
                assert digest(value) == contract[key], 'Existing route input changed: ' + path + ' ' + key
            for status, response_contract in contract['responses'].items():
                assert status in operation['responses'], 'Existing response removed: ' + path + ' ' + status
                response = operation['responses'][status]
                assert digest(response.get('headers')) == response_contract['headers_sha256'], 'Response headers changed: ' + path
                for media, expected in response_contract['content_schemas'].items():
                    assert media in response.get('content', {}), 'Existing media type removed: ' + path + ' ' + media
                    retained = retained_schema(response['content'][media].get('schema'), path, method, status)
                    assert digest(retained) == expected, 'Paid/retained response changed: ' + path + ' ' + status
    free = schemas['FreeDeveloperCalendarResponse']
    assert free['additionalProperties'] is False
    assert free['properties']['events']['maxItems'] == 20
    event = schemas['FreeDeveloperEvent']
    assert event['additionalProperties'] is False
    validate_properties('FreeDeveloperEvent', event)
    validate_properties('FreeDeveloperCalendarResponse', free)
    assert set(event['properties']) == FREE_EVENT_FIELDS, 'Free event allowlist changed'
    assert set(free['properties']) == {'from', 'to', 'count', 'total', 'truncated', 'events', 'generated_at', 'attribution', 'free_developer', 'more_on_paid_plans'}, 'Free response allowlist changed'
    for key, value in [('daily_limit', 10), ('monthly_limit', 100), ('max_events_per_response', 20)]:
        assert schemas['FreeDeveloperUsage']['properties'][key]['const'] == value
    for path in ('/calendar', '/today'):
        operation = document['paths'][path]['get']
        assert operation['x-free-developer']['schema'] == FREE_REFS['FreeDeveloperCalendarResponse']
        assert FREE_REFS['FreeDeveloperCalendarResponse'] in operation['responses']['200']['content']['application/json']['schema']['anyOf']
    assert FREE_REFS['FreeDeveloperKeyUsage'] in document['paths']['/keys/me']['get']['responses']['200']['content']['application/json']['schema']['anyOf']
    assert document['x-product-offer']['evaluation'] == {'available': False, 'retained_participants_honored': True}
    assert document['x-product-offer']['free_developer']['available'] is True
    assert document['info']['license']['name'] == 'Finance Calendar API terms and source attribution'


def main():
    document = json.loads((ROOT / 'openapi.json').read_text())
    baseline = json.loads((ROOT / 'scripts/fixtures/free-developer-compatibility.json').read_text())
    validate(document, baseline)
    mutations = [
        lambda value: value['components']['schemas']['Event'].update(description='unreviewed paid change'),
        lambda value: value.update(security=[]),
        lambda value: value['components']['schemas']['FreeDeveloperEvent']['properties'].update(actual={'type': 'number'}),
        lambda value: value['components']['schemas']['FreeDeveloperEvent']['properties'].update(unreviewed_value={'type': 'number'}),
        lambda value: value['components']['schemas']['FreeDeveloperUsage']['properties']['monthly_limit'].update(const=5000),
        lambda value: value['components']['schemas']['TrialStatus']['properties']['total_limit'].update(const=100),
        lambda value: value['paths']['/calendar']['get']['responses']['200']['content']['application/json'].update(schema=FREE_REFS['FreeDeveloperCalendarResponse']),
        lambda value: value['paths']['/history']['get'].update(parameters=[]),
        lambda value: value['components']['securitySchemes']['ApiKey'].update(name='Public-Key'),
        lambda value: value['components']['schemas']['Event']['properties']['forecasts'].update(type='number'),
        lambda value: value['components']['schemas']['FreeDeveloperEvent']['properties']['figures_available'].update(const=False),
        lambda value: next(parameter for parameter in value['paths']['/changes']['get']['parameters'] if parameter['name'] == 'fields')['schema'].update(type='number'),
    ]
    for mutate in mutations:
        candidate = deepcopy(document)
        mutate(candidate)
        try:
            validate(candidate, baseline)
        except AssertionError:
            continue
        raise AssertionError('Incompatible mutation accepted')
    print(f'Paid/trial schemas, route inputs/responses and authentication preserved; Free closed projection/limits verified; {len(mutations)} incompatible mutations rejected.')


if __name__ == '__main__':
    main()
