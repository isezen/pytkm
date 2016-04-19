#!/usr/bin/python
# -*- coding: utf-8 -*-
# pylint: disable=C0103, C0321, W0212
"""Compression utility for 7z and zip files. Optimized for csv files."""

import os
import zipfile as zipf
import pylzma


def compress(f, rename_to=None, big_data=False, f_type='7z'):
    """
    Compresses a file. Optimized for csv files.

    :param f: Full file path
    :param big_data: If True, directly reads data from file, compress it and
                     writes to new file. Uses less memory. Suitable for big
                     data.
    :param f_type: File type: 7z | zip
    :type f_type: str
    :type big_data: bool
    :type f: str
    """
    f_types = ['7z', 'zip']
    if f_type not in f_types:
        raise ValueError("f_type must be one of %s" % f_types)

    fn = f if rename_to is None else rename_to
    fn = fn + '.' + f_type
    if f_type == f_types[0]:
        import struct
        with open(f, "rb") as f1:
            # pylint: disable=E1101
            c = pylzma.compressfile(f1, literalContextBits=4, eos=0,
                                    dictionary=24, fastBytes=255)
            result = c.read(5) + struct.pack('<Q', os.path.getsize(f))
            with open(fn, 'wb') as f2: f2.write(result)
            with open(fn, 'ab') as f2:
                if big_data:
                    while True:
                        tmp = c.read(1024)
                        if not tmp: break
                        f2.write(tmp)
                else:
                    f2.write(c.read())
    elif f_type == f_types[1]:
        # http://stackoverflow.com/questions/14568647/create-zip-in-python?rq=1
        with zipf.ZipFile(fn, 'w', zipf.ZIP_DEFLATED) as z:
            f2 = os.path.splitext(fn)[0] + os.path.splitext(f)[1]
            z.write(f, os.path.basename(f2))
    return fn


def decompress(f, rename_to=None):
    """
    Decompress a compressed file by the extension.
    Only supports .7z and .zip files.

    :type f: str
    :param f: Full path to file
    """
    f_types = ['.7z', '.zip']
    fn, ext = os.path.splitext(f)
    if ext not in f_types:
        raise ValueError("f extension must be one of %s" % f_types)
    fn = fn if rename_to is None else rename_to
    if ext == f_types[0]:
        with open(f, "rb") as fl: cdata = fl.read()
        with open(fn, 'wb') as fl:
            # pylint: disable=E1101
            fl.write(pylzma.decompress_compat(cdata[0:5] + cdata[13:]))
    elif ext == f_types[1]:
        with zipf.ZipFile(f) as z:
            p = os.path.dirname(f)
            z.extractall(p)
            fn = z.namelist()
            fn = [os.path.join(p, i) for i in fn]
            if len(fn) == 1: fn = fn[0]
    return fn


def read_from_zip(f):
    """
    Reads first file content from zip file.

    :param f: Full path to file
    :return: Decompressed data
    :rtype: str
    """
    byts = ''
    with zipf.ZipFile(f) as z:
        il = z.infolist()
        if len(il) > 0:
            byts = z.read(il[0].filename)
    return byts.decode()



