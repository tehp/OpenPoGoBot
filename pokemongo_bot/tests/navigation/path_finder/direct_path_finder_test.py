import unittest

from pokemongo_bot.navigation.path_finder import DirectPathFinder
from pokemongo_bot.tests import create_mock_bot


class DirectPathFinderTest(unittest.TestCase):
    def test_path(self): # pylint: disable=no-self-use
        bot = create_mock_bot(None)

        stepper = bot.stepper

        path_finder = DirectPathFinder(stepper)

        path = path_finder.path(51.5043872, -0.0741802, 51.5060435, -0.073983)

        assert len(path) == 1
        lat, lng = path[0]
        assert lat == 51.5060435
        assert lng == -0.073983
