#!/usr/bin/env python # noqa
# -*- coding: utf-8 -*-
"""This script downloads traffic data from tkm.ibb.gov.tr"""

import logging as log
# import tkm
import compression as comp


log.basicConfig(format='%(asctime)s %(levelname)s %(name)s %(message)s',
                filename='tkm.log', level=log.INFO)
logger = log.getLogger(__name__)
logger.root.name = 'tkm_logger.py'


if __name__ == "__main__":
    csv = '/Users/isezen/project/tkmpy/database/ \
    TrafficDataNew.20160227aaa.csv.zip'

    # noinspection PyMissingOrEmptyDocstring
    def _compress1(): comp.compress(csv, f_type='.zip')

    # noinspection PyMissingOrEmptyDocstring
    def _compress2(): comp.compress(csv, True)

    _compress1()

    # compress2()
    # Line #    Mem usage    Increment   Line Contents
    # ================================================
    #    531   21.891 MiB    0.000 MiB       @profile
    #    532   38.828 MiB   16.938 MiB       def compress2():
    #                                           _compress(csv, True)
