#!/usr/bin/python # noqa
# -*- coding: utf-8 -*-
"""This is decryption module for tkm.py"""

from array import array
import numpy as np

# region Constants
_REF_TABLE_1 = array('i', (
    237, 220, 239, 100, 120, 248, 241, 54, 244, 169, 178, 230, 68, 203, 43,
    127, 175, 114, 154, 60, 218, 20, 140, 238, 84, 95, 93, 142, 62, 3, 69,
    255, 156, 152, 211, 148, 112, 245, 246, 113, 161, 99, 123, 59, 94, 21,
    209, 19, 205, 122, 2, 91, 72, 184, 240, 82, 131, 213, 201, 90, 31, 181,
    227, 221, 222, 162, 104, 200, 217, 133, 149, 190, 81, 85, 53, 6, 197, 103,
    44, 102, 79, 96, 186, 219, 27, 229, 139, 76, 145, 89, 83, 247, 34, 193, 58,
    61, 48, 174, 35, 250, 46, 182, 143, 232, 71, 136, 18, 50, 78, 128, 39, 108,
    109, 75, 42, 126, 233, 51, 115, 74, 47, 101, 49, 32, 16, 172, 88, 151, 111,
    45, 116, 55, 188, 118, 234, 22, 77, 228, 67, 36, 198, 15, 226, 242, 28,
    153, 121, 33, 12, 163, 129, 107, 135, 98, 70, 150, 63, 144, 124, 158, 11,
    171, 86, 159, 66, 231, 141, 64, 56, 160, 7, 8, 155, 206, 5, 23, 1, 37, 9,
    40, 110, 29, 132, 195, 216, 105, 10, 225, 125, 24, 176, 65, 130, 253, 235,
    192, 87, 189, 41, 14, 249, 30, 166, 243, 164, 80, 194, 183, 167, 173, 26,
    180, 202, 73, 191, 97, 57, 210, 146, 236, 207, 147, 177, 215, 223, 170, 25,
    214, 38, 252, 137, 254, 52, 208, 196, 0, 4, 13, 138, 212, 117, 165, 179,
    106, 119, 224, 134, 168, 199, 204, 17, 157, 251, 187, 185, 92))

_REF_TABLE_2 = array('i', (
    235, 176, 50, 29, 236, 174, 75, 170, 171, 178, 186, 160, 148, 237, 199,
    141, 124, 250, 106, 47, 21, 45, 135, 175, 189, 226, 210, 84, 144, 181, 201,
    60, 123, 147, 92, 98, 139, 177, 228, 110, 179, 198, 114, 14, 78, 129, 100,
    120, 96, 122, 107, 117, 232, 74, 7, 131, 168, 216, 94, 43, 19, 95, 28, 156,
    167, 191, 164, 138, 12, 30, 154, 104, 52, 213, 119, 113, 87, 136, 108, 80,
    205, 72, 55, 90, 24, 73, 162, 196, 126, 89, 59, 51, 255, 26, 44, 25, 81,
    215, 153, 41, 3, 121, 79, 77, 66, 185, 243, 151, 111, 112, 180, 128, 36,
    39, 17, 118, 130, 240, 133, 244, 4, 146, 49, 42, 158, 188, 115, 15, 109,
    150, 192, 56, 182, 69, 246, 152, 105, 230, 238, 86, 22, 166, 27, 102, 157,
    88, 218, 221, 35, 70, 155, 127, 33, 145, 18, 172, 32, 251, 159, 163, 169,
    40, 65, 149, 204, 241, 202, 208, 247, 9, 225, 161, 125, 209, 97, 16, 190,
    222, 10, 242, 211, 61, 101, 207, 53, 254, 82, 253, 132, 197, 71, 214, 195,
    93, 206, 183, 234, 76, 140, 248, 67, 58, 212, 13, 249, 48, 173, 220, 233,
    46, 217, 34, 239, 57, 227, 223, 184, 68, 20, 83, 1, 63, 64, 224, 245, 187,
    142, 62, 137, 85, 11, 165, 103, 116, 134, 194, 219, 0, 23, 2, 54, 6, 143,
    203, 8, 37, 38, 91, 5, 200, 99, 252, 229, 193, 231, 31))

_KEY_SIZE = 8
_KEY_SECTION_LENGTH = 30
_CLEAR_TEXT_LENGTH_SECTION_LENGTH = 7
_HEX_CHARS = '0123456789ABCDEF'
_INT_TO_CHAR_TABLE = '\x00ZN\xc3\x87V bCK\xc4\xb1Ut01\xc3\x9cL\xc5\x9f' + \
                     'EaB23O\xc3\x96456u7M8S!9\xc5\x9eFRDAIPHpT\xc4\x9e' + \
                     'i\xc3\xbc/J+%hrGYsyc&(zn)\xc3\xa7vjd=ek\xc4\x9fmo' + \
                     'g?*-\xc3\xb6f_\xc4\xb0{l}[]#$@<>;.:"\'WwQqXx\\\n\r' + \
                     ',|~\xc3\xa9^\x01\x02\x03\x04\x05\x06\x07\x08\t\x0b' + \
                     '\x0c\x0e\x0f\x10\x11\x12\x13\x14'
# endregion


# region private functions

def _hex_to_str(p1, p2):
    return ''.join(
        [chr((_HEX_CHARS.find(p1[i]) << 4 | _HEX_CHARS.find(p1[i + 1])))
         for i in range(0, len(p1) + p2, 2)]
    )


def _de_shuffle_hex_str(p1, p2, p3, p4):
    u = [int(j) for j in p2]
    l7 = [u[(i - p3) % _KEY_SIZE] for i in range(_KEY_SIZE)]
    # http://stackoverflow.com/questions/10133194/reverse-modulus-operator

    l9 = len(p1) + p4
    l8 = [ord(i) for i in p1[:l9]]
    a = l9 / _KEY_SIZE
    for i in range(a):
        l9 = i * _KEY_SIZE
        for j in range(_KEY_SIZE):
            l8[l9 + l7[j]] = ord(p1[(l9 + j)])

    return ''.join([chr(i) for i in l8])

# endregion


# region public functions

def decrypt0(encrypted_text, key):
    """Decrypt an encrypted text by a key.

    This function is used to decrypt instant data.
    :type key: str
    :type encrypted_text: str
    :param encrypted_text: Encrypted text
    :param key: Key string
    :return:
    """
    # region Internal functions

    def _f(j):
        """internal function.

        :rtype: int
        """
        return int(encrypted_text[len(encrypted_text) - j])

    def _opt(l8):
        """internal function.

        :param l8: Option
        :rtype: str
        """
        if l8 == 0:
            return encrypted_text
        elif l8 == 1:
            return _hex_to_str(encrypted_text, -1)
        elif l8 == 2:
            return _hex_to_str(
                _de_shuffle_hex_str(encrypted_text, key, _f(2), -2), 0)

    # endregion

    l6 = _opt(_f(1))
    l9 = [ord(l6[25 + _KEY_SIZE + (ord(l6[(20 + i)]) - 90)]) - 90
          for i in range(0, _KEY_SIZE)]

    l10 = sum(l9) % l9[0] + 1

    l5 = ''.join([chr((ord(l6[(20 + _KEY_SIZE + i)]) - (60 + i)))
                  for i in range(5)])

    l4 = l6[(55 + _KEY_SIZE):(55 + _KEY_SIZE + int(l5))]
    l3 = ''
    for i in range(int(l5)):
        l19 = ord(l4[i])
        l20 = l9[i % _KEY_SIZE]
        l19 = (l19 >> l20 | (l19 << 8 - l20 & 255)) & 255
        l19 -= int(l10)
        l3 += _INT_TO_CHAR_TABLE.decode('utf-8')[l19]

    return l3.encode('utf-8')


def decrypt2(encrypted_text):
    """Decrypt an encrypted text.

    This function is used to decrypt static files.
    :type encrypted_text: str
    :param encrypted_text: Encrypted text
    :return: Decrypted Text
    """
    # this function is faster for big encrypted_text
    def f(x):return x - 55 if x > 57 else x - 48
    f = np.vectorize(f, otypes=[np.uint8])

    ibyte = np.fromstring(encrypted_text, dtype = 'uint8')
    key, c1, c2, l = 3, 6, 3, len(ibyte)
    ii1 = (f(ibyte[c1:l:2]) << 4) + f(ibyte[(c1+1):l:2])
    cc2 = (np.arange(c2, len(ii1)+c2) & 15) + key
    rt1 = np.array(_REF_TABLE_1, dtype='int8')
    rt2 = np.array(_REF_TABLE_2, dtype='int8')
    return rt2[ii1 ^ rt1[cc2]].tostring()


def decrypt2_old(encrypted_text):
    """Decrypt an encrypted text.

    This function is used to decrypt static files.
    :type encrypted_text: str
    :param encrypted_text: Encrypted text
    :return: Decrypted Text
    """
    in_bytes = [ord(i) for i in encrypted_text]
    out_bytes = bytearray(len(in_bytes))
    key, c1, c2 = 3, 6, 3
    while c1 < (len(in_bytes)):
        i1 = (in_bytes[c1] - 48)
        c1 += 1
        i2 = (in_bytes[c1] - 48)
        c1 += 1
        if i1 > 9: i1 -= 7
        if i2 > 9: i2 -= 7
        i1 = (i1 << 4) + i2
        i1 = i1 ^ _REF_TABLE_1[key + (c2 & 15)]
        i1 = _REF_TABLE_2[i1]
        out_bytes[c2 - 3] = i1
        c2 += 1
    clear_text = str(out_bytes)
    return clear_text[:clear_text.find('\x00')]

# endregion
