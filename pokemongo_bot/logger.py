# pylint: disable=redefined-builtin
from __future__ import print_function
from builtins import str
import time

from colorama import init, Fore, Back, Style
from pokemongo_bot.event_manager import manager

# Uncomment for type annotations on Python 3
# from typing import Optional

init()

try:
    # pylint: disable=import-error
    import lcd  # type: ignore

    LCD = lcd.lcd()
    # Change this to your i2c address
    LCD.set_addr(0x23)
except ImportError:
    LCD = None


def log(string, color='black', fire_event=True):
    # type: (str, Optional[str], Optional[bool]) -> None
    color_hex = {
        'green': Fore.GREEN,
        'yellow': Fore.YELLOW,
        'red': Fore.RED
    }
    string = str(string)
    if fire_event:
        manager.fire("logging", output=string, color=color)
    output = u"[" + time.strftime("%Y-%m-%d %H:%M:%S") + u"] " + string
    if color in color_hex:
        output = color_hex[color] + output + Style.RESET_ALL
    print(output)
    if LCD is not None and string is not None:
        LCD.message(string)
