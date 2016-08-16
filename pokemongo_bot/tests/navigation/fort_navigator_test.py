import unittest

from mock import MagicMock

from api.worldmap import Cell
from pokemongo_bot import FortNavigator
from pokemongo_bot.navigation.destination import Destination
from pokemongo_bot.tests import create_mock_api_wrapper, create_core_test_config


class FortNavigatorTest(unittest.TestCase):

    def test_navigate_pokestops_known(self):
        config = create_core_test_config()
        api_wrapper = create_mock_api_wrapper(config)
        navigator = FortNavigator(config, api_wrapper)

        pgoapi = api_wrapper.get_api()
        pgoapi.set_response('fort_details', self._create_pokestop("Test Stop", 51.5043872, -0.0741802))
        pgoapi.set_response('fort_details', self._create_pokestop("Test Stop 2", 51.5060435, -0.073983))

        map_cells = self._create_map_cells()

        destinations = list()
        for destination in navigator.navigate(map_cells):
            assert isinstance(destination, Destination)

            if len(destinations) == 0:
                assert destination.target_lat == 51.5043872
                assert destination.target_lng == -0.0741802
                assert destination.name == "PokeStop \"Test Stop\""
            elif len(destinations) == 1:
                assert destination.target_lat == 51.5060435
                assert destination.target_lng == -0.073983
                assert destination.name == "PokeStop \"Test Stop 2\""

            destinations.append(destination)

        assert len(destinations) == 2
        assert pgoapi.call_stack_size() == 0

    def test_navigate_pokestops_unknown(self):
        config = create_core_test_config()
        api_wrapper = create_mock_api_wrapper(config)
        api_wrapper.call = MagicMock(return_value=None)
        navigator = FortNavigator(config, api_wrapper)

        pgoapi = api_wrapper.get_api()

        map_cells = self._create_map_cells()

        destinations = list()
        for destination in navigator.navigate(map_cells):
            assert isinstance(destination, Destination)

            if len(destinations) == 0:
                assert destination.target_lat == 51.5043872
                assert destination.target_lng == -0.0741802
                assert destination.name == "PokeStop \"fort_unknown1\""
            elif len(destinations) == 1:
                assert destination.target_lat == 51.5060435
                assert destination.target_lng == -0.073983
                assert destination.name == "PokeStop \"fort_unknown2\""

            destinations.append(destination)

        assert len(destinations) == 2
        assert pgoapi.call_stack_size() == 0

    def _create_map_cells(self):
        return [
            Cell({
                "s2_cell_id": 1,
                "spawn_points": [
                    {
                        "latitude": 0,
                        "longitude": 0
                    }
                ],
                "forts": [
                    self._create_pokestop("unknown1", 51.5043872, -0.0741802),
                    self._create_pokestop("unknown2", 51.5060435, -0.073983),
                ]
            })
        ]

    @staticmethod
    def _create_pokestop(name, lat, lng):
        return {
            "id": "fort_" + str(name),
            "name": str(name),
            "latitude": lat,
            "longitude": lng,
            "enabled": 1,
            "last_modified_timestamp_ms": 0,
            "cooldown_complete_timestamp_ms": 0,
            "type": 1
        }
