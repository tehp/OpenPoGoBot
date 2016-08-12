from __future__ import print_function
import unittest

from mock import Mock, patch

import pokemongo_bot
from pokemongo_bot.event_manager import manager

class LoggerTest(unittest.TestCase):

    @staticmethod
    def test_log_by_event():

        manager.fire = Mock()

        pokemongo_bot.logger.log("log row", color="yellow", prefix="test", fire_event=True)

        manager.fire.assert_called_once_with("logging", text="log row", color="yellow", prefix="test")

    @staticmethod
    def test_log_by_call():
        import sys
        from io import StringIO
        out = StringIO()
        sys.stdout = out

        pokemongo_bot.logger.log("log row", color="yellow", prefix="test", fire_event=False)
        output = out.getvalue().strip()
        assert "[test] log row" in output
