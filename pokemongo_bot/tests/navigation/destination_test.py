import unittest

from pokemongo_bot.navigation.destination import Destination


class DestinationNavigatorTest(unittest.TestCase):
    @staticmethod
    def test_init():
        destination = Destination(1, 2, 0, name="test_destination", exact_location=False)
        assert destination.target_lat == 1
        assert destination.target_lng == 2
        assert destination.target_alt == 0
        assert destination.name == "test_destination"
        assert destination.exact_location is False

    @staticmethod
    def test_set_steps():
        destination = Destination(1, 2, 0, name="test_destination", exact_location=False)

        destination.set_steps([
            (1, 2, 0),
            (2, 3, 0),
            (3, 4, 0)
        ])

        assert destination.get_step_count() == 3

    @staticmethod
    def test_step():
        destination = Destination(1, 2, 0, name="test_destination", exact_location=False)

        steps = [
            (1, 2, 0),
            (2, 3, 0),
            (3, 4, 0)
        ]
        destination.set_steps(steps)

        step_values = []
        for step in destination.step():
            assert step in steps
            step_values.append(step)

        assert len(step_values) == 3

    @staticmethod
    def test_step_exact():
        destination = Destination(4, 5, 6, name="test_destination", exact_location=True)

        steps = [
            (1, 2, 0),
            (2, 3, 0),
            (3, 4, 0)
        ]
        destination.set_steps(steps)

        step_values = []
        for step in destination.step():
            if len(step_values) < 3:
                assert step in steps
            else:
                assert step == (4, 5, 6)
            step_values.append(step)

        assert len(step_values) == 4
