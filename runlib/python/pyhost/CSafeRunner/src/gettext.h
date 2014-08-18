// @file: runlib/python/pyhost/CSafeRunner/src/gettext.h
// ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
// This file is released under BSD 2-clause license.

#ifndef RUNLIB_PYTHON_PYHOST_CSAFERUNNER_SRC_GETTEXT_H_07D9A7F81FA611E48B1A84383555E6CC
#define RUNLIB_PYTHON_PYHOST_CSAFERUNNER_SRC_GETTEXT_H_07D9A7F81FA611E48B1A84383555E6CC

#include <string>
#include <map>
#include <iosfwd>
#include <memory>
#include "utility.h"
#include "variant.h"

struct GetTextString
{
  UnicodeString text;
  std::map<UnicodeString, std::shared_ptr<Variant> > kwargs;

  GetTextString();
  explicit GetTextString(std::string const& text);
  explicit GetTextString(UnicodeString const& text);
  ~GetTextString();

  void writeJson(std::ostream *os) const;
};



#endif // RUNLIB_PYTHON_PYHOST_CSAFERUNNER_SRC_GETTEXT_H_07D9A7F81FA611E48B1A84383555E6CC
