import unittest
from mock import patch, Mock, MagicMock

from pokemongo_bot.navigation.path_finder import GooglePathFinder
from pokemongo_bot.tests import create_mock_bot


class GooglePathFinderTest(unittest.TestCase):

    @staticmethod
    def test_path():

        with patch('googlemaps.Client') as GoogleMapsClient:
            client = Mock()
            client.directions = MagicMock(return_value=[
                {
                    "legs": [
                        {
                            "steps": [
                                {
                                    "end_location": {
                                        "lat": 51.5043872,
                                        "lng": -0.0741802
                                    }
                                },
                                {
                                    "end_location": {
                                        "lat": 51.5050996,
                                        "lng": -0.0747055
                                    }
                                }
                            ]
                        },
                        {
                            "steps": [
                                {
                                    "end_location": {
                                        "lat": 51.5060607,
                                        "lng": -0.0746535
                                    }
                                }
                            ]
                        }
                    ]
                }
            ])
            GoogleMapsClient.return_value = client
            bot = create_mock_bot({
                "gmapkey": "abc123"
            })
            stepper = bot.stepper

            path_finder = GooglePathFinder(stepper)
            path = path_finder.path(51.5043872, -0.0741802, 51.5060435, -0.073983)

            assert len(path) == 4

            lat, lng = path[0]
            assert lat == 51.5043872
            assert lng == -0.0741802

            lat, lng = path[1]
            assert lat == 51.5050996
            assert lng == -0.0747055

            lat, lng = path[2]
            assert lat == 51.5060607
            assert lng == -0.0746535

            lat, lng = path[3]
            assert lat == 51.5060435
            assert lng == -0.073983

    @staticmethod
    def test_path_no_route():

        with patch('googlemaps.Client') as GoogleMapsClient:
            client = Mock()
            client.directions = MagicMock(return_value=[])
            GoogleMapsClient.return_value = client
            bot = create_mock_bot({
                "gmapkey": "abc123"
            })
            stepper = bot.stepper

            path_finder = GooglePathFinder(stepper)
            path = path_finder.path(51.5043872, -0.0741802, 51.5060435, -0.073983)

            assert len(path) == 1

            lat, lng = path[0]
            assert lat == 51.5060435
            assert lng == -0.073983

    @staticmethod
    def test_path_log():

        with patch('googlemaps.Client') as GoogleMapsClient:
            client = Mock()
            client.directions = MagicMock(return_value=[])
            GoogleMapsClient.return_value = client

            with patch('pokemongo_bot.logger') as logger:
                logger.log = MagicMock(return_value=None)

                bot = create_mock_bot({
                    "gmapkey": "abc123",
                    "debug": True
                })
                stepper = bot.stepper

                path_finder = GooglePathFinder(stepper)
                path = path_finder.path(51.5043872, -0.0741802, 51.5060435, -0.073983)

                assert len(path) == 1

                lat, lng = path[0]
                assert lat == 51.5060435
                assert lng == -0.073983
