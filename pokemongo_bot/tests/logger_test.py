import unittest
import sys
from io import StringIO

from mock import Mock

import pokemongo_bot


class LoggerTest(unittest.TestCase):
    def setUp(self):
        self.out = StringIO()
        sys.stdout = self.out

    @staticmethod
    def test_log_by_event():
        pokemongo_bot.event_manager.manager.fire = Mock()

        pokemongo_bot.logger.log("log row", color="yellow", prefix="test", fire_event=True)

        pokemongo_bot.event_manager.manager.fire.assert_called_once_with("logging", text="log row", color="yellow", prefix="test")

    def test_log_by_call(self):
        pokemongo_bot.logger.log("log row", color="yellow", prefix="test", fire_event=False)

        output = self.out.getvalue().strip()
        assert "[test] log row" in output
