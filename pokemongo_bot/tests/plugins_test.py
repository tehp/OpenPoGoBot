import unittest
import os
import pytest

from pokemongo_bot.plugins import PluginManager


class PluginsTest(unittest.TestCase):
    def setUp(self):
        import sys
        from io import StringIO

        self.out = StringIO()
        sys.stdout = self.out

    @staticmethod
    def test_get_available_plugins():
        plugin_manager = PluginManager(os.path.dirname(os.path.realpath(__file__)) + '/plugins')

        plugins = plugin_manager.get_available_plugins()

        assert len(plugins) == 2
        assert 'test_plugin' in plugins
        assert 'name' in plugins['test_plugin']
        assert plugins['test_plugin']['name'] == 'test_plugin'
        assert 'info' in plugins['test_plugin']

    def test_load_plugin(self):
        plugin_manager = PluginManager(os.path.dirname(os.path.realpath(__file__)) + '/plugins')

        plugin_manager.load_plugin('test_plugin')

        loaded_plugins = plugin_manager.get_loaded_plugins()

        assert len(loaded_plugins) == 1
        assert 'test_plugin' in loaded_plugins
        assert 'name' in loaded_plugins['test_plugin']
        assert loaded_plugins['test_plugin']['name'] == 'test_plugin'
        assert 'info' in loaded_plugins['test_plugin']

        assert 'Loaded plugin "test_plugin".' in self.out.getvalue().strip()

    def test_load_plugin_already_loaded(self):
        plugin_manager = PluginManager(os.path.dirname(os.path.realpath(__file__)) + '/plugins')

        plugin_manager.load_plugin('test_plugin')
        plugin_manager.load_plugin('test_plugin')

        loaded_plugins = plugin_manager.get_loaded_plugins()

        assert len(loaded_plugins) == 1
        assert 'test_plugin' in loaded_plugins

        assert 'Loaded plugin "test_plugin".' in self.out.getvalue().strip()
        assert 'Plugin "test_plugin" was already loaded!' in self.out.getvalue().strip()

    def test_load_plugin_not_exists(self):
        with pytest.raises(Exception) as _:
            plugin_manager = PluginManager(os.path.dirname(os.path.realpath(__file__)) + '/plugins')

            plugin_manager.load_plugin('unknown')

            assert 'Cannot locate plugin "unknown"!' in self.out.getvalue().strip()

    def test_unload_plugin(self):
        plugin_manager = PluginManager(os.path.dirname(os.path.realpath(__file__)) + '/plugins')

        plugin_manager.load_plugin('test_plugin')

        loaded_plugins = plugin_manager.get_loaded_plugins()

        assert len(loaded_plugins) == 1
        assert 'test_plugin' in loaded_plugins

        plugin_manager.unload_plugin('test_plugin')

        assert 'Unloaded plugin "test_plugin".' in self.out.getvalue().strip()
