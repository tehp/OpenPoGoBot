# pylint: disable=redefined-builtin
from __future__ import print_function
from builtins import str
import time

from colorama import Fore, Back, Style

from app import kernel
from pokemongo_bot.event_manager import EventManager


@kernel.container.register('logger', ['@event_manager'])
class Logger(object):
    def __init__(self, event_manager):
        # type: (EventManager) -> None
        self._event_manager = event_manager
        self._event_manager.add_listener('logging', self._log)

    def log(self, string, color='black', prefix=None, fire_event=True):
        # type: (str, Optional[str], Optional[str], Optional[bool]) -> None
        if fire_event:
            self._event_manager.fire('logging', text=string, color=color, prefix=prefix)
        else:
            self._log(text=string, color=color, prefix=prefix)

    @staticmethod
    def _log(text='', color='black', prefix=None):
        # type: (str, Optional[str], Optional[str]) -> None
        color_hex = {
            'green': Fore.GREEN,
            'yellow': Fore.YELLOW,
            'red': Fore.RED
        }
        string = str(text)
        output = u'[' + time.strftime('%Y-%m-%d %H:%M:%S') + u'] '
        if prefix is not None:
            output += u'[{}] '.format(str(prefix))
        output += string
        if color in color_hex:
            output = color_hex[color] + output + Style.RESET_ALL
        print(output)
