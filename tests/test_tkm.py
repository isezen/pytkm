#!/usr/bin/python # noqa
# -*- coding: utf-8 -*-
# pylint: disable=W0212
"""Test module for tkm.py"""

import tkm # pylint: disable=E0401
from datetime import datetime

_url_main = 'http://tkm.ibb.gov.tr'
_url_not_found = _url_main + '/notfound.html'
_url_static_file = _url_main + '/YHarita/res/r0.txt'
_url_traffic_indx = _url_main + '/data/IntensityMap/TrafficIndex.aspx'
_e_tag = tkm._now().strftime('%Y%m%d')


def get_diff(x, y):
    from itertools import compress
    x = ''.join(set(x))
    r = list(compress(x, [i not in y for i in x]))
    if len(r):
        s = ','.join('[{0}]'.format(i) for i in r)
        raise ValueError(u"str_list requires -> %s" % s)


def test_tkm_add_e_tag():
    a = tkm._add_e_tag('abc', '123')
    assert a == 'abc.123'

def test_static_file():
    url = tkm.URL.road[0]
    ret = tkm._urlopen(url)
    a, b, c, d = tkm._get_data(ret)
    assert isinstance(a, datetime)
    assert isinstance(b, str)
    assert isinstance(c, str)
    assert ['r0', b, 'txt'] == c.split('.')
    assert isinstance(d, str)


def test_tkm_urlopen():
    a, b, c, d = tkm._urlopen(_url_traffic_indx)
    assert a.__class__.__name__ == 'addinfourl'
    assert isinstance(b, datetime)
    assert c is None
    assert d.__class__.__name__ == 'str'
    assert ['TrafficIndex', _e_tag, 'csv'] == d.split('.')

    a, b, c, d = tkm._urlopen(_url_static_file)
    assert a.__class__.__name__ == 'addinfourl'
    assert isinstance(b, datetime)
    assert isinstance(c, str)
    assert isinstance(d, str)

    a, b, c, d = tkm._urlopen(_url_not_found)
    assert a is None
    assert isinstance(b, datetime)
    assert c is None
    assert ['notfound', _e_tag, 'csv'] == d.split('.')


def test_tkm_get_filename_with_e_tag():
    a, b = tkm._get_filename_with_e_tag(_url_static_file)
    assert isinstance(a, str)
    assert isinstance(b, datetime)


def test_get_data():
    a, b, c, d = tkm._get_data(_url_not_found)
    assert a == -1
    assert b is None
    assert ['notfound', _e_tag, 'csv'] == c.split('.')
    assert d == 'NA'


def test_get_traffic_index():
    a, b, c, d = tkm.get_traffic_index()
    assert a == -1
    assert b is None
    assert ['TrafficIndex', _e_tag, 'csv'] == c.split('.')
    assert isinstance(d, str)


def test_get_traffic_data():
    a, b, c, d = tkm.get_traffic_data()
    assert a == -1
    assert b is None
    assert ['TrafficDataNew', _e_tag, 'csv'] == c.split('.')
    assert isinstance(d, str)
    assert all(i in '0123456789|&' for i in d)


def test_get_parking_data():
    a, b, c, d = tkm.get_parking_data()
    assert a == -1
    assert b is None
    assert ['ParkingLotData', _e_tag, 'csv'] == c.split('.')
    assert isinstance(d, str)
    assert all(i in '0123456789&-~.: ' for i in d)


def test_get_announcements():
    a, b, c, d = tkm.get_announcements()
    assert a == -1
    assert b is None
    assert ['AnnouncementData', _e_tag, 'csv'] == c.split('.')
    assert isinstance(d, str)

    str_list = 'abcçdefgğhıijklmnoöprsştuüvwxyz' + \
               'ABCÇDEFGĞHIİJKLMNOÖPRSŞTUÜVWXYZ 0123456789-_:.,&|!\'()/%\n'
    get_diff(d, str_list)


def test_get_weather_data():
    # get uniq chars -> ''.join(set(d))
    a, b, c, d = tkm.get_weather_data()
    assert a == -1
    assert b is None
    assert ['WeatherData', _e_tag, 'csv'] == c.split('.')
    assert isinstance(d, str)
    str_list = 'abcçdefgğhıijklmnoöprsştuüvyz' + \
               'ABCÇDEFGĞHIİJKLMNOÖPRSŞTUÜVYZ 0123456789-:.,&|'
    get_diff(d, str_list)
