# -*- coding: utf-8 -*-

import time
from math import ceil
from random import random, randint


def sleep(seconds, delta=0.3):
    jitter = ceil(delta * seconds)
    sleep_time = randint(int(seconds - jitter), int(seconds + jitter))
    time.sleep(sleep_time)


def random_lat_long_delta(factor=10):
    # Return random value from [-.000001 * factor, .000001 * factor].
    # Example: Since 364,000 feet is equivalent to one degree of latitude, a factor of 10 means this
    # should be 364,000 * .000010 = 3.64. So it returns between [-3.64, 3.64]
    return ((random() * 0.000001) * factor * 2) - (factor * 0.000001)
