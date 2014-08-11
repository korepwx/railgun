// @file: runlib/python/pyhost/CSafeRunner/src/utility.cpp
// ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
// Contributors:
//   public@korepwx.com   <public@korepwx.com>
// ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
// This file is released under BSD 2-clause license.

#include <iostream>
#include <iterator>
#include "utility.h"
#include "3rdparty/utf8.h"

namespace
{
  char ToHex(int value)
  {
    if (value >= 10)
      return 'A' + (value - 10);
    return value + '0';
  }
}

void UTF8toUnicode(std::string const& s, UnicodeString *dst)
{
  dst->clear();
  try {
    utf8::utf8to16(s.begin(), s.end(), std::back_inserter(*dst));
  } catch (...) {
    throw UnicodeError();
  }
}

void UnicodetoUTF8(UnicodeString const& s, std::string *dst)
{
  dst->clear();
  try {
    utf8::utf16to8(s.begin(), s.end(), std::back_inserter(*dst));
  } catch (...) {
    throw UnicodeError();
  }
}

bool IsPrintableChar(UChar ch)
{
  return (ch >= 0x20 && ch < 0x7f);
}

void WriteEscapeString(UnicodeString const& s, std::ostream *os)
{
  for (UChar c: s) {
    switch (c) {
      case '\\':
        *os << "\\\\";
        break;
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
          char hexdigit[4];
          for (int i=3; i>=0; --i) {
            hexdigit[i] = ToHex(c % 16);
            c /= 16;
          }
          *os << "\\u";
          for (int i=0; i<4; ++i) {
            *os << hexdigit[i];
          }
        } else {
          *os << (char)c;
        }
        break;
    }
  }
}

void WriteEscapeString(std::string const& s, std::ostream *os)
{
  UnicodeString ustring;
  UTF8toUnicode(s, &ustring);
  WriteEscapeString(ustring, os);
}
