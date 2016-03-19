#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Compression utility for 7z and zip files. Optimized for csv files."""

import os
import pylzma
import zipfile as zipf


def compress(f, big_data=False, f_type='7z'):
    """
    Compresses a file. Optimized for csv files.

    :param f: Full file path
    :param big_data: If True, directly reads data from file, compress it and
                    writes to new file. Uses less memory. Suitable for big data.
    :param f_type: File type: 7z | zip
    :type f_type: str
    :type big_data: bool
    :type f: str
    """
    if f_type == '7z':
        import struct
        with open(f, "rb") as f1:
            c =pylzma.compressfile(f1, literalContextBits=4, eos=0,
                                   dictionary=24, fastBytes=255)
            result = c.read(5) + struct.pack('<Q', os.path.getsize(f))
            fn = f +'.7z'
            with open(fn, 'wb') as f2: f2.write(result)
            with open(fn, 'ab') as f2:
                if big_data:
                    while True:
                        tmp = c.read(1024)
                        if not tmp: break
                        f2.write(tmp)
                else:
                    f2.write(c.read())
    elif f_type == 'zip':
        # http://stackoverflow.com/questions/14568647/create-zip-in-python?rq=1
        with zipf.ZipFile(f +'.zip', 'w', zipf.ZIP_DEFLATED) as z:
            z.write(f, os.path.basename(f))


def decompress(f):
    """
    Decompress a compressed file by the extension.
    Only supports .7z and .zip files.

    :type f: str
    :param f: Full path to file
    """
    fn, ext = os.path.splitext(f)
    if ext == '.7z':
        with open(f, "rb") as fl: cdata = fl.read()
        with open(fn, 'wb') as fl:
            fl.write(pylzma.decompress_compat(cdata[0:5] + cdata[13:]))
    elif ext == '.zip':
        with zipf.ZipFile(f) as z: z.extractall(os.path.dirname(f))


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
        if len(il)>0:
            byts = z.read(il[0].filename)
    return byts.decode()



