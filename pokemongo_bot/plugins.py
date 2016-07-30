import collections
import imp
import os
import logging

logging.basicConfig(level=logging.DEBUG)

__author__ = "Michael E. Cotterell"
__email__ = "mepcotterell@gmail.com"
__copyright__ = "Copyright 2013, Michael E. Cotterell"
__license__ = "MIT"


class PluginManager(object):
    """
    A simple plugin manager
    """

    def __init__(self, plugin_folder, main_module='__init__', log=logging):
        self.logging = log
        self.plugin_folder = plugin_folder
        self.main_module = main_module
        self.loaded_plugins = collections.OrderedDict()

    def get_available_plugins(self):
        """
        Returns a dictionary of plugins available in the plugin folder
        """
        plugins = {}
        for possible in os.listdir(self.plugin_folder):
            location = os.path.join(self.plugin_folder, possible)
            if os.path.isdir(location) and self.main_module + '.py' in os.listdir(location):
                info = imp.find_module(self.main_module, [location])
                plugins[possible] = {
                    'name': possible,
                    'info': info
                }
        return plugins

    def get_loaded_plugins(self):
        """
        Returns a dictionary of the loaded plugin modules
        """
        return self.loaded_plugins.copy()

    def load_plugin(self, plugin_name):
        """
        Loads a plugin module
        """
        plugins = self.get_available_plugins()
        if plugin_name in plugins:
            if plugin_name not in self.loaded_plugins:
                module = imp.load_module(self.main_module, *plugins[plugin_name]['info'])
                self.loaded_plugins[plugin_name] = {
                    'name': plugin_name,
                    'info': plugins[plugin_name]['info'],
                    'module': module
                }
                self.logging.log('plugin "%s" loaded' % plugin_name)
            else:
                self.logging.log('plugin "%s" already loaded' % plugin_name)
        else:
            self.logging.log('cannot locate plugin "%s"' % plugin_name)
            raise Exception('cannot locate plugin "%s"' % plugin_name)

    def unload_plugin(self, plugin_name):
        """
        Unloads a plugin module
        """
        del self.loaded_plugins[plugin_name]
        self.logging.log('plugin "%s" unloaded' % plugin_name)
