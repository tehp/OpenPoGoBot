import os

from app.service_container import ServiceContainer
from app.plugin_manager import PluginManager

import ruamel.yaml


class Kernel(object):
    """
        The Kernel handles the creation of the app and service container.
    """
    def __init__(self):
        # type: () -> None
        self.container = ServiceContainer()
        self._plugins = []
        self._plugin_manager = None
        self._disabled_plugins = []
        self._configs = {}
        self._booted = False
        self._config_file = './config'

    def set_config_file(self, config_dir):
        self._config_file = config_dir

    def get_config_file(self):
        return self._config_file

    def load_config(self):
        # type: (str) -> None
        with open(self._config_file, 'r') as config_file:
            self._configs['core'] = ruamel.yaml.load(config_file.read(), ruamel.yaml.RoundTripLoader)

        for plugin in self._configs['core']['plugins']['exclude']:
            self.disable_plugin(plugin)

        config_dir = os.path.dirname(self._config_file)
        for node in os.listdir(os.path.join(config_dir, 'plugins')):
            location = os.path.join(config_dir, 'plugins', node)
            if os.path.isfile(location) and node[-4:].lower() == '.yml':
                with open(location, 'r') as config_file:
                    module_name = node[:-4]
                    self._configs[module_name] = ruamel.yaml.load(config_file.read(), ruamel.yaml.RoundTripLoader)

    def get_config(self):
        return self._configs

    def disable_plugin(self, plugin_name):
        # type: (str) -> None
        self._disabled_plugins.append(plugin_name)

    def boot(self):
        # type: () -> None
        self.load_config()
        self._plugin_manager = PluginManager(self._configs['core']['plugins']['include'])
        for plugin in self._plugin_manager.get_available_plugins():
            if plugin not in self._disabled_plugins:
                self._plugin_manager.load_plugin(plugin)

        self.container.set_parameter('kernel.config_dir', self._config_file)
        for config_name in self._configs:
            self.container.register_singleton('config.' + config_name, self._configs[config_name])

        self.container.boot()

        for plugin in self.container.get_by_tag('plugin'):
            self._plugins.append(plugin)

        self._booted = True
