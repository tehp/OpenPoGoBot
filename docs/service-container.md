# Services and the Service Container
If you're not familiar with Dependency Injection (DI), please see [have a read](https://en.wikipedia.org/wiki/Dependency_injection#Examples).

In order to make DI as easy as possible, a [ServiceContainer](../app/service_container.py) handles all of your class 
dependencies. The ServiceContainer handles registering new services and parameters.

## Registering a New Service

New services can be registered in one of two ways:

 - Via a decorator
 - Via code at runtime


### Registering With a Decorator

Say we have a class named `Pokemon`, and we have dependencies on the `Config`, `PoGoApi`, and a scalar value `log_dir`. 
Our class will look something like this:

```python
from app import service_container

@service_container.register('pokemon', ['@config', '@api_wrapper'], {'dir': '%log_dir%'})
class Pokemon(object):
    def __init__(self, config, api, dir=None)
        self._api = api
```

`register` takes 3 arguments:

 - The service name (that is, the name by which other services will recognise this service as)
 - A List of constructor arguments.
 - A Dict of keyword arguments

#### Argument Syntax
When passing in arguments defined with a decorator, the service container will look for specific formats to identify 
services, parameters and flat values:

- To reference a service, prefix the name with @. For example, `@api_wrapper` would inject the PoGoApi service.
- To reference a parameter, wrap the name with %. For example, `%log_dir%` would reference the value of the `log_dir` paramterer.
- To use a staic value, just don't use the syntax of a service or parameter.

### Registering a Singleton

If you need to register a singleton object, you can do this by calling `service_container.register_singleton`:

```python
pokemon_service = Pokemon(
    service_container.get('config'),
    service_container.get('api_wrapper'),
    log_dir = service_container.get_parameter('log_dir'),
)

service_container.register_singleton(pokemon_service)
```

## Fetching a Service

If you need to fetch a service from the container, you can call `service_container.get`:

```python
pokemon_service = service_container.get('pokemon')
```

## Getting and Setting Parameters

Getting and setting is done by calling `service_container.get_parameter` and  `service_container.set_parameter` 
respectively:

```python
service_container.set_parameter('pokemon', 'is great')
#... 
pokemon_parameter = service_container.get_parameter('pokemon') # 'is great'
```
