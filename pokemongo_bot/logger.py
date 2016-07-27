from __future__ import print_function
import time

from pokemongo_bot.event_manager import manager
try:
    #pylint: disable=import-error
    import lcd
    LCD = lcd.lcd()
    # Change this to your i2c address
    LCD.set_addr(0x23)
except ImportError:
    LCD = None


def log(string, color='black', fire_event=True):
    color_hex = {
        'green': '92m',
        'yellow': '93m',
        'red': '91m'
    }
    string = string.decode("utf-8")
    if fire_event:
        manager.fire("logging", output=string, color=color)
    output = '[' + time.strftime("%Y-%m-%d %H:%M:%S") + '] ' + string
    if color in color_hex:
        output = u"\033[" + color_hex[color] + output + "\033[0m"
    print(output)
    if LCD is not None and string is not None:
        LCD.message(string)
