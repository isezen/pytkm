#!/usr/bin/env python # noqa
# -*- coding: utf-8 -*-
#
# THIS MIGHT BE REQUIRED
# For projection from lat/lon to EPSG3857
# See: https://twms.googlecode.com/hg/twms/projections.py
# I think smopy has a projection sytem. NEED MORE STUDY!
# https://github.com/rossant/smopy/blob/master/smopy.py
"""This script downloads traffic data from tkm.ibb.gov.tr"""


from StringIO import StringIO
import matplotlib.pyplot as plt
import numpy as np
import pandas as p
import smopy
import tkm


colors = ['black', 'lime', 'yellowgreen', 'orange', 'red', 'darkred',
          'lightgray']
mp = smopy.Map((40.97, 28.7, 41.2, 29.3), z=12)  # Wide
# map = smopy.Map((41, 28.89, 41.1, 29.0), z=14) # Narrow
# map.show_ipython()

ti = tkm.get_traffic_index()
td = tkm.get_traffic_data(); td_date = td.date
td = p.read_table(StringIO(td.data.replace('&', '\r')), header=None,
                  sep="|", names=['seg', 'speed', 'color'])
for i in range(0, 1):
    road = p.read_table('static_files/r%d.txt' % i, header=None, sep=';',
                        usecols=[0, 1, 2, 3, 10],
                        names=['seg', 'no', 'lon', 'lat', 'district'])
    road.sort_values(['seg', 'no'], ascending=[False, True], inplace=True)
    # get unique numbers in seg column (Use index instead of column name)
    segs = np.unique(road.ix[:, 0])

    ax = mp.show_mpl(figsize=(20, 18))
    ax.text(0.02, 0.02, "r%d.txt" % i, fontsize=20, transform=ax.transAxes)
    ax.text(0.83, 0.95, "Traffic Index: %%%d" % int(ti.data), fontsize=24,
            transform=ax.transAxes)
    ax.text(0.85, 0.92, "{:%Y-%m-%d %H:%M:%S}".format(td_date), fontsize=16,
            transform=ax.transAxes)
    for s in segs:  # for each unique segment in road DataFrame
        seg = road[road.ix[:, 0] == s]  # get road segments
        t = td[td.ix[:, 0] == s]  # filter traffic data for segment
        # get color from traffic data, if it does not exist, then lightgray
        col = 6 if len(t) == 0 else int(t.color)
        # convert lat/lon to pixel coordinates
        x, y = mp.to_pixels(np.array([seg.ix[:, 3], seg.ix[:, 2]]).T).T
        ax.plot(x, y, c='black', linewidth=4)  # make a balck border for roads
        ax.plot(x, y, c=colors[col], linewidth=3)
    fig = plt.gcf()
    fig.savefig('r%d.png' % i)
plt.show()
