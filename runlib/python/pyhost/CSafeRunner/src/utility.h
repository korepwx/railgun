// @file: runlib/python/pyhost/CSafeRunner/src/utility.h
// ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
// This file is released under BSD 2-clause license.

#ifndef RUNLIB_PYTHON_PYHOST_CSAFERUNNER_SRC_UTILITY_H_52D0DEEE1FAA11E49ACD84383555E6CC
#define RUNLIB_PYTHON_PYHOST_CSAFERUNNER_SRC_UTILITY_H_52D0DEEE1FAA11E49ACD84383555E6CC

#include <string>
#include <iosfwd>

/// @brief The unicode class compatible with Python 2.7
typedef unsigned short UChar;
typedef std::basic_string<UChar> UnicodeString;

/// @brief Convert UTF-8 string into UnicodeString
void UTF8toUnicode(std::string const& s, UnicodeString *dst);
static inline UnicodeString UTF8toUnicode(std::string const& s) {
  UnicodeString ret;
  UTF8toUnicode(s, &ret);
  return ret;
}

/// @brief Convert UnicodeString to UTF-8 string
void UnicodetoUTF8(UnicodeString const& s, std::string *dst);

/// @brief Class to represent a UnicodeError
class UnicodeError {};

/// @brief Check whether a character is printable?
bool IsPrintableChar(char ch);

/// @brief Write a string into given output stream in escaped representation.
void WriteEscapeString(std::string const& s, std::ostream *os);

/// @brief Write a unicode into given output stream in escaped representation.
void WriteEscapeString(UnicodeString const& s, std::ostream *os);

#endif // RUNLIB_PYTHON_PYHOST_CSAFERUNNER_SRC_UTILITY_H_52D0DEEE1FAA11E49ACD84383555E6CC
