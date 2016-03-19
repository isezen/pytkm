#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Converter functions from eoner csv files to mine"""

import os
import re
from datetime import timedelta
from datetime import datetime as dt
from dateutil import tz
import compression as comp
import tkm

def _add_date_to_file_name(f, date):
    return '{0}.{2}{1}'.format(*(os.path.splitext(f) + (date,)))


def _oa_to_datetime(x):
    if isinstance(x, str) or isinstance(x, unicode):
        non_decimal = re.compile(r'[^\d.]+')
        x = float(non_decimal.sub('', x))
    return dt(1899,12,30) + timedelta(days=x)

def convert_data_from_zip_file(f):
    """
    Directly reads eoner's csv from zip file and converts it to ours.
    :param f: Full path to file name.
    :type f: str
    """

    # f = '/Users/isezen/project/tkmpy/tkmdata/2015-07-31.zip'
    date = os.path.splitext(os.path.basename(f))[0]
    date = dt.strptime(date,'%Y-%m-%d')
    fnames = [_add_date_to_file_name(os.path.splitext(os.path.basename(url))[0],
                                     date.strftime('%Y%m%d')) +'.csv'
              for url in tkm.URL[:5]]
    text = comp.read_from_zip(f)
    k = 0
    for l in [x for x in text.split('\n') if not re.match(r'^\s*$', x)]:
        d = l.replace(u'\ufeff','').split('#')
        if len(d)>6:
            for i in range(6,len(d)): d[5] = d[5] + '#' + d[i]
            d = d[0:6]

        d = [i.replace(';', '|').replace('|&', '&') for i in d]
        for i in range(len(d)):
            if d[i][len(d[i])-1] == u'&': d[i] = d[i][:(len(d[i])-1)]
        date = _oa_to_datetime(d[0])
        date = date.replace(tzinfo=tz.tzutc()).astimezone(tz.tzlocal())
        k+=1
        for i in range(len(d[:-1])):
            f_name = _add_date_to_file_name(os.path.basename(tkm.URL[i]),
                                            date.strftime('%Y%m%d'))
            f_name = os.path.splitext(f_name)[0] + '.csv'
            if d[i+1] != 'error':
                tkmd = tkm.TKM_DATA(date=date, e_tag=None,
                                    filename=f_name, data=d[i+1])
                tkm.save_instant_data(tkmd)

    for f in fnames:
        f = os.path.join(tkm.DIR.data, f)
        comp.compress(f)
        if os.path.exists(f): os.remove(f)


def convert_data_from_eoner():
    """
    Converts directly data from zip file to 7z.
    """
    dir_tkmdata = os.path.join(tkm.DIR.cur, "tkmdata")
    for f in [f for f in os.listdir(dir_tkmdata) if f.endswith('.zip')]:
        date = os.path.splitext(os.path.basename(f))[0]
        date = dt.strptime(date,'%Y-%m-%d')
        f_names = [
            _add_date_to_file_name(
                  os.path.splitext(os.path.basename(url))[0],
                  date.strftime('%Y%m%d')) +'.csv' for url in tkm.URL[:5]
            ]

        for fl in f_names:
            fl = os.path.join(tkm.DIR.data, fl)
            if os.path.exists(fl): os.remove(fl)

    for f in [f for f in os.listdir(dir_tkmdata) if f.endswith('.zip')]:
        print f
        convert_data_from_zip_file(os.path.join(dir_tkmdata, f))
