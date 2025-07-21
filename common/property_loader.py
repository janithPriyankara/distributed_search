# Property loader utility
import json


_properties = None

def load_properties(path):
    global _properties
    if _properties is None:
        with open(path) as f:
            _properties = json.load(f)
    return _properties

def get_property(key, default=None):
    global _properties
    if _properties is None:
        raise RuntimeError("Properties not loaded. Call load_properties(path) first.")
    return _properties.get(key, default)
