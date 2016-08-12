import unittest

from api.worldmap import Cell
from pokemongo_bot import CamperNavigator
from pokemongo_bot.navigation.destination import Destination
from pokemongo_bot.tests import create_test_config, create_mock_api_wrapper


class CamperNavigatorTest(unittest.TestCase):
    def test_navigate_campsite(self):
        config = create_test_config({
            "walk": 5,
            "max_steps": 2,
            "navigator_campsite": "{},{}".format(51.5043872, -0.0741802)
        })
        api_wrapper = create_mock_api_wrapper(config)

        navigator = CamperNavigator(config, api_wrapper)
        map_cells = self._create_map_cells()

        destinations = list()
        for destination in navigator.navigate(map_cells):
            assert isinstance(destination, Destination)

            assert destination.target_lat == 51.5043872
            assert destination.target_lng == -0.0741802
            assert destination.name == "Camping position at 51.5043872,-0.0741802"

            destinations.append(destination)

        assert len(destinations) == 1

    def test_navigate_campsite_last_position(self):
        config = create_test_config({
            "walk": 5,
            "max_steps": 2,
            "navigator_campsite": None,
            "location": "0,0"
        })
        api_wrapper = create_mock_api_wrapper(config)

        navigator = CamperNavigator(config, api_wrapper)
        map_cells = self._create_map_cells()

        destinations = list()
        for destination in navigator.navigate(map_cells):
            assert isinstance(destination, Destination)

            assert destination.target_lat == 0
            assert destination.target_lng == 0
            assert destination.name == "Camping position at 0,0"

            destinations.append(destination)

        assert len(destinations) == 1

    def test_navigate_campsite_invalid_index(self):
        config = create_test_config({
            "walk": 5,
            "max_steps": 2,
            "navigator_campsite": "{},{}".format(51.5043872, -0.0741802)
        })
        api_wrapper = create_mock_api_wrapper(config)

        navigator = CamperNavigator(config, api_wrapper)
        navigator.pointer = 100
        map_cells = self._create_map_cells()

        destinations = list()
        for _ in navigator.navigate(map_cells):
            pass

        assert len(destinations) == 0

    def test_navigate_campsite_add_before_start(self):
        config = create_test_config({
            "walk": 5,
            "max_steps": 2,
            "navigator_campsite": "{},{}".format(51.5043872, -0.0741802)
        })
        api_wrapper = create_mock_api_wrapper(config)

        navigator = CamperNavigator(config, api_wrapper)
        map_cells = self._create_map_cells()

        navigator.set_campsite(51.5060435, -0.073983)
        destinations = list()
        for destination in navigator.navigate(map_cells):
            assert isinstance(destination, Destination)

            assert destination.target_lat == 51.5060435
            assert destination.target_lng == -0.073983
            assert destination.name == "Camping position at 51.5060435,-0.073983"

            destinations.append(destination)

        assert len(destinations) == 1

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
                    self._create_pokestop(1, 51.5043872, -0.0741802),
                    self._create_pokestop(2, 51.5060435, -0.073983),
                ]
            })
        ]

    @staticmethod
    def _create_pokestop(name, lat, lng):
        return {
            "fort_id": str(name),
            "name": str(name),
            "latitude": lat,
            "longitude": lng,
            "enabled": 1,
            "last_modified_timestamp_ms": 0,
            "cooldown_complete_timestamp_ms": 0,
            "type": 1
        }
