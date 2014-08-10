// @file: runlib/python/pyhost/CSafeRunner/src/utility.h
// ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
// Contributors:
//   public@korepwx.com   <public@korepwx.com>
// ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
// This file is released under BSD 2-clause license.

#ifndef RUNLIB_PYTHON_PYHOST_CSAFERUNNER_SRC_UTILITY_H_52D0DEEE1FAA11E49ACD84383555E6CC
#define RUNLIB_PYTHON_PYHOST_CSAFERUNNER_SRC_UTILITY_H_52D0DEEE1FAA11E49ACD84383555E6CC

#include <string>
#include <iosfwd>

/// @brief Check whether a character is printable?
bool IsPrintableChar(char ch);

/// @brief Write a string into given output stream in escaped representation.
void WriteEscapeString(std::string const& s, std::ostream *os);

#endif // RUNLIB_PYTHON_PYHOST_CSAFERUNNER_SRC_UTILITY_H_52D0DEEE1FAA11E49ACD84383555E6CC
