import jsonpickle

# pylint: disable=unused-variable, unused-argument

def dumps(obj, **args):
    return jsonpickle.encode(obj, unpicklable=False)

def loads(json, **args):
    return jsonpickle.decode(json)
