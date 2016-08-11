import os
import json
import unittest

from mock import Mock, call

from api.worldmap import Cell
from pokemongo_bot.mapper import Mapper
from pokemongo_bot.stepper import Stepper
from pokemongo_bot.navigation.destination import Destination
from pokemongo_bot.navigation.path_finder import DirectPathFinder
from pokemongo_bot.navigation.path_finder import GooglePathFinder
from pokemongo_bot.tests import create_mock_bot, create_test_config, create_mock_api_wrapper


class MapperTest(unittest.TestCase):
    @staticmethod
    def test_init():
        api_wrapper = create_mock_api_wrapper()
        config = create_test_config({
            "walk": 13.37,
        })
        mapper = Mapper(config, api_wrapper)

        assert mapper.config == config
        assert mapper.api_wrapper == api_wrapper

    def test_get_cells(self):
        api_wrapper = create_mock_api_wrapper()
        config = create_test_config({
            "username": "testaccount1337"
        })
        mapper = Mapper(config, api_wrapper)

        api_wrapper.set_position(51.5044524, -0.0752479, 10)

        pgo = api_wrapper._api
        pgo.set_response("get_map_objects", {
            "map_cells": [
                self._create_map_cell(1),
                self._create_map_cell(2),
                self._create_map_cell(3),
                self._create_map_cell(4),
                self._create_map_cell(5)
            ]
        })

        # Clean up any old location logs
        if os.path.isfile('data/last-location-testaccount1.json'):
            os.unlink('data/last-location-testaccount1.json')

        cells = mapper.get_cells(51.5044524, -0.0752479)

        assert len(cells) == 5

        assert os.path.isfile('data/last-location-testaccount1.json') is True
        with open('data/last-location-testaccount1.json') as data_file:
            data = json.load(data_file)
            assert data["lat"] == 51.5044524
            assert data["lng"] == -0.0752479

        os.unlink('data/last-location-testaccount1.json')

    @staticmethod
    def test_get_cells_no_response():
        api_wrapper = create_mock_api_wrapper()
        config = create_test_config({
            "username": "testaccount1337"
        })
        mapper = Mapper(config, api_wrapper)

        api_wrapper.set_position(51.5044524, -0.0752479, 10)

        pgo = api_wrapper._api  # pylint: disable=protected-access
        pgo.set_response("get_map_objects", {})
        api_wrapper.call = Mock(return_value=None)

        # Clean up any old location logs
        if os.path.isfile('data/last-location-testaccount3.json'):
            os.unlink('data/last-location-testaccount3.json')

        cells = mapper.get_cells(51.5044524, -0.0752479)

        assert len(cells) == 0

    def _create_map_cell(self, cell_id):
        return {
            "s2_cell_id": cell_id,
            "spawn_points": [
                {
                    "latitude": 0,
                    "longitude": 0
                }
            ],
            "forts": [
                self._create_pokestop(cell_id),
                self._create_pokestop(cell_id),
                self._create_pokestop(cell_id),
                self._create_pokestop(cell_id),
                self._create_pokestop(cell_id)
            ]
        }

    @staticmethod
    def _create_pokestop(cell_id):
        return {
            "id": "fort_" + str(cell_id),
            "name": str(cell_id),
            "latitude": cell_id,
            "longitude": cell_id,
            "enabled": 1,
            "last_modified_timestamp_ms": 0,
            "cooldown_complete_timestamp_ms": 0,
            "type": 1
        }
