import jsonpickle

# pylint: disable=unused-variable, unused-argument

jsonpickle.set_preferred_backend("json")

def dumps(obj, **args):
    return jsonpickle.encode(obj, unpicklable=False)

def loads(json, **args):
    return jsonpickle.decode(json)
