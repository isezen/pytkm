#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=C0103, C0321, C0330
"""This script downloads traffic data from tkm.ibb.gov.tr"""

import argparse
import signal
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
import datetime
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

_stop_events = []
_terminate = False
_run_time = -1
# _file_pid = ""


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


def _create_pid():
    pidfile = "tkm.pid"
    file(pidfile, 'w').write(str(os.getpid()))
    return pidfile


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
        file_with_e_tag = _add_e_tag(file_with_e_tag,
                                     _now().strftime('%Y%m%d'))
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

        if not _e_tag:
            _last_modified = _run_time

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
                    filename=f_e_tag, data=data)


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

# endregion

# region public functions


def get(t):
    """ Get data by type

    :t: type of data ['traffic_data', 'traffic_index',
                      'parking_data', 'announcements', 'weather_data']
    :return: TKM_DATA object
    """
    if t not in ['traffic_data', 'traffic_index',
                 'parking_data', 'announcements', 'weather_data']:
        raise ValueError('get_data(t) -> t is not proper option')
    try:
        if t == "traffic_data":
            return _get_data(URL.trafficdata, "62403715")
        elif t == "traffic_index":
            return _get_data(URL.trafficindex, "60413275")
        elif t == "parking_data":
            return _get_data(URL.parkingdata, "74205136")
        elif t == "announcements":
            return _get_data(URL.announcements, "50614732")
        elif t == "weather_data":
            return _get_data(URL.weatherdata, "26107354")
    except Exception as e:  # pylint: disable=W0703
        err = t + '-> ' + str(e)
        log.error(err)
    finally:
        pass
    return None


def get_traffic_index():
    """Download Traffic Index.

    :rtype: TKM_DATA
    :return: TKM_DATA object
    """
    return get("traffic_index")


def get_traffic_data():
    """Download Traffic Data.

    :rtype: TKM_DATA
    :return: TKM_DATA object
    """
    return get("traffic_data")


def get_parking_data():
    """Download Parking Data.

    :rtype: TKM_DATA
    :return: TKM_DATA object
    """
    return get("parking_data")


def get_announcements():
    """Download Announcements.

    :rtype: TKM_DATA
    :return: TKM_DATA object
    """
    return get("announcements")


def get_weather_data():
    """Download Weather Data.

    :rtype: TKM_DATA
    :return: TKM_DATA object
    """
    return get("weather_data")


def download_static_files(url_list=URL.road + URL.other):
    """Download Static Files.

    :type url_list: list
    :param url_list: List of URL
    :rtype: None
    """
    if isinstance(url_list, str): url_list = [url_list]
    for u in url_list: _static_file_download(u)
    if '_logged' not in globals():  # log once per session
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


def compress_files():
    """Compresses downloaded data files."""
    lcsv = [f for f in os.listdir(DIR.data) if f.endswith('.csv')]
    today_e_tag = _now().strftime('%Y%m%d')
    for f in lcsv:
        ff = os.path.join(DIR.data, f)
        if today_e_tag not in ff:
            c.compress(ff)
            log.info('%s compressed.', os.path.basename(ff))
            os.remove(ff)


def run_action(a):
    """ Run specified action. """
    actions = ['traffic_data', 'traffic_index', 'parking_data',
               'announcements', 'weather_data', 'static_files',
               'compress']
    if a in actions:
        try:
            if a == "static_files":
                download_static_files()
            elif a == "compress":
                compress_files()
            else:
                save_instant_data(get(a))
        except Exception as e:  # pylint: disable=W0703
            err = a + ' -> ' + str(e)
            log.error(err)
        finally:
            pass
    else:
        raise ValueError('selected action must be one of %s' % str(actions))


def worker(action, rep_sec, run_on, stop_event):
    """ Thread worker """
    fmt = '%Y-%m-%d %H:%M:%S'

    def _calc_run_on(run_on, delta=0):
        if isinstance(run_on, str):
            l = len(run_on)
            t = _now().strftime(fmt)
            run_on = t[:-l] + run_on
            run_on = dt.strptime(run_on, fmt).replace(tzinfo=tz.tzlocal())
        while run_on < _now():
            run_on = run_on + datetime.timedelta(0, delta)
            log.debug("run_on=%s" % run_on)
        return run_on.strftime(fmt)

    global _run_time  # pylint: disable=W0603
    a, b = (_now(), 1) if run_on == 'immediate' else (run_on, 60)
    run_on = _calc_run_on(a, b)
    log.info("Thread " + action + " started")
    while not stop_event.is_set():
        if _now().strftime(fmt) == run_on:
            _run_time = dt.strptime(run_on, fmt)
            run_action(action)
            if rep_sec <= 0: break
            time.sleep(rep_sec * 0.9)
        run_on = _calc_run_on(run_on, rep_sec)
        time.sleep(0.2)
    log.info("Thread " + action + " stopped")


def main():
    """Entry point."""
    def signal_handler(*args):  # pylint: disable=W0613
        """ Handle signals from system."""
        # Stop threads
        for se in _stop_events: se.set()
        global _terminate  # pylint: disable=W0603
        _terminate = True
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGTSTP, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    p = argparse.ArgumentParser(
        description='Save data from http://tkm.ibb.gov.tr',
        epilog='Example of use')
    args = [['-t', '--traffic-data', 'save traffic data'],
            ['-i', '--traffic-index', 'save traffic index'],
            ['-p', '--parking-data', 'save parking data'],
            ['-a', '--announcements', 'save announcements'],
            ['-w', '--weather-data', 'save weather data'],
            ['-s', '--static-files', 'save static files'],
            ['-c', '--compress', 'compress old csv files']]
    for a in args: p.add_argument(a[0], a[1], action="store_const",
                                  default=None, const='func', help=a[2])

    p.add_argument('-o', '--on', default='immediate',
                   type=str, help='start on time {default: immediate}')
    p.add_argument('-r', '--repeat', default=0, type=int, dest='rep',
                   help='repeat every n seconds after start ' +
                   '{default: Do not repeat}')

    args = p.parse_args()

    threads = []
    for a, v in sorted(vars(args).items()):
        if v == 'func':
            te = threading.Event()
            threads.append(threading.Thread(target=worker,
                                            args=[a, args.rep, args.on, te]))
            _stop_events.append(te)

    if args.rep > 0:
        log.info('----------------------------------------------------------')
        log.info('Module started in continuous mode')

    # global _file_pid  # pylint: disable=W0603
    # _file_pid = _create_pid()
    # try to start each thread in same time as far as possible
    for t in threads: t.start()

    # do not let main thread end soon
    # this line helps to keep it alive and
    # catch signals to exit properly.
    while not _terminate:
        if not all([t.isAlive() for t in threads]): break
        time.sleep(10)

    if args.rep > 0: log.info('Module terminated gracefully')
    # os.unlink(_file_pid)

# endregion

if __name__ == "__main__":
    main()
