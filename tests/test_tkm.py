#!/usr/bin/python # noqa
# -*- coding: utf-8 -*-
# pylint: disable=W0212
"""Test module for tkmdecrypt.py"""

import tkm # pylint: disable=E0401
from datetime import datetime

_url_main = 'http://tkm.ibb.gov.tr'
_url_not_found = _url_main + '/notfound.html'
_url_static_file = _url_main + '/YHarita/res/r0.txt'
_url_traffic_indx = _url_main + '/data/IntensityMap/TrafficIndex.aspx'
_e_tag = tkm._now().strftime('%Y%m%d')

def test_tkm_add_e_tag():
    a = tkm._add_e_tag('abc', '123')
    assert a == 'abc.123'

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
    assert isinstance(a, datetime)
    assert b is None
    assert ['notfound', _e_tag, 'csv'] == c.split('.')
    assert d == 'NA'

def test_get_traffic_index():
    a, b, c, d = tkm.get_traffic_index()
    assert isinstance(a, datetime)
    assert b is None
    assert ['TrafficIndex', _e_tag, 'csv'] == c.split('.')
    assert isinstance(d, unicode)


def test_get_traffic_data():
    a, b, c, d = tkm.get_traffic_data()
    assert isinstance(a, datetime)
    assert b is None
    assert ['TrafficDataNew', _e_tag, 'csv'] == c.split('.')
    assert isinstance(d, unicode)
    assert all(i in '0123456789|&' for i in d)


def test_get_parking_data():
    a, b, c, d = tkm.get_parking_data()
    assert isinstance(a, datetime)
    assert b is None
    assert ['ParkingLotData', _e_tag, 'csv'] == c.split('.')
    assert isinstance(d, unicode)
    assert all(i in '0123456789&-~.: ' for i in d)


def test_get_announcements():
    a, b, c, d = tkm.get_announcements()
    assert isinstance(a, datetime)
    assert b is None
    assert ['AnnouncementData', _e_tag, 'csv'] == c.split('.')
    assert isinstance(d, unicode)
    str_list = u"\xfcj\u011f! \xc7'0)(-,/.1\u013032547698:ACBEDGPHKvMONgSR" + \
               u"UTWVYZ\u015f\u015ea&cbed\xe7fihk\u0131mlonpsrutw\xf6yz|"
    assert all(i in str_list for i in d)


def test_get_weather_data():
    # get uniq chars -> ''.join(set(d))
    a, b, c, d = tkm.get_weather_data()
    assert isinstance(a, datetime)
    assert b is None
    assert ['WeatherData', _e_tag, 'csv'] == c.split('.')
    assert isinstance(d, unicode)
    str_list = u'\xfc\u011f &-,.1032547698:ABDGHK\xf6ONSUVY\u015fae\xe7gfi' + \
               u'hk\u0131mlonsrutvyz|'
    assert all(i in str_list for i in d)


