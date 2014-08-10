// @file: runlib/python/pyhost/CSafeRunner/src/gettext.h
// ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
// Contributors:
//   public@korepwx.com   <public@korepwx.com>
// ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
// This file is released under BSD 2-clause license.

#ifndef RUNLIB_PYTHON_PYHOST_CSAFERUNNER_SRC_GETTEXT_H_07D9A7F81FA611E48B1A84383555E6CC
#define RUNLIB_PYTHON_PYHOST_CSAFERUNNER_SRC_GETTEXT_H_07D9A7F81FA611E48B1A84383555E6CC

#include <string>
#include <map>
#include <iosfwd>
#include <memory>
#include "variant.h"

struct GetTextString
{
  std::string text;
  std::map<std::string, std::shared_ptr<Variant> > kwargs;

  GetTextString();
  explicit GetTextString(std::string const& text);
  ~GetTextString();

  void writeJson(std::ostream *os) const;
};



#endif // RUNLIB_PYTHON_PYHOST_CSAFERUNNER_SRC_GETTEXT_H_07D9A7F81FA611E48B1A84383555E6CC
