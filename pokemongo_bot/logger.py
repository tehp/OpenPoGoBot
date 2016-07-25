from __future__ import print_function
import time
try:
    #pylint: disable=import-error
    import lcd
    LCD = lcd.lcd()
    # Change this to your i2c address
    LCD.set_addr(0x23)
except ImportError:
    LCD = None


def log(string, color='white'):
    color_hex = {
        'green': '92m',
        'yellow': '93m',
        'red': '91m'
    }
    if color not in color_hex:
        print('[' + time.strftime("%Y-%m-%d %H:%M:%S") + '] ' + string)
    else:
        print(u'\033[' + color_hex[color] + "[" + time.strftime("%Y-%m-%d %H:%M:%S") + '] ' + string.decode('utf-8') + '\033[0m')
    if LCD is not None and string is not None:
        LCD.message(string)
