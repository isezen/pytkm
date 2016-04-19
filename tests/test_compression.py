#!/usr/bin/python # noqa
# -*- coding: utf-8 -*-
# pylint: disable=C0103, C0321, W0212
"""Test module for compression.py"""

import os
import hashlib
import tempfile
import compression as c # pylint: disable=E0401

_f = 'tests/encrypted.dat'

def test_compression():
    """ Test compression and decompression functions """
    f_sha = hashlib.sha256(open(_f, 'rb').read()).hexdigest()
    temp_name = os.path.join('tests', next(tempfile._get_candidate_names()))

    fc = c.compress(_f, temp_name)
    fd = c.decompress(fc)
    assert f_sha == hashlib.sha256(open(fd, 'rb').read()).hexdigest()
    os.remove(fc); os.remove(fd)

    fc = c.compress(_f, temp_name, f_type='zip')
    fd = c.decompress(fc)
    assert f_sha == hashlib.sha256(open(fd, 'rb').read()).hexdigest()
    os.remove(fc); os.remove(fd)


