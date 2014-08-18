// @file: runlib/python/pyhost/CSafeRunner/src/crypto.h
// ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
// This file is released under BSD 2-clause license.

#ifndef RUNLIB_PYTHON_PYHOST_CSAFERUNNER_SRC_CRYPTO_H_921863B3204111E4B75D84383555E6CC
#define RUNLIB_PYTHON_PYHOST_CSAFERUNNER_SRC_CRYPTO_H_921863B3204111E4B75D84383555E6CC

#include <string>

class AESCipher
{
  typedef unsigned char byte;
  static const int KeySize = 32;

public:
  AESCipher(std::string const& key);
  std::string encrypt(std::string const& s) const;

private:
  byte key[KeySize];
};

#endif // RUNLIB_PYTHON_PYHOST_CSAFERUNNER_SRC_CRYPTO_H_921863B3204111E4B75D84383555E6CC
