import os
import json
import unittest

from mock import Mock, call

from api.worldmap import Cell
from pokemongo_bot import Mapper
from pokemongo_bot import Stepper
from pokemongo_bot.navigation.destination import Destination
from pokemongo_bot.navigation.path_finder import DirectPathFinder
from pokemongo_bot.navigation.path_finder import GooglePathFinder
from pokemongo_bot.tests import create_mock_bot


class MapperTest(unittest.TestCase):
    @staticmethod
    def test_init():
        bot = create_mock_bot({
            "walk": 13.37,
        })

        bot.position = (51.5044524, -0.0752479, 10)
        mapper = Mapper(bot)

        assert mapper.bot == bot
        assert mapper.stepper == bot.stepper
        assert mapper.api_wrapper == bot.api_wrapper
        assert mapper.config == bot.config

    def test_get_cells(self):
        bot = create_mock_bot({
            "username": "testaccount1"
        })
        bot.position = (51.5044524, -0.0752479, 10)
        bot.stepper = Stepper(bot)
        bot.stepper.start()

        pgo = bot.api_wrapper._api  # pylint: disable=protected-access

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

        mapper = Mapper(bot)

        cells = mapper.get_cells(51.5044524, -0.0752479)

        assert len(cells) == 5

        assert os.path.isfile('data/last-location-testaccount1.json') is True
        with open('data/last-location-testaccount1.json') as data_file:
            data = json.load(data_file)
            assert data["lat"] == 51.5044524
            assert data["lng"] == -0.0752479

        os.unlink('data/last-location-testaccount1.json')

    def test_get_cells_at_current_position(self):
        bot = create_mock_bot({
            "username": "testaccount2"
        })
        bot.position = (51.5044524, -0.0752479, 10)
        bot.stepper = Stepper(bot)
        bot.stepper.start()

        pgo = bot.api_wrapper._api  # pylint: disable=protected-access

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
        if os.path.isfile('data/last-location-testaccount2.json'):
            os.unlink('data/last-location-testaccount2.json')

        mapper = Mapper(bot)

        cells = mapper.get_cells_at_current_position()

        assert len(cells) == 5

        assert os.path.isfile('data/last-location-testaccount2.json') is True
        with open('data/last-location-testaccount2.json') as data_file:
            data = json.load(data_file)
            assert data["lat"] == 51.5044524
            assert data["lng"] == -0.0752479

        os.unlink('data/last-location-testaccount2.json')

    @staticmethod
    def test_get_cells_no_response():
        bot = create_mock_bot({
            "username": "testaccount3"
        })
        bot.position = (51.5044524, -0.0752479, 10)
        bot.stepper = Stepper(bot)
        bot.stepper.start()

        pgo = bot.api_wrapper._api  # pylint: disable=protected-access

        pgo.set_response("get_map_objects", {})
        bot.api_wrapper.call = Mock(return_value=None)

        # Clean up any old location logs
        if os.path.isfile('data/last-location-testaccount3.json'):
            os.unlink('data/last-location-testaccount3.json')

        mapper = Mapper(bot)

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
