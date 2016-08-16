import os
import unittest

from app import Kernel


class KernelTest(unittest.TestCase):
    @staticmethod
    def test_config_file():
        kernel = Kernel()
        kernel.set_config_file('test/config.yml')

        assert (kernel.get_config_file()) == 'test/config.yml'

    @staticmethod
    def test_load_config():
        kernel = Kernel()
        kernel.set_config_file(os.path.join(os.path.dirname(__file__), 'config', 'config.yml'))
        kernel.load_config()

        config = kernel.get_config()

        assert 'core' in config
        assert 'another_test_plugin' in config
        assert 'test_plugin' not in config
