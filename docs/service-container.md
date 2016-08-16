# Kernels, Service Container and Services
If you're not familiar with Dependency Injection (DI), please see [have a read](https://en.wikipedia.org/wiki/Dependency_injection#Examples).

In order to make DI as easy as possible an app kernel and service container manager class dependencies.

## The Kernel

The [kernel](../app/kernel.py) is responsible for the outer functionality of the app. That is, loading plugins and setting up the service container.

## The Service Container
The [ServiceContainer](../app/service_container.py) handles all of your class dependencies. It also handles registering new services and parameters.

### Registering a New Service

New services can be registered in one of two ways:

 - Via a decorator
 - Via code at runtime


#### Registering With a Decorator

Say we have a class named `Pokemon`, and we have dependencies on the `Config`, `PoGoApi`, and a scalar value `log_dir`. 
Our class will look something like this:

```python
from app import kernel

@kernel.container.register('pokemon', ['@config', '@api_wrapper'], {'dir': '%log_dir%'})
class Pokemon(object):
    def __init__(self, config, api, dir=None)
        self._api = api
```

`register` can take 4 arguments:

 - The service name (that is, the name by which other services will recognise this service as)
 - A List of constructor arguments.
 - A Dict of keyword arguments
 - An array of Tags. Tags can be used to fetch a collection of services that are all tagged with the same name.

##### Argument Syntax
When passing in arguments defined with a decorator, the service container will look for specific formats to identify 
services, parameters and flat values:

- To reference a service, prefix the name with @. For example, `@api_wrapper` would inject the PoGoApi service.
- To reference a parameter, wrap the name with %. For example, `%log_dir%` would reference the value of the `log_dir` paramterer.
- To use a staic value, just don't use the syntax of a service or parameter.

#### Registering a Singleton

If you need to register a singleton object, you can do this by calling `service_container.register_singleton`:

```python
pokemon_service = Pokemon(
    kernel.container.get('config'),
    kernel.container.get('api_wrapper'),
    log_dir = kernel.container.get_parameter('log_dir'),
)

kernel.container.register_singleton(pokemon_service)
```

### Fetching a Service

If you need to fetch a service from the container, you can call `service_container.get`:

```python
pokemon_service = kernel.container.get('pokemon')
```

### Getting and Setting Parameters

Getting and setting is done by calling `service_container.get_parameter` and  `service_container.set_parameter` 
respectively:

```python
kernel.container.set_parameter('pokemon', 'is great')
#... 
pokemon_parameter = kernel.container.get_parameter('pokemon') # 'is great'
```

### Plugins
The kernel loads plugins automatically from the [./plugins](../plugins) directory. In order to load the plugin, the plugin class service must be tagged with 'plugin':

```
from app import kernel


@kernel.container.register('plugin_service', tags=['plugin'])
class PluginService(object):
    # ...

```
