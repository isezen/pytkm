#!/usr/bin/python # noqa
# -*- coding: utf-8 -*-
# pylint: disable=C0103, W0212
"""Test module for tkm.py"""

import tkm  # pylint: disable=E0401
from datetime import datetime

_URL_MAIN = 'http://tkm.ibb.gov.tr'
_URL_NOT_FOUND = _URL_MAIN + '/notfound.html'
_URL_STATIC_FILE = _URL_MAIN + '/YHarita/res/r0.txt'
_URL_TRAFFIC_INDX = _URL_MAIN + '/data/IntensityMap/TrafficIndex.aspx'
_E_TAG = tkm._now().strftime('%Y%m%d')


def _get_diff(x, y):
    """ Internal function. """
    from itertools import compress
    x = ''.join(set(x))
    r = list(compress(x, [i not in y for i in x]))
    if len(r):
        s = ','.join('[{0}]'.format(i) for i in r)
        raise ValueError(u"str_list requires -> %s" % s)


def test_tkm_add_e_tag():
    """Test _add_e_tag function. """
    a = tkm._add_e_tag('abc', '123')
    assert a == 'abc.123'


def test_static_file():
    """Test _get_data against static file download. """
    url = tkm.URL.road[0]
    ret = tkm._urlopen(url)
    a, b, c, d = tkm._get_data(ret)
    assert isinstance(a, datetime)
    assert isinstance(b, str)
    assert isinstance(c, str)
    assert ['r0', b, 'txt'] == c.split('.')
    assert isinstance(d, str)


def test_tkm_urlopen():
    """Test _urlopen function. """
    a, b, c, d = tkm._urlopen(_URL_TRAFFIC_INDX)
    assert a.__class__.__name__ == 'addinfourl'
    assert isinstance(b, datetime)
    assert c is None
    assert d.__class__.__name__ == 'str'
    assert ['TrafficIndex', _E_TAG, 'csv'] == d.split('.')

    a, b, c, d = tkm._urlopen(_URL_STATIC_FILE)
    assert a.__class__.__name__ == 'addinfourl'
    assert isinstance(b, datetime)
    assert isinstance(c, str)
    assert isinstance(d, str)

    a, b, c, d = tkm._urlopen(_URL_NOT_FOUND)
    assert a is None
    assert isinstance(b, datetime)
    assert c is None
    assert ['notfound', _E_TAG, 'csv'] == d.split('.')


def test_tkm_get_filename_with_e_tag():
    """Test _get_filename_with_e_tag function. """
    a, b = tkm._get_filename_with_e_tag(_URL_STATIC_FILE)
    assert isinstance(a, str)
    assert isinstance(b, datetime)


def test_get_data():
    """Test _get_data function. """
    a, b, c, d = tkm._get_data(_URL_NOT_FOUND)
    assert a == -1
    assert b is None
    assert ['notfound', _E_TAG, 'csv'] == c.split('.')
    assert d == 'NA'


def test_get_traffic_index():
    """Test get_traffic_index function. """
    a, b, c, d = tkm.get_traffic_index()
    assert a == -1
    assert b is None
    assert ['TrafficIndex', _E_TAG, 'csv'] == c.split('.')
    assert isinstance(d, str)


def test_get_traffic_data():
    """Test get_traffic_data function."""
    a, b, c, d = tkm.get_traffic_data()
    assert a == -1
    assert b is None
    assert ['TrafficDataNew', _E_TAG, 'csv'] == c.split('.')
    assert isinstance(d, str)
    assert all(i in '0123456789|&' for i in d)


def test_get_parking_data():
    """Test get_parking_data function."""
    a, b, c, d = tkm.get_parking_data()
    assert a == -1
    assert b is None
    assert ['ParkingLotData', _E_TAG, 'csv'] == c.split('.')
    assert isinstance(d, str)
    assert all(i in '0123456789&-~.: ' for i in d)


def test_get_announcements():
    """Test get_announcements function."""
    a, b, c, d = tkm.get_announcements()
    assert a == -1
    assert b is None
    assert ['AnnouncementData', _E_TAG, 'csv'] == c.split('.')
    assert isinstance(d, str)

    str_list = 'abcçdefgğhıijklmnoöprsştuüvwxyz' + \
               'ABCÇDEFGĞHIİJKLMNOÖPRSŞTUÜVWXYZ 0123456789-_:.,&|!\'()/%\n'
    _get_diff(d, str_list)


def test_get_weather_data():
    """Test get_weather_data function."""
    # get uniq chars -> ''.join(set(d))
    a, b, c, d = tkm.get_weather_data()
    assert a == -1
    assert b is None
    assert ['WeatherData', _E_TAG, 'csv'] == c.split('.')
    assert isinstance(d, str)
    str_list = 'abcçdefgğhıijklmnoöprsştuüvyz' + \
               'ABCÇDEFGĞHIİJKLMNOÖPRSŞTUÜVYZ 0123456789-:.,&|'
    _get_diff(d, str_list)
