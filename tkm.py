#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""This script downloads traffic data from tkm.ibb.gov.tr"""

import logging as log
import os
from os import path
from os.path import join as joinp
import re
import threading
import time
import urllib2 as ul
from collections import namedtuple as nt

from datetime import datetime as dt
from dateutil import tz

import tkmdecrypt as td
import compression as c

# region initial definitions

log.basicConfig(format='%(asctime)s %(levelname)s %(name)s %(message)s',
                filename='tkm.log', level=log.INFO)
logger = log.getLogger(__name__)
logger.root.name = 'tkm.py'

SENSOR_DATA = nt('SensorData', 'id speed color')
TKM_DATA = nt('TkmData', 'date e_tag filename data')


def __init__():
    _dir = nt('DirObject', 'cur data static')(
        *[joinp(os.getcwd(), d) for d in ['', 'database/', 'static_files/']])
    # pylint: disable=W0106
    [os.makedirs(p) for p in _dir if not path.exists(p)]
    main_url = 'http://tkm.ibb.gov.tr/'
    # File Names for static files
    fl_road = ['r{0:d}.txt'.format(x) for x in range(5)]
    fl_other = ['d{0:02d}.txt'.format(x) for x in range(1, 10)]
    static_files_url = 'YHarita/res/'
    # Create list of URLs to use in module.
    _url = nt('UrlList',
              'trafficindex trafficdata parkingdata '
              'announcements weatherdata road other')(
        *(tuple([joinp(main_url, url) for url in [
            'data/IntensityMap/' +
            url + '.aspx' for url in [
                'TrafficIndex',
                'TrafficDataNew',
                'ParkingLotData',
                'AnnouncementData',
                'WeatherData']]]) +
            ([joinp(main_url, static_files_url, fn) for fn in fl_road],
             [joinp(main_url, static_files_url, fn) for fn in fl_other])))
    return _url, _dir


URL, DIR = __init__()

# endregion


# region private functions


def _now():
    """
    Return current DateTime in Local Time Zone.

    :rtype: dt
    """
    return dt.now().replace(tzinfo=tz.tzlocal())


def _add_e_tag(f, e_tag):
    return '{0}.{2}{1}'.format(*(path.splitext(f) + (e_tag,)))


def _write_to_file(f, data, last_modified, e_tag=None):
    """
    Write data to a file with last_modified time.

    :param f: Full path to file
    :param data: Unicode data to write to file
    :param last_modified: Last modified date object
    :rtype: None
    """
    if e_tag:  # if e_tag exists, add to filename
        f = _add_e_tag(f, e_tag)
    write_type = 'wb' if e_tag else 'a'
    with open(f, write_type) as fl: fl.write(data)
    # change creation and last modified datetime of file.
    os.utime(f, (time.mktime(_now().timetuple()),
                 time.mktime(last_modified.timetuple())))


def _static_file_write(tkmd):
    """Write tkmd data to a static file.

    :param tkmd: TKM_DATA type object
    :type tkmd: TKM_DATA
    :rtype: None
    """
    _write_to_file(joinp(DIR.static, tkmd.filename),
                   tkmd.data, tkmd.date)


def _static_file_read(fl):
    fl = joinp(DIR.static, fl)
    data = None
    if path.exists(fl):
        with open(fl, "rb") as f:
            data = f.read().decode('UTF-8')
    return data


def _static_file_get_modified_time(f):
    f = joinp(DIR.static, f)
    if path.exists(f):
        return dt.fromtimestamp(
            path.getmtime(f)
        ).replace(tzinfo=tz.tzlocal())
    return None


def _urlopen(url, k=0):
    """Send a request to url.

    :param url: Url to open
    :param k: Only for internal use
    :return: (url_handle, local_last_modified, e_tag)
    :rtype: tuple
    """
    from socket import error as SocketError
    import errno

    file_with_e_tag = path.basename(url)
    try:
        url_handle = ul.urlopen(ul.Request(url))
    # pylint: disable=W0703
    except Exception as e:
        if k < 5:
            k += 1
            # log.error('%s -> %s Retrying [%d]', file_with_e_tag, str(e), k)
            return _urlopen(url, k)
        else:
            url_handle = None
            log.error('%s -> %s STOPPED', file_with_e_tag, str(e))
    if url_handle:
        h = url_handle.info()
        # this value changes if file at url is modified
        e_tag = h.getheader("ETag")
    else:
        h = e_tag = None
    if e_tag:
        e_tag = e_tag.replace('"', '')  # WTF?
        e_tag = e_tag.replace(':', '').upper()  # make e_tag filename friendly
        local_last_modified = dt.fromtimestamp(
            time.mktime(
                time.strptime(
                    h.getheader("Last-Modified"),
                    '%a, %d %b %Y %H:%M:%S %Z'))
        ).replace(tzinfo=tz.tzutc()).astimezone(tz.tzlocal())
        file_with_e_tag = _add_e_tag(file_with_e_tag, e_tag)
    else:  # if e_tag value is None, do not trust to last modified date.
        local_last_modified = _now()
        file_with_e_tag = _add_e_tag(file_with_e_tag, _now().strftime('%Y%m%d'))
        file_with_e_tag = path.splitext(file_with_e_tag)[0] + '.csv'
    return url_handle, local_last_modified, e_tag, file_with_e_tag


def _get_filename_with_e_tag(url, e_tag=None):
    last_modified = None
    f = path.basename(url)
    if e_tag:
        f = _add_e_tag(f, e_tag)
    else:
        (_, last_modified, _, f) = _urlopen(url)
    return f, last_modified


def _static_file_compare_last_modified(url):
    """Compare local and remote files last modified date.

    :param url:  Url to open or StaticFile object
    :return: if file was modified, return a
            tuple (url_handle, local_last_modified, e_tag) else None.
    :type url: str or tuple
    :rtype: tuple
    """
    ret = _urlopen(url)
    f, _ = _get_filename_with_e_tag(url, ret[2])
    last_modified = ret[1]
    if last_modified == _static_file_get_modified_time(f): return None
    return ret


def _get_data(url, key=None, decrypt=True):
    """Download/Get and decrypts data from tkm web site.

    :param url: Full url to data or a tuple from _urlopen()
    :param key: Encryption key
    :return: TKM_DATA object
    :type url: str or tuple
    :type key: str
    :rtype: TKM_DATA
    """
    def _get_data_internal(_url, _key, k=0):
        url_handle, _last_modified, _e_tag, _f_e_tag = _url \
        if isinstance(_url, tuple) else _urlopen(_url)

        if not _e_tag:  # make sure second = 00
            t = list(_now().timetuple())
            t[5] = 0
            _last_modified = dt.fromtimestamp(
                time.mktime(
                    time.struct_time(t))).replace(tzinfo=tz.tzlocal())

        if url_handle:
            _data = url_handle.read()
            if decrypt:
                _data = td.decrypt0(_data, _key) \
                if _key else td.decrypt2(_data)

            if _data == 'error' or _data == 'no_data':
                if k < 5:
                    k += 1
                    # log.error('Server returned ERROR. Retrying [%d]', [k])
                    (_data, _e_tag, _f_e_tag, _last_modified,
                     k) = _get_data_internal(_url, _key, k)
                else:
                    _data = 'NA'
        else:
            _data = 'NA'

        if _data == 'NA':
            log.error('%s -> Server ERROR. Data was saved as NA',
                      path.basename(_url))
        return _data, _e_tag, _f_e_tag, _last_modified, k

    (data, e_tag, f_e_tag, last_modified, _) = _get_data_internal(url, key)
    data = data.replace(';', '|').replace('|&', '&')
    if len(data) > 0:
        if data[len(data) - 1] == '&': data = data[:len(data) - 1]
    return TKM_DATA(date=last_modified, e_tag=e_tag,
                    filename=f_e_tag, data=data.encode('utf-8'))


def _get_static_file_data_if_modified(url):
    """Get static file data if modified.

    First checks for last modified date for the local and remote files and
    latter if last modified dates are different, downloads the remote file
    and compares to local one.

    :param url: url of remote file
    :return: remote file data if modified else None
    :rtype: TKM_DATA
    """
    ret = _static_file_compare_last_modified(url)
    if ret:  # if modified
        tkmd = _get_data(ret)
        if tkmd.data != _static_file_read(ret[3]): return tkmd
    return None


def _static_file_download(url):
    """Download a static file.

    :param url: url to file
    :type url: str
    :rtype: None
    """
    tkmd = _get_static_file_data_if_modified(url)
    if tkmd:
        _static_file_write(tkmd)
        info = tkmd.filename + ' > DOWNLOADED.'
        log.info(info)
        print info
    return tkmd


def _check_for_stop():
    threading.Timer(10, _check_for_stop).start()
    f = joinp(DIR.cur, 'killme')
    if path.exists(f):
        os.remove(f)
        # make sure process will be stopped when threads finished.
        while True:
            sec = _now().second
            if 2 < sec < 60:
                log.info('Module terminated successfully')
                # noinspection PyProtectedMember
                os._exit(0)  # pylint: disable=W0212

# endregion

# region public functions


def get_traffic_index():
    """Download Traffic Index.

    :rtype: TKM_DATA
    :return: TKM_DATA object
    """
    return _get_data(URL.trafficindex, "60413275")


def get_traffic_data():
    """Download Traffic Data.

    :rtype: TKM_DATA
    :return: TKM_DATA object
    """
    return _get_data(URL.trafficdata, "62403715")


def get_parking_data():
    """Download Parking Data.

    :rtype: TKM_DATA
    :return: TKM_DATA object
    """
    return _get_data(URL.parkingdata, "74205136")


def get_announcements():
    """Download Announcements.

    :rtype: TKM_DATA
    :return: TKM_DATA object
    """
    return _get_data(URL.announcements, "50614732")


def get_weather_data():
    """Download Weather Data.

    :rtype: TKM_DATA
    :return: TKM_DATA object
    """
    return _get_data(URL.weatherdata, "26107354")


def download_static_files(url_list=URL.road + URL.other):
    """Download Static Files.

    :type url_list: list
    :param url_list: List of URL
    :rtype: None
    """
    if isinstance(url_list, str): url_list = [url_list]
    if not [t for t in [_static_file_download(u) for u in url_list] if t]:
        if '_logged' not in globals(): # log once per session
            log.info('All Static Files are up-to-date.')
            globals()['_logged'] = 1



def download_roads():
    """Download and save road files (If files were not modified).

    :rtype: None
    """
    download_static_files(URL.road)


def file_is_modified(url):
    """Check if a remote file was modified or not.

    :type url: str
    :param url: url to file
    :return: True if file is modified else False
    :rtype: bool
    """
    try:
        ret = _static_file_compare_last_modified(url)
        return ret is not None
    # pylint: disable=W0703
    except Exception as e:
        err = '{0} -> {1}'.format(path.basename(url), str(e))
        log.error(err)
        print err
    finally:
        pass


def roads_are_modified():
    """Check if roads are modified or not.

    :rtype: list
    :return: list of bool
    """
    return [file_is_modified(u) for u in URL.road]


def _check_refresh_interval(url=URL.trafficdata):
    """Check refresh interval of URL source.

    :param url: A valid URL
    """
    data1 = data2 = ul.urlopen(url).read()
    t1 = _now()
    k = 0
    while data1 == data2: k += 1; data2 = ul.urlopen(url).read()
    t2 = _now()
    print t2 - t1, k


def parse_speed_data(tkmd):
    """Parse speed data and store the result in a hierarchical list object.

    :param tkmd: TKM_DATA object
    :return: TKM_DATA
    """
    data = list()
    # Split tkm.data by & (remove empty elements)
    for l in [x for x in tkmd.data.split('&') if not re.match(r'^\s*$', x)]:
        # split segment value by '|' (remove empty elements)
        token = [x for x in l.split('|') if not re.match(r'^\s*$', x)]
        if token == '' or len(token) < 3: continue
        s = SENSOR_DATA(id=int(token[0]), speed=int(token[1]),
                        color=int(token[2]))
        data.append(s)
    return TKM_DATA(date=tkmd.date, data=data)


def save_instant_data(tkmd):
    """Save TKM_DATA object to file.

    :type tkmd: TKM_DATA
    :param tkmd:
    :rtype: None
    """
    f = joinp(DIR.data, tkmd.filename)
    data = tkmd.date.strftime("%Y-%m-%d %H:%M:%S") + ';' + tkmd.data + '\r\n'
    _write_to_file(f, data, tkmd.date)


def save_traffic_data():
    """Download and save traffic data for every 1 minutes.

    This function starts a thread.
    """
    t = threading.Timer(60, save_traffic_data)
    t.daemon = True
    t.start()
    try:
        save_instant_data(get_traffic_data())
    except Exception as e:  # pylint: disable=W0703
        err = 'save_traffic_data -> ' + str(e)
        log.error(err)
    finally:
        pass


def save_traffic_index():
    """Download and save traffic index data for every 1 minutes.

    This function starts a thread.
    """
    t = threading.Timer(60, save_traffic_index)
    t.daemon = True
    t.start()
    try:
        save_instant_data(get_traffic_index())
    except Exception as e:  # pylint: disable=W0703
        err = 'save_traffic_index -> ' + str(e)
        log.error(err)
    finally:
        pass


def save_weather_data():
    """Download and save weather data for every 1 minutes.

    This function starts a thread.
    """
    t = threading.Timer(60, save_weather_data)
    t.daemon = True
    t.start()
    try:
        save_instant_data(get_weather_data())
    except Exception as e:  # pylint: disable=W0703
        err = 'save_weather_data -> ' + str(e)
        log.error(err)
    finally:
        pass


def save_static_files():
    """Download and save static files if modified for every 10 minutes.

    This function starts a thread.
    """
    t = threading.Timer(3600, save_static_files)
    t.daemon = True
    t.start()
    try:
        download_static_files()
    except Exception as e:  # pylint: disable=W0703
        err = 'save_static_files -> ' + str(e)
        log.error(err)
    finally:
        pass


def compress_files():
    """Compresses downloaded data files.

    This function starts a thread.
    """
    t = threading.Timer(10800, compress_files)
    t.daemon = True
    t.start()
    lcsv = [f for f in os.listdir(DIR.data) if f.endswith('.csv')]
    today_e_tag = _now().strftime('%Y%m%d')
    for f in lcsv:
        ff = os.path.join(DIR.data, f)
        if today_e_tag not in ff:
            c.compress(ff)
            log.info('%s compressed.' % os.path.basename(ff))
            os.remove(ff)


# endregion


if __name__ == "__main__":
    log.info('-------------------------------------------------------------')
    log.info('Module started')

    while True:  # make sure process is started when second is zero.
        if _now().second == 0:
            log.info('data acquisition was started')
            save_traffic_data()
            save_traffic_index()
            save_weather_data()
            save_static_files()
            compress_files()
            _check_for_stop()
            break
