from __future__ import print_function
import collections
import imp
import os
import time

from colorama import Fore, Style

__author__ = "Michael E. Cotterell"
__email__ = "mepcotterell@gmail.com"
__copyright__ = "Copyright 2013, Michael E. Cotterell"
__license__ = "MIT"


def log(text, color=None):
    # type: (str, Optional[str]) -> None

    # Added because this code needs to run without importing the logger module.
    color_hex = {
        'green': Fore.GREEN,
        'yellow': Fore.YELLOW,
        'red': Fore.RED
    }
    string = str(text)
    output = u"[" + time.strftime("%Y-%m-%d %H:%M:%S") + u"] [Plugin Manager] {}".format(string)
    if color in color_hex:
        output = color_hex[color] + output + Style.RESET_ALL
    print(output)


class PluginManager(object):
    """
    A simple plugin manager
    """

    def __init__(self, plugin_folder, main_module='__init__'):
        self.plugin_folder = plugin_folder
        self.main_module = main_module
        self.loaded_plugins = collections.OrderedDict()

    def get_available_plugins(self):
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
        return self.loaded_plugins.copy()

    def load_plugin(self, plugin_name):
        plugins = self.get_available_plugins()
        if plugin_name in plugins:
            if plugin_name not in self.loaded_plugins:
                module = imp.load_module(self.main_module, *plugins[plugin_name]['info'])
                self.loaded_plugins[plugin_name] = {
                    'name': plugin_name,
                    'info': plugins[plugin_name]['info'],
                    'module': module
                }
                log('Loaded plugin "%s".' % plugin_name, color="green")
            else:
                log('Plugin "%s" was already loaded!' % plugin_name, color="yellow")
        else:
            log('Cannot locate plugin "%s"!' % plugin_name, color="red")
            raise Exception('Cannot locate plugin "%s"' % plugin_name)

    def unload_plugin(self, plugin_name):
        del self.loaded_plugins[plugin_name]
        log('Unloaded plugin "%s".' % plugin_name, color="green")
