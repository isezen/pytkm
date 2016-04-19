#!/usr/bin/python # noqa
# -*- coding: utf-8 -*-
# pylint: disable=C0103, C0321, W0212
"""Test module for tkmdecrypt.py"""

import os
import tkmdecrypt as td  # pylint: disable=E0401

_encrypted_traffic_index_data = 'AF199176AE2FC5028302F355B0478735825B0302A' + \
  '274B755277DA566CD6FE6661066C57506660566CC599573A3533645FB5813077D0A1433' + \
  '2B5DA5279A78E0158728F4642804C571F206A757874E1217612907160C52'

fl = "tests/encrypted.dat"
_enc_data = None
if os.path.exists(fl):
    with open(fl, "rb") as f: _enc_data = f.read()


def test_tkmdecrypt__hex_to_str():
    """ Test _hex_to_str function """
    result = "\xaf\x19\x91v\xae/\xc5\x02\x83\x02\xf3U\xb0G\x87" + \
      "5\x82[\x03\x02\xa2t\xb7U'}\xa5f\xcdo\xe6f\x10f\xc5u\x06f\x05" + \
      "f\xccY\x95s\xa3S6E\xfbX\x13\x07}\n\x143+]\xa5'\x9ax\xe0\x15\x87" + \
      "(\xf4d(\x04\xc5q\xf2\x06\xa7W\x87N\x12\x17a)\x07\x16\x0cR"
    # pylint: disable=W0212
    assert td._hex_to_str(_encrypted_traffic_index_data, -1) == result


def test_tkmdecrypt_de_shuffle_hex_str():
    """ Test _de_shuffle_hex_str function """
    a = '7A1F69190A2E2C5F58035F323B4058770852203B5A725B7462776A5D6C6D6E6F7' + \
      '1605C56606660567C5C39594A5353630F5B7138370D314A225B7A5D197A5E086827' + \
      '4F4872081C545F027A761847712E162160790C'
    key = "60413275"
    # pylint: disable=W0212
    b = td._de_shuffle_hex_str(_encrypted_traffic_index_data, key, 5, -2)
    assert a == b


def test_tkmdecrypt_decrypt0():
    """Test decrypt0 function"""
    assert td.decrypt0(_encrypted_traffic_index_data, "60413275") == '8'


def test_tkmdecrypt_decrypt2_and_old_2():
    """Test decrypt2 function"""
    a = td.decrypt2(_enc_data)
    b = td.decrypt2_old(_enc_data)
    assert a == b

# Benchmark test


def test_decrypt2(benchmark):
    """Big data benchmark test for decrypt2 function"""
    benchmark(td.decrypt2, _enc_data)


def test_decrypt2_old(benchmark):
    """Big data benchmark test for decrypt2 function"""
    benchmark(td.decrypt2_old, _enc_data)
