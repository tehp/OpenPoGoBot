import unittest

from mock import Mock, call

from pokemongo_bot import Stepper
from pokemongo_bot.navigation.destination import Destination
from pokemongo_bot.navigation.path_finder import DirectPathFinder
from pokemongo_bot.navigation.path_finder import GooglePathFinder
from pokemongo_bot.tests import create_mock_bot


class StepperTest(unittest.TestCase):
    @staticmethod
    def test_init():
        bot = create_mock_bot({
            "walk": 13.37,
        })

        bot.position = (51.5044524, -0.0752479, 10)
        stepper = Stepper(bot)

        assert stepper.speed == 13.37

        assert stepper.origin_lat == 51.5044524
        assert stepper.origin_lng == -0.0752479
        assert stepper.origin_alt == 10

        assert stepper.current_lat == 51.5044524
        assert stepper.current_lng == -0.0752479
        assert stepper.current_alt == 10

    @staticmethod
    def test_init_no_walk():
        bot = create_mock_bot({
            "walk": None,
        })

        stepper = Stepper(bot)

        assert stepper.speed == 4.16

    @staticmethod
    def test_init_negative_walk():
        bot = create_mock_bot({
            "walk": -5,
        })

        stepper = Stepper(bot)

        assert stepper.speed == 4.16

    @staticmethod
    def test_init_path_finder_google():
        bot = create_mock_bot({
            "walk": None,
            "path_finder": "google"
        })

        stepper = Stepper(bot)

        assert isinstance(stepper.path_finder, GooglePathFinder)

    @staticmethod
    def test_init_path_finder_direct():
        bot = create_mock_bot({
            "walk": None,
            "path_finder": "direct"
        })

        stepper = Stepper(bot)

        assert isinstance(stepper.path_finder, DirectPathFinder)

    @staticmethod
    def test_start():
        bot = create_mock_bot({
            "walk": None,
            "path_finder": "direct"
        })
        bot.position = (51.5044524, -0.0752479, 10)

        stepper = Stepper(bot)
        stepper.start()

        pgo = bot.api_wrapper._api  # pylint: disable=protected-access
        lat, lng, alt = pgo.get_position()

        assert lat == 51.5044524
        assert lng == -0.0752479
        assert alt == 10

    @staticmethod
    def test_get_route_between():
        bot = create_mock_bot({
            "walk": 5,
            "path_finder": "direct"
        })
        bot.position = (51.5044524, -0.0752479, 10)

        stepper = Stepper(bot)
        stepper.start()

        # pre-calculated distance is 205.5 meters
        # expected steps is 205.5 / (0.6 * 5) = 68.5 (which rounds to 69)
        steps = stepper.get_route_between(51.5044524, -0.0752479, 51.5062939, -0.0750065, 10)

        assert len(steps) == 69

        for step in steps:
            assert len(step) == 3

    @staticmethod
    def test_snap_to():
        bot = create_mock_bot({
            "walk": 5,
            "path_finder": "direct"
        })
        bot.position = (51.5043945, -0.0760622, 10)
        bot.fire = Mock(return_value=None)
        bot.heartbeat = Mock(return_value=None)

        stepper = Stepper(bot)
        stepper.start()

        # pre-calculated distance is 10.3 meters
        stepper.snap_to(51.504389, -0.07621, 11)

        pgo = bot.api_wrapper._api  # pylint: disable=protected-access
        lat, lng, alt = pgo.get_position()

        assert stepper.current_lat == 51.504389
        assert stepper.current_lng == -0.07621
        assert stepper.current_alt == 11
        assert lat == 51.504389
        assert lng == -0.07621
        assert alt == 11

        bot.fire.assert_called_once()
        bot.heartbeat.assert_called_once()

    @staticmethod
    def test_snap_to_over_distance():
        bot = create_mock_bot({
            "walk": 5,
            "path_finder": "direct"
        })
        bot.position = (51.50451, -0.07607, 10)
        bot.fire = Mock(return_value=None)
        bot.heartbeat = Mock(return_value=None)

        stepper = Stepper(bot)
        stepper.start()

        # pre-calculated distance is 17.8 meters
        stepper.snap_to(51.50436, -0.07616, 11)

        pgo = bot.api_wrapper._api  # pylint: disable=protected-access
        lat, lng, alt = pgo.get_position()

        assert stepper.current_lat == 51.50451
        assert stepper.current_lng == -0.07607
        assert stepper.current_alt == 10
        assert lat == 51.50451
        assert lng == -0.07607
        assert alt == 10

        assert bot.fire.call_count == 0
        assert bot.heartbeat.call_count == 0

    @staticmethod
    def test_step():
        calls = []
        bot = create_mock_bot({
            "walk": 5,
            "path_finder": "direct",
            "distance_unit": "m"
        })
        bot.position = (51.50451, -0.07607, 10)
        bot.fire = Mock(return_value=None)
        bot.heartbeat = Mock(return_value=None)

        destination = Destination(51.50436, -0.07616, 11, name="Test Destination", exact_location=False)
        steps = [
            (51.50442, -0.07612, 10),
            (51.50448, -0.07609, 11),
            (51.50436, -0.07616, 11)
        ]
        destination.set_steps(steps)

        stepper = Stepper(bot)
        stepper.start()

        pgo = bot.api_wrapper._api  # pylint: disable=protected-access

        calls.append(call("walking_started", coords=(51.50436, -0.07616, 11)))
        # pre-calculated distance is 17.8 meters
        pointer = 0
        for step in stepper.step(destination):
            calls.append(call("position_updated", coordinates=step))

            target_lat, target_lng, target_alt = steps[pointer]
            assert stepper.current_lat == target_lat
            assert stepper.current_lng == target_lng
            assert stepper.current_alt == target_alt

            bot_lat, bot_lng, bot_alt = pgo.get_position()
            assert bot_lat == target_lat
            assert bot_lng == target_lng
            assert bot_alt == target_alt

            pointer += 1

        calls.append(call("walking_finished", coords=(51.50436, -0.07616, 11)))

        assert bot.fire.call_count == 5
        bot.fire.assert_has_calls(calls, any_order=False)

        assert bot.heartbeat.call_count == 3
