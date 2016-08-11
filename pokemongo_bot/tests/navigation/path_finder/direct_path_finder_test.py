import unittest

from pokemongo_bot.navigation.path_finder import DirectPathFinder
from pokemongo_bot.tests import create_test_config


class DirectPathFinderTest(unittest.TestCase):
    @staticmethod
    def test_path():
        config = create_test_config()
        path_finder = DirectPathFinder(config)

        path = path_finder.path(51.5043872, -0.0741802, 51.5060435, -0.073983)

        assert len(path) == 1
        lat, lng = path[0]
        assert lat == 51.5060435
        assert lng == -0.073983
