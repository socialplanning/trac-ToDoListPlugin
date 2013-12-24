import json

def json_dumps_default(obj):
    if hasattr(obj, 'to_json'):
        return obj.to_json()

def json_dumps(data):
    return json.dumps(data, indent=2, default=json_dumps_default)

