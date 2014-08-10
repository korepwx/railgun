#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/common/crypto.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Contributors:
#   public@korepwx.com   <public@korepwx.com>
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

from Crypto import Random
from Crypto.Cipher import AES


class AESCipher:
    def __init__(self, key):
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
        raw = self._pad(raw)
        iv = Random.new().read(self.IVSize)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return iv + cipher.encrypt(raw)

    def decrypt(self, enc):
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
        if (not s or len(s) % self.BlockSize != 0):
            raise ValueError("`s` is not a padded string.")
        return s[:-ord(s[-1])]


def DecryptMessage(s, key):
    return AESCipher(key).decrypt(s)


def EncryptMessage(s, key):
    return AESCipher(key).encrypt(s)
