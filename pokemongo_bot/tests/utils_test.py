import unittest
import sys
from io import StringIO

from mock import Mock

import pokemongo_bot
from api.worldmap import PokeStop, Gym

from pokemongo_bot.utils import distance, filtered_forts, convert, dist_to_str, format_dist, format_time, f2i, i2f, \
    convert_to_utf8


class UtilsTest(unittest.TestCase):
    def setUp(self):
        self.out = StringIO()
        sys.stdout = self.out

    @staticmethod
    def test_distance():
        dist = distance(51.503056, -0.119500, 51.503635, -0.119337)

        assert round(dist, 2) == 65.41

    def test_filtered_forts(self):

        forts = [
            self._create_fort("pokestop", "test_1", 51.50204, -0.11955),
            self._create_fort("pokestop", "test_2", 51.503342, -0.119668),
            self._create_fort("pokestop", "test_3", 51.504250, -0.117458),
            self._create_fort("gym", "test_4", 51.503602, -0.118756)
        ]

        returned_forts = filtered_forts(51.503056, -0.119500, forts)

        assert len(returned_forts) == 3
        assert returned_forts[0].fort_name == 'test_2'
        assert returned_forts[1].fort_name == 'test_1'
        assert returned_forts[2].fort_name == 'test_3'

    @staticmethod
    def test_convert():
        assert (convert(10000.0, "mm", "mm")) == 10000.0
        assert (convert(10000.0, "mm", "cm")) == 1000.0
        assert (convert(10000.0, "mm", "m")) == 10.0
        assert (convert(10000.0, "mm", "km")) == 0.01
        assert round((convert(10000.0, "mm", "ft")), 5) == 32.8084
        assert round((convert(10000.0, "mm", "yd")), 5) == 10.93610
        assert round((convert(10000.0, "mm", "mi")), 5) == 0.00621

        assert (convert(1000.0, "cm", "mm")) == 10000.0
        assert (convert(1000.0, "cm", "cm")) == 1000.0
        assert (convert(1000.0, "cm", "m")) == 10.0
        assert (convert(1000.0, "cm", "km")) == 0.01
        assert round((convert(1000.0, "cm", "ft")), 5) == 32.8084
        assert round((convert(1000.0, "cm", "yd")), 5) == 10.93610
        assert round((convert(1000.0, "cm", "mi")), 5) == 0.00621

        assert (convert(10.0, "m", "mm")) == 10000.0
        assert (convert(10.0, "m", "cm")) == 1000.0
        assert (convert(10.0, "m", "m")) == 10.0
        assert (convert(10.0, "m", "km")) == 0.01
        assert round((convert(10.0, "m", "ft")), 5) == 32.8084
        assert round((convert(10.0, "m", "yd")), 5) == 10.93610
        assert round((convert(10.0, "m", "mi")), 5) == 0.00621

        assert (convert(0.01, "km", "mm")) == 10000.0
        assert (convert(0.01, "km", "cm")) == 1000.0
        assert (convert(0.01, "km", "m")) == 10.0
        assert (convert(0.01, "km", "km")) == 0.01
        assert round((convert(0.01, "km", "ft")), 5) == 32.8084
        assert round((convert(0.01, "km", "yd")), 5) == 10.93610
        assert round((convert(0.01, "km", "mi")), 5) == 0.00621

        assert round((convert(32.8084, "ft", "mm")), 1) == 10000.0
        assert round((convert(32.8084, "ft", "cm")), 1) == 1000.0
        assert round((convert(32.8084, "ft", "m")), 1) == 10.0
        assert round((convert(32.8084, "ft", "km")), 2) == 0.01
        assert round((convert(32.8084, "ft", "ft")), 5) == 32.8084
        assert round((convert(32.8084, "ft", "yd")), 5) == 10.93613
        assert round((convert(32.8084, "ft", "mi")), 5) == 0.00621

        assert round((convert(10.93613312, "yd", "mm")), 1) == 10000.0
        assert round((convert(10.93613312, "yd", "cm")), 1) == 1000.0
        assert round((convert(10.93613312, "yd", "m")), 1) == 10.0
        assert round((convert(10.93613312, "yd", "km")), 2) == 0.01
        assert round((convert(10.93613312, "yd", "ft")), 5) == 32.80840
        assert round((convert(10.93613312, "yd", "yd")), 5) == 10.93613
        assert round((convert(10.93613312, "yd", "mi")), 5) == 0.00621

        assert round((convert(0.006213712, "mi", "mm")), 1) == 10000.0
        assert round((convert(0.006213712, "mi", "cm")), 1) == 1000.0
        assert round((convert(0.006213712, "mi", "m")), 1) == 10.0
        assert round((convert(0.006213712, "mi", "km")), 2) == 0.01
        assert round((convert(0.006213712, "mi", "ft")), 5) == 32.80840
        assert round((convert(0.006213712, "mi", "yd")), 5) == 10.93613
        assert round((convert(0.006213712, "mi", "mi")), 5) == 0.00621

    @staticmethod
    def test_dist_to_str():
        return_value = dist_to_str(123.123, 'km')

        assert return_value == "123.12km"

    @staticmethod
    def test_format_dist():
        assert (format_dist(1.234567, 'mm')) == "1234.57mm"
        assert (format_dist(1.234567, 'cm')) == "123.46cm"
        assert (format_dist(1.234567, 'm')) == "1.23m"
        assert (format_dist(123.4567, 'km')) == "0.12km"

        assert (format_dist(123.4567, 'ft')) == "405.04ft"
        assert (format_dist(123.4567, 'yd')) == "135.01yd"
        assert (format_dist(1234.567, 'mi')) == "0.77mi"

    @staticmethod
    def test_format_time():
        assert (format_time(0.123)) == "0.12 second"
        assert (format_time(12.345)) == "12.35 seconds"
        assert (format_time(123.456)) == "2.06 minutes"
        assert (format_time(123.456)) == "2.06 minutes"
        assert (format_time(12345.678)) == "12345.68 seconds"

    @staticmethod
    def test_f2i():
        assert (f2i(51.503315)) == 4632445264504572682
        assert (f2i(-0.119421)) == 13816641647455544128

    @staticmethod
    def test_i2f():
        assert (i2f(4632445264504572682)) == 51.503315
        assert (i2f(13816641647455544128)) == -0.119421

    @staticmethod
    def test_convert_to_utf8():
        assert (convert_to_utf8(b'hello')) == "hello"
        assert (convert_to_utf8(u'hello')) == "hello"
        assert (convert_to_utf8(123)) == 123
        assert (convert_to_utf8(123.456)) == 123.456
        assert (convert_to_utf8({'key': b'value'})) == {'key': 'value'}
        assert (convert_to_utf8((b'value', u'uvalue'))) == ('value', 'uvalue')
        assert (convert_to_utf8(list((b'value', u'uvalue')))) == list(('value', 'uvalue'))
        assert (convert_to_utf8(set((b'value', u'uvalue')))) == set(('value', 'uvalue'))

    @staticmethod
    def _create_fort(fort_type, name, lat, lng):
        if fort_type == 'gym':
            return Gym({
                "id": "gym_" + str(name),
                "name": str(name),
                "latitude": lat,
                "longitude": lng,
            })
        else:
            return PokeStop({
                "id": "pokestop_" + str(name),
                "name": str(name),
                "latitude": lat,
                "longitude": lng,
            })
