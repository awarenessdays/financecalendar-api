"""Retain exact earlier contracts after the reviewed forecast/marker additions."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

ADDITIONS = json.loads((Path(__file__).with_name('fixtures') / 'forecast-marker-additions.json').read_text())


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def validate_properties(name, schema):
    for field, expected in ADDITIONS['schema_properties'].get(name, {}).items():
        assert digest(schema.get('properties', {}).get(field)) == expected, 'Reviewed additive field changed: ' + name + '.' + field


def prior_schema(name, schema):
    """Remove exact approved additions and explanation text before earlier hashes."""
    validate_properties(name, schema)
    value = deepcopy(schema)
    for field in ADDITIONS['schema_properties'].get(name, {}):
        value['properties'].pop(field)
    for field, update in ADDITIONS.get('property_updates', {}).get(name, {}).items():
        assert digest(schema['properties'].get(field)) == update['after_sha256'], 'Reviewed field explanation changed: ' + name + '.' + field
        value['properties'][field] = update['before']
    return value


def prior_parameters(path, method, parameters):
    reviewed = ADDITIONS['operation_parameters'].get(path, {}).get(method, {})
    if not reviewed:
        return parameters
    for name, expected in reviewed.items():
        match = [parameter for parameter in parameters if parameter.get('name') == name]
        assert len(match) == 1 and digest(match[0]) == expected, 'Reviewed additive input changed: ' + path + ' ' + name
    return [parameter for parameter in parameters if parameter.get('name') not in reviewed]


def prior_response(path, method, status, schema):
    reviewed = ADDITIONS.get('response_properties', {}).get(path, {}).get(method, {}).get(status, {})
    value = deepcopy(schema)
    for field, expected in reviewed.items():
        assert digest(schema.get('properties', {}).get(field)) == expected, 'Reviewed response field changed: ' + path + ' ' + field
        value['properties'].pop(field)
    return value
