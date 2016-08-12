class ServiceContainer(object):
    def __init__(self):
        self._services_definitions = {}
        self._services = {}
        self._parameters = {}

    def register(self, service_id, arguments=None, keywordsargs=None):

        def register_handler(function):
            self._services_definitions[service_id] = (function, arguments, keywordsargs)
            return function

        return register_handler

    def register_singleton(self, service_id, service_instance):
        self._services[service_id] = service_instance

    def _make_service(self, service_id):
        service_class, service_args, service_kwargs = self._services_definitions[service_id]

        args = []
        if service_args is not None:
            for service_arg in service_args:
                if service_arg[0] == '%' and service_arg[-1:] == '%':
                    param = self.get_parameter(service_arg[1:-1])
                    if self.has(param):
                        args.append(self.get(param))
                    else:
                        args.append(param)
                else:
                    if service_arg[0] == '@' and self.has(service_arg[1:]):
                        args.append(self.get(service_arg[1:]))
                    else:
                        args.append(service_arg)

        kwargs = {}
        if service_kwargs is not None:
            for service_kwarg_param in service_kwargs:
                service_kwarg = service_kwargs[service_kwarg_param]
                if self.has(service_kwarg):
                    kwargs[service_kwarg_param] = self.get(service_kwarg)
                else:
                    kwargs[service_kwarg_param] = service_kwarg

        return service_class(*args, **kwargs)

    def get(self, service_id):
        if not self.has(service_id):
            raise Exception('Service "{}" was not registered.'.format(service_id))

        if service_id not in self._services:
            self._services[service_id] = self._make_service(service_id)

        return self._services[service_id]

    def has(self, service_id):
        return service_id in self._services_definitions or service_id in self._services

    def get_parameter(self, parameter):
        return self._parameters[parameter]

    def set_parameter(self, parameter, value):
        self._parameters[parameter] = value
