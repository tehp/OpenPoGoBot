# -*- coding: utf-8 -*-

from __future__ import print_function
# pylint: disable=redefined-builtin
from builtins import bytes, str
import struct
import time

from api.worldmap import PokeStop
from colorama import init               # type: ignore
from geopy.distance import vincenty     # type: ignore

# Uncomment to enable type annotations for Python 3
# from typing import List
# from api.worldmap import Fort

init()


def distance(lat1, lon1, lat2, lon2):
    # type: (float, float, float, float) -> float
    return vincenty((lat1, lon1), (lat2, lon2)).meters


def filtered_forts(lat, lng, forts):
    # type: (float, float, List[Fort]) -> List[Fort]
    # pylint: disable=bad-continuation
    def should_keep(fort):
        return fort.fort_type == 1 and\
                isinstance(fort, PokeStop) and\
                fort.cooldown_complete_timestamp_ms < time.time() * 1000

    filtered_list = [(fort, distance(lat, lng, fort.latitude, fort.longitude)) for fort in forts if should_keep(fort)]
    return [x[0] for x in sorted(filtered_list, key=lambda y: y[1])]


def convert(original_distance, from_unit, to_unit):  # Converts units
    # type: (float, str, str) -> float
    # Example of converting distance from meters to feet:
    # convert(100.0,"m","ft")
    conversions = {
        "mm": {"mm": 1.0,
               "cm": 1.0 / 10.0,
               "m": 1.0 / 1000.0,
               "km": 1.0 / 1000000,
               "ft": 0.00328084,
               "yd": 0.00109361,
               "mi": 1.0 / 1609340.0007802},
        "cm": {"mm": 10.0,
               "cm": 1.0,
               "m": 1.0 / 100,
               "km": 1.0 / 100000,
               "ft": 0.0328084,
               "yd": 0.0109361,
               "mi": 1.0 / 160934.0},
        "m": {"mm": 1000,
              "cm": 100.0,
              "m": 1.0,
              "km": 1.0 / 1000.0,
              "ft": 3.28084,
              "yd": 1.09361,
              "mi": 1.0 / 1609.34},
        "km": {"mm": 100000,
               "cm": 10000.0,
               "m": 1000.0,
               "km": 1.0,
               "ft": 3280.84,
               "yd": 1093.61,
               "mi": 1.0 / 1.60934},
        "ft": {"mm": 1.0 / 328.084,
               "cm": 1.0 / 32.8084,
               "m": 1.0 / 3.28084,
               "km": 1 / 3280.84,
               "ft": 1.0,
               "yd": 1.0 / 3.0,
               "mi": 1.0 / 5280.0},
        "yd": {"mm": 1.0 / 328.084,
               "cm": 1.0 / 32.8084,
               "m": 1.0 / 3.28084,
               "km": 1 / 1093.61,
               "ft": 3.0,
               "yd": 1.0,
               "mi": 1.0 / 1760.0},
        "mi": {"mm": 1609340.0007802,
               "cm": 160934.0,
               "m": 1609.34,
               "km": 1.60934,
               "ft": 5280.0,
               "yd": 1760.0,
               "mi": 1.0}
    }
    return original_distance * conversions[from_unit][to_unit]


def dist_to_str(original_distance, unit):
    # type: (float, str) -> str
    return '{:.2f}{}'.format(original_distance, unit)


def format_dist(original_distance, unit):
    # type: (float, str) -> str
    # Assumes that distance is in meters and converts it to the given unit, then a formatted string is returned
    # Ex: format_dist(1500, 'km') returns the string "1.5km"
    return dist_to_str(convert(original_distance, 'm', unit), unit)


def format_time(seconds):
    # type: (float) -> str
    # Return a string displaying the time given as seconds or minutes
    if seconds <= 1.0:
        return '{:.2f} second'.format(seconds)
    elif seconds < 60:
        return '{:.2f} seconds'.format(seconds)
    elif seconds < 3600:
        minutes = seconds / 60
        return '{:.2f} minutes'.format(minutes)
    return '{:.2f} seconds'.format(seconds)


def i2f(input_int):
    # type: (int) -> float
    return struct.unpack('<d', struct.pack('<Q', input_int))[0]


def f2i(input_float):
    # type: (float) -> int
    return struct.unpack('<Q', struct.pack('<d', input_float))[0]


# pylint: disable=too-many-return-statements
def convert_to_utf8(data):
    if isinstance(data, bytes):
        return data.decode()
    elif isinstance(data, str):
        return str(data)
    elif isinstance(data, int):
        return int(data)
    elif isinstance(data, float):
        return float(data)
    elif isinstance(data, dict):
        return dict(map(convert_to_utf8, data.items()))
    elif isinstance(data, tuple):
        return tuple(map(convert_to_utf8, data))
    elif isinstance(data, list):
        return list(map(convert_to_utf8, data))
    elif isinstance(data, set):
        return set(map(convert_to_utf8, data))
