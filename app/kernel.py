from app.service_container import ServiceContainer
from app.plugin_manager import PluginManager


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
        self._config = None
        self._booted = False

    def import_config(self, config):
        # type: (Dict) -> None
        self._config = config

    def load_config(self, location):
        # type: (str) -> None
        pass

    def disable_plugin(self, plugin_name):
        # type: (str) -> None
        self._disabled_plugins.append(plugin_name)

    def boot(self):
        # type: () -> None
        self._plugin_manager = PluginManager(self._config["plugins"]["include"])
        for plugin in self._plugin_manager.get_available_plugins():
            if plugin not in self._disabled_plugins:
                self._plugin_manager.load_plugin(plugin)

        self.container.config = self._config
        self.container.register_singleton('config', self._config)
        self.container.boot()

        for plugin in self.container.get_by_tag('plugin'):
            self._plugins.append(plugin)

        self._booted = True
