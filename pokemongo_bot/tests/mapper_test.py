import os
import json
import unittest

from googlemaps import Client
from googlemaps.exceptions import ApiError
from mock import Mock
from mock import call

from pokemongo_bot.mapper import Mapper
from pokemongo_bot.tests import create_core_test_config, create_mock_api_wrapper, test_account_name


class MapperTest(unittest.TestCase):
    @staticmethod
    def test_init():
        config = create_core_test_config()
        api_wrapper = create_mock_api_wrapper(config)
        google_maps = Mock(spec=Client)
        logger = Mock()
        logger.log = Mock(return_value=None)
        mapper = Mapper(config, api_wrapper, google_maps, logger)

        assert mapper.config == config
        assert mapper.api_wrapper == api_wrapper
        assert mapper.google_maps == google_maps

    def test_get_cells(self):
        account = test_account_name()
        config = create_core_test_config({
            "debug": True,
            "login": {
                "username": account,
            },
            "mapping": {
                "cell_radius": 500
            }
        })
        api_wrapper = create_mock_api_wrapper(config)
        google_maps = Mock(spec=Client)
        logger = Mock()
        logger.log = Mock(return_value=None)
        mapper = Mapper(config, api_wrapper, google_maps, logger)

        api_wrapper.set_position(51.5044524, -0.0752479, 10)

        pgo = api_wrapper.get_api()
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
        if os.path.isfile('data/last-location-'+account+'.json'):
            os.unlink('data/last-location-'+account+'.json')

        cells = mapper.get_cells(51.5044524, -0.0752479)

        assert len(cells) == 5

        assert bool(os.path.isfile('data/last-location-'+account+'.json')) is True
        with open('data/last-location-'+account+'.json') as data_file:
            data = json.load(data_file)
            assert data["lat"] == 51.5044524
            assert data["lng"] == -0.0752479

        os.unlink('data/last-location-'+account+'.json')

    @staticmethod
    def test_get_cells_no_response():
        account = test_account_name()
        config = create_core_test_config({
            "login": {
                "username": account
            },
            "mapping": {
                "cell_radius": 500
            }
        })
        api_wrapper = create_mock_api_wrapper(config)
        google_maps = Mock(spec=Client)
        logger = Mock()
        logger.log = Mock(return_value=None)
        mapper = Mapper(config, api_wrapper, google_maps, logger)

        api_wrapper.set_position(51.5044524, -0.0752479, 10)

        pgo = api_wrapper.get_api()
        pgo.set_response("get_map_objects", {})
        api_wrapper.call = Mock(return_value=None)

        # Clean up any old location logs
        if os.path.isfile('data/last-location-'+account+'.json'):
            os.unlink('data/last-location-'+account+'.json')

        cells = mapper.get_cells(51.5044524, -0.0752479)

        assert len(cells) == 0

    @staticmethod
    def test_find_location_with_coordinates():
        config = create_core_test_config()
        api_wrapper = create_mock_api_wrapper(config)
        google_maps = Mock(spec=Client)
        google_maps.elevation = Mock(return_value=[{'elevation': 10.1}])
        logger = Mock()
        logger.log = Mock(return_value=None)
        mapper = Mapper(config, api_wrapper, google_maps, logger)

        lat, lng, alt = mapper.find_location('51.5044524, -0.0752479')

        assert lat == 51.5044524
        assert lng == -0.0752479
        assert alt == 10.1

    @staticmethod
    def test_find_location_with_coordinates_google_error():
        config = create_core_test_config()
        api_wrapper = create_mock_api_wrapper(config)
        google_maps = Mock(spec=Client)
        google_maps.elevation = Mock(side_effect=ApiError(403))
        location = Mock()
        location.latitude = 51.5044524
        location.longitude = -0.0752479
        location.altitude = 10.1
        google_maps.geocode = Mock(return_value=location)
        logger = Mock()
        logger.log = Mock(return_value=None)
        mapper = Mapper(config, api_wrapper, google_maps, logger)

        lat, lng, alt = mapper.find_location('51.5044524, -0.0752479')

        assert lat == 51.5044524
        assert lng == -0.0752479
        assert alt == 10.1

    @staticmethod
    def test_find_location_with_coordinates_invalid_response():
        config = create_core_test_config()
        api_wrapper = create_mock_api_wrapper(config)
        google_maps = Mock(spec=Client)
        google_maps.elevation = Mock(return_value=None)
        location = Mock()
        location.latitude = 51.5044524
        location.longitude = -0.0752479
        location.altitude = 10.1
        google_maps.geocode = Mock(return_value=location)
        logger = Mock()
        logger.log = Mock(return_value=None)
        mapper = Mapper(config, api_wrapper, google_maps, logger)

        lat, lng, alt = mapper.find_location('51.5044524, -0.0752479')

        assert lat == 51.5044524
        assert lng == -0.0752479
        assert alt == 10.1

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
