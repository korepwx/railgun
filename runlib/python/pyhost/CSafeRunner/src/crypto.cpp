// @file: runlib/python/pyhost/CSafeRunner/src/crypto.cpp
// ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
// Contributors:
//   public@korepwx.com   <public@korepwx.com>
// ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
// This file is released under BSD 2-clause license.

#include <stdlib.h>
#include <stdio.h>
#include <iostream>
#include <stdexcept>
#include <vector>

#include <cryptopp/modes.h>
#include <cryptopp/aes.h>
#include <cryptopp/filters.h>

#include "crypto.h"

using namespace CryptoPP;

// AES parameters
static const int KeySize = 32;
static const int BlockSize = AES::BLOCKSIZE;
static const int IVSize = BlockSize;


AESCipher::AESCipher(std::string const& key)
{
  int keysize = int(key.size());
  if (keysize > KeySize) {
    keysize = KeySize;
  }
  memcpy(this->key, key.data(), keysize);
  memset(this->key+keysize, 0, KeySize - keysize);
}

std::string AESCipher::encrypt(std::string const& s) const
{
  // Initialize the AES encryptor
  byte iv[IVSize];
  memset(iv, 0, sizeof(iv));

  AES::Encryption aes(key, KeySize);
  CBC_Mode_ExternalCipher::Encryption cbc(aes, iv);

  // Do encryption
  // TODO: write unittest to check whether following routine correctly outputs
  //       padded cipher just as railgun.common.crypto.AESCipher does.
  std::string cipher;
  StreamTransformationFilter encryptor(cbc, new StringSink(cipher));
  encryptor.Put((const byte*)s.data(), s.size());
  encryptor.MessageEnd();

  // Return IV + cipher text
  return std::string((char*)iv, sizeof(iv)) + cipher;
}
