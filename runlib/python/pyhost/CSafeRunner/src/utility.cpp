// @file: runlib/python/pyhost/CSafeRunner/src/utility.cpp
// ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
// Contributors:
//   public@korepwx.com   <public@korepwx.com>
// ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
// This file is released under BSD 2-clause license.

#include <iostream>
#include "utility.h"

namespace
{
  char ToHex(int value)
  {
    if (value >= 10)
      return 'A' + (value - 10);
    return value + '0';
  }
}

bool IsPrintableChar(char ch)
{
  return (ch >= 0x20 && ch < 0x7f);
}

void WriteEscapeString(std::string const& s, std::ostream *os)
{
  for (char c: s) {
    switch (c) {
      case '"':
        *os << "\\\"";
        break;
      case '\n':
        *os << "\\n";
        break;
      case '\r':
        *os << "\\r";
        break;
      case '\t':
        *os << "\\t";
        break;
      default:
        if (!IsPrintableChar(c)) {
          int cv = (unsigned char)c;
          *os << "\\x" << ToHex(c / 16) << ToHex(c % 16);
        } else {
          *os << c;
        }
        break;
    }
  }
}
