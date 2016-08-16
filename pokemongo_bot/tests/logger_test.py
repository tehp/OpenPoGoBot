from __future__ import print_function
import unittest

from mock import Mock

import pokemongo_bot
from pokemongo_bot import EventManager
from pokemongo_bot import Logger


class LoggerTest(unittest.TestCase):
    @staticmethod
    def test_log_by_event():
        event_manager = EventManager()
        logger = Logger(event_manager)

        event_manager.fire = Mock()

        logger.log("log row", color="yellow", prefix="test", fire_event=True)

        event_manager.fire.assert_called_once_with("logging", text="log row", color="yellow", prefix="test")

    @staticmethod
    def test_log_by_call():
        import sys
        from io import StringIO
        out = StringIO()
        sys.stdout = out

        logger = Logger(Mock())

        logger.log("log row", color="yellow", prefix="test", fire_event=False)
        output = out.getvalue().strip()
        assert "[test] log row" in output
