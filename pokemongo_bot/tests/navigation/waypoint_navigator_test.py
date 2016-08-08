import unittest

from api.worldmap import Cell
from pokemongo_bot import WaypointNavigator
from pokemongo_bot.navigation.destination import Destination
from pokemongo_bot.tests import create_mock_bot


class WaypointNavigatorTest(unittest.TestCase):

    def test_navigate_waypoint(self):
        bot = create_mock_bot({
            "walk": 5,
            "max_steps": 2,
            "navigator_waypoints": [
                [51.5043872, -0.0741802],
                [51.5060435, -0.073983]
            ]
        })

        navigator = WaypointNavigator(bot)
        map_cells = self._create_map_cells()

        destinations = list()
        for destination in navigator.navigate(map_cells):
            assert isinstance(destination, Destination)

            if len(destinations) == 0:
                assert destination.target_lat == 51.5043872
                assert destination.target_lng == -0.0741802
                assert destination.name == "Waypoint at 51.5043872,-0.0741802"
            elif len(destinations) == 1:
                assert destination.target_lat == 51.5060435
                assert destination.target_lng == -0.073983
                assert destination.name == "Waypoint at 51.5060435,-0.073983"

            destinations.append(destination)

        assert len(destinations) == 2

    def test_navigate_waypoint_add(self):
        bot = create_mock_bot({
            "walk": 5,
            "max_steps": 2,
            "navigator_waypoints": [
                [51.5043872, -0.0741802],
                [51.5060435, -0.073983]
            ]
        })

        navigator = WaypointNavigator(bot)
        map_cells = self._create_map_cells()

        navigator.waypoint_add(51.5087667, -0.0732307)

        destinations = list()
        for destination in navigator.navigate(map_cells):
            assert isinstance(destination, Destination)

            if len(destinations) == 0:
                assert destination.target_lat == 51.5043872
                assert destination.target_lng == -0.0741802
                assert destination.name == "Waypoint at 51.5043872,-0.0741802"
            elif len(destinations) == 1:
                assert destination.target_lat == 51.5060435
                assert destination.target_lng == -0.073983
                assert destination.name == "Waypoint at 51.5060435,-0.073983"
            elif len(destinations) == 2:
                assert destination.target_lat == 51.5087667
                assert destination.target_lng == -0.0732307
                assert destination.name == "Waypoint at 51.5087667,-0.0732307"

            destinations.append(destination)

        assert len(destinations) == 3

    def test_navigate_waypoint_add_runtime(self):
        bot = create_mock_bot({
            "walk": 5,
            "max_steps": 2,
            "navigator_waypoints": [
                [51.5043872, -0.0741802],
                [51.5060435, -0.073983]
            ]
        })

        navigator = WaypointNavigator(bot)
        map_cells = self._create_map_cells()

        waypoint_add = True
        destinations = list()
        for destination in navigator.navigate(map_cells):
            assert isinstance(destination, Destination)

            if len(destinations) == 0:
                assert destination.target_lat == 51.5043872
                assert destination.target_lng == -0.0741802
                assert destination.name == "Waypoint at 51.5043872,-0.0741802"
            elif len(destinations) == 1:
                assert destination.target_lat == 51.5060435
                assert destination.target_lng == -0.073983
                assert destination.name == "Waypoint at 51.5060435,-0.073983"
            elif len(destinations) == 2:
                assert destination.target_lat == 51.5087667
                assert destination.target_lng == -0.0732307
                assert destination.name == "Waypoint at 51.5087667,-0.0732307"

            # Inject a new waypoint after first visit
            if waypoint_add is True:
                navigator.waypoint_add(51.5087667, -0.0732307)
                waypoint_add = False

            destinations.append(destination)

        assert len(destinations) == 3

    def test_navigate_waypoint_remove(self):
        bot = create_mock_bot({
            "walk": 5,
            "max_steps": 2,
            "navigator_waypoints": [
                [51.5043872, -0.0741802],
                [51.5060435, -0.073983]
            ]
        })

        navigator = WaypointNavigator(bot)
        map_cells = self._create_map_cells()

        navigator.waypoint_remove(0)

        destinations = list()
        for destination in navigator.navigate(map_cells):
            assert isinstance(destination, Destination)

            assert destination.target_lat == 51.5060435
            assert destination.target_lng == -0.073983
            assert destination.name == "Waypoint at 51.5060435,-0.073983"

            destinations.append(destination)

        assert len(destinations) == 1

    def test_navigate_waypoint_remove_runtime(self):
        bot = create_mock_bot({
            "walk": 5,
            "max_steps": 2,
            "navigator_waypoints": [
                [51.5043872, -0.0741802],
                [51.5060435, -0.073983]
            ]
        })

        navigator = WaypointNavigator(bot)
        map_cells = self._create_map_cells()

        waypoint_remove = True
        destinations = list()
        for destination in navigator.navigate(map_cells):
            assert isinstance(destination, Destination)

            assert destination.target_lat == 51.5043872
            assert destination.target_lng == -0.0741802
            assert destination.name == "Waypoint at 51.5043872,-0.0741802"

            # Inject a new waypoint after first visit
            if waypoint_remove is True:
                navigator.waypoint_remove(1)
                waypoint_remove = False

            destinations.append(destination)

        assert len(destinations) == 1

    @staticmethod
    def test_navigate_waypoint_remove_not_exists():
        bot = create_mock_bot({
            "walk": 5,
            "max_steps": 2,
            "navigator_waypoints": [
                [51.5043872, -0.0741802],
                [51.5060435, -0.073983]
            ]
        })

        navigator = WaypointNavigator(bot)

        navigator.waypoint_remove(100)

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
