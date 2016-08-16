import unittest

from mock import Mock, call

from pokemongo_bot.stepper import Stepper
from pokemongo_bot.navigation.destination import Destination
from pokemongo_bot.navigation.path_finder import DirectPathFinder
from pokemongo_bot.navigation.path_finder import GooglePathFinder
from pokemongo_bot.tests import create_mock_api_wrapper, create_core_test_config


class StepperTest(unittest.TestCase):
    @staticmethod
    def test_init():
        config = create_core_test_config({
            "movement": {
                "walk_speed": 13.37,
            }
        })
        api_wrapper = create_mock_api_wrapper(config)
        path_finder = Mock()

        logger = Mock()
        logger.log = Mock(return_value=None)
        stepper = Stepper(config, api_wrapper, path_finder, logger)

        assert stepper.origin_lat is None
        assert stepper.origin_lng is None
        assert stepper.origin_alt is None

        assert stepper.current_lat is None
        assert stepper.current_lng is None
        assert stepper.current_alt is None

        assert stepper.speed == 13.37

    @staticmethod
    def test_init_no_walk():
        config = create_core_test_config({
            "movement": {
                "walk_speed": None,
            }
        })
        api_wrapper = create_mock_api_wrapper(config)
        path_finder = Mock()
        logger = Mock()
        logger.log = Mock(return_value=None)
        stepper = Stepper(config, api_wrapper, path_finder, logger)

        assert stepper.speed == 4.16

    @staticmethod
    def test_init_negative_walk():
        config = create_core_test_config({
            "movement": {
                "walk_speed": -5,
            }
        })
        api_wrapper = create_mock_api_wrapper(config)
        path_finder = Mock()
        logger = Mock()
        logger.log = Mock(return_value=None)
        stepper = Stepper(config, api_wrapper, path_finder, logger)

        assert stepper.speed == 4.16

    @staticmethod
    def test_init_path_finder_google():
        config = create_core_test_config({
            "movement": {
                "walk_speed": 4.16,
            }
        })
        api_wrapper = create_mock_api_wrapper(config)
        path_finder = GooglePathFinder(config, Mock())
        logger = Mock()
        logger.log = Mock(return_value=None)
        stepper = Stepper(config, api_wrapper, path_finder, logger)

        assert isinstance(stepper.path_finder, GooglePathFinder)

    @staticmethod
    def test_init_path_finder_direct():
        config = create_core_test_config({
            "movement": {
                "walk_speed": 4.16,
            }
        })
        api_wrapper = create_mock_api_wrapper(config)
        path_finder = DirectPathFinder(config)
        logger = Mock()
        logger.log = Mock(return_value=None)
        stepper = Stepper(config, api_wrapper, path_finder, logger)

        assert isinstance(stepper.path_finder, DirectPathFinder)

    @staticmethod
    def test_start():
        config = create_core_test_config({
            "movement": {
                "walk_speed": 4.16,
            }
        })
        api_wrapper = create_mock_api_wrapper(config)
        path_finder = DirectPathFinder(config)
        logger = Mock()
        logger.log = Mock(return_value=None)
        stepper = Stepper(config, api_wrapper, path_finder, logger)

        stepper.start(51.5044524, -0.0752479, 10)

        assert stepper.origin_lat == 51.5044524
        assert stepper.origin_lng == -0.0752479
        assert stepper.origin_alt == 10

        assert stepper.current_lat == 51.5044524
        assert stepper.current_lng == -0.0752479
        assert stepper.current_alt == 10

        pgo = api_wrapper.get_api()
        lat, lng, alt = pgo.get_position()

        assert lat == 51.5044524
        assert lng == -0.0752479
        assert alt == 10

    @staticmethod
    def test_get_route_between():
        config = create_core_test_config({
            "movement": {
                "walk_speed": 5,
            }
        })
        api_wrapper = create_mock_api_wrapper(config)
        path_finder = DirectPathFinder(config)
        logger = Mock()
        logger.log = Mock(return_value=None)
        stepper = Stepper(config, api_wrapper, path_finder, logger)
        stepper.start(51.5044524, -0.0752479, 10)

        # pre-calculated distance is 205.5 meters
        # expected steps is 205.5 / (0.6 * 5) = 68.5 (which rounds to 69)
        steps = stepper.get_route_between(51.5044524, -0.0752479, 51.5062939, -0.0750065, 10)

        assert len(steps) == 69

        for step in steps:
            assert len(step) == 3

    @staticmethod
    def test_snap_to():
        config = create_core_test_config({
            "movement": {
                "walk_speed": 5,
            }
        })
        api_wrapper = create_mock_api_wrapper(config)
        path_finder = DirectPathFinder(config)
        logger = Mock()
        logger.log = Mock(return_value=None)
        stepper = Stepper(config, api_wrapper, path_finder, logger)

        stepper.start(51.5043945, -0.0760622, 10)

        # pre-calculated distance is 10.3 meters
        stepper.snap_to(51.504389, -0.07621, 11)

        pgo = api_wrapper.get_api()
        lat, lng, alt = pgo.get_position()

        assert stepper.current_lat == 51.504389
        assert stepper.current_lng == -0.07621
        assert stepper.current_alt == 11
        assert lat == 51.504389
        assert lng == -0.07621
        assert alt == 11

    @staticmethod
    def test_snap_to_over_distance():
        config = create_core_test_config({
            "movement": {
                "walk_speed": 5,
            }
        })
        api_wrapper = create_mock_api_wrapper(config)
        path_finder = DirectPathFinder(config)
        logger = Mock()
        logger.log = Mock(return_value=None)
        stepper = Stepper(config, api_wrapper, path_finder, logger)
        stepper.start(51.50451, -0.07607, 10)

        # pre-calculated distance is 17.8 meters
        stepper.snap_to(51.50436, -0.07616, 11)

        pgo = api_wrapper.get_api()
        lat, lng, alt = pgo.get_position()

        assert stepper.current_lat == 51.50451
        assert stepper.current_lng == -0.07607
        assert stepper.current_alt == 10
        assert lat == 51.50451
        assert lng == -0.07607
        assert alt == 10

    @staticmethod
    def test_step():
        config = create_core_test_config({
            "movement": {
                "walk_speed": 5,
                "path_finder": "direct",
                "distance_unit": "m"
            }
        })
        api_wrapper = create_mock_api_wrapper(config)
        path_finder = DirectPathFinder(config)
        logger = Mock()
        logger.log = Mock(return_value=None)
        stepper = Stepper(config, api_wrapper, path_finder, logger)
        stepper.start(51.50451, -0.07607, 10)

        destination = Destination(51.506000, -0.075049, 11, name="Test Destination", exact_location=False)
        steps = [
            (51.504778, -0.075838, 10),
            (51.505092, -0.075650, 11),
            (51.505436, -0.075446, 11)
        ]
        destination.set_steps(steps)

        pgo = api_wrapper.get_api()

        # This route is being walked: http://www.darrinward.com/lat-long/?id=2163411
        # pre-calculated distance is 17.8 meters
        pointer = 0
        for _ in stepper.step(destination):
            target_lat, target_lng, target_alt = steps[pointer]
            assert stepper.current_lat == target_lat
            assert stepper.current_lng == target_lng
            assert stepper.current_alt == target_alt

            bot_lat, bot_lng, bot_alt = pgo.get_position()
            assert bot_lat == target_lat
            assert bot_lng == target_lng
            assert bot_alt == target_alt

            pointer += 1

        assert pointer == 3

        bot_lat, bot_lng, bot_alt = pgo.get_position()
        assert bot_lat == 51.505436
        assert bot_lng == -0.075446
        assert bot_alt == 11
        assert stepper.current_lat == 51.505436
        assert stepper.current_lng == -0.075446
        assert stepper.current_alt == 11

    @staticmethod
    def test_step_already_near_fort():
        calls = []
        config = create_core_test_config({
            "movement": {
                "walk_speed": 5,
                "path_finder": "direct",
                "distance_unit": "m"
            }
        })
        api_wrapper = create_mock_api_wrapper(config)
        path_finder = DirectPathFinder(config)

        destination = Destination(51.50436, -0.07616, 11, name="Test Destination", exact_location=False)
        steps = [
            (51.50442, -0.07612, 10),
            (51.50448, -0.07609, 11),
            (51.50436, -0.07616, 11)
        ]
        destination.set_steps(steps)

        logger = Mock()
        logger.log = Mock(return_value=None)
        stepper = Stepper(config, api_wrapper, path_finder, logger)
        stepper.start(51.50451, -0.07607, 10)

        pgo = api_wrapper.get_api()

        # This route is being walked: http://www.darrinward.com/lat-long/?id=2163408
        calls.append(call("walking_started", coords=(51.50436, -0.07616, 11)))
        pointer = 0
        for _ in stepper.step(destination):
            pointer += 1

        assert pointer == 0

        bot_lat, bot_lng, bot_alt = pgo.get_position()
        assert bot_lat == 51.50451
        assert bot_lng == -0.07607
        assert bot_alt == 10
        assert stepper.current_lat == 51.50451
        assert stepper.current_lng == -0.07607
        assert stepper.current_alt == 10
