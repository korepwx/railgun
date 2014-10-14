#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/common/crypto.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

from Crypto import Random
from Crypto.Cipher import AES


class AESCipher(object):
    """Wrap the AES encryption algorithm so that you can use secret keys
    in any size to encrypt a plain text in any length, and decrypt it
    backwards.  You don't need to worry about the paddings, in that this
    class will take care of it for you.

    :param key: Encryption and decryption key for AES algorithm.
        If `len(key)` != 32, it will be padded or truncated.
    :type key: :class:`str`
    """

    def __init__(self, key):
        """Construct a new :class:`AESCipher` with given `key`."""

        # AES encryption parameters
        self.BlockSize = AES.block_size
        self.IVSize = self.BlockSize
        self.KeySize = 32
        # pad the key
        if len(key) >= self.KeySize:
            self.key = key[:self.KeySize]
        else:
            self.key = self._padkey(key)

    def encrypt(self, raw):
        """Encrypt the `raw` text.

        :param raw: Plain text to be encrypted.
        :type raw: :class:`str`
        """
        raw = self._pad(raw)
        iv = Random.new().read(self.IVSize)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return iv + cipher.encrypt(raw)

    def decrypt(self, enc):
        """Decrypt the `enc` text.

        :param enc: Cipher text to be decrypted.
        :type enc: :class:`str`
        """
        iv = enc[:self.IVSize]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc[self.IVSize:]))

    def _padkey(self, s):
        padsize = self.KeySize - len(s) % self.KeySize
        return s + (chr(0) * padsize)

    def _pad(self, s):
        padsize = self.BlockSize - len(s) % self.BlockSize
        return s + (chr(padsize) * padsize)

    def _unpad(self, s):
        if not s or len(s) % self.BlockSize != 0:
            raise ValueError("`s` is not a padded string.")
        return s[:-ord(s[-1])]


def DecryptMessage(s, key):
    """Convenient method to encrypt `s` with `key`.

    :param s: Cipher text to be decrypted.
    :type s: :class:`str`
    :param key: Key to be used in AES algorithm.
    :type key: :class:`str`
    """
    return AESCipher(key).decrypt(s)


def EncryptMessage(s, key):
    """Convenient method to decrypt `s` with `key`.

    :param s: Plain text to be encrypted.
    :type s: :class:`str`
    :param key: Key to be used in AES algorithm.
    :type key: :class:`str`
    """
    return AESCipher(key).encrypt(s)
