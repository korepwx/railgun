// @file: runlib/python/pyhost/CSafeRunner/src/score.h
// ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
// Contributors:
//   public@korepwx.com   <public@korepwx.com>
// ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
// This file is released under BSD 2-clause license.

#ifndef RUNLIB_PYTHON_PYHOST_CSAFERUNNER_SRC_SCORE_H_942C47EE1F9F11E4B2A084383555E6CC
#define RUNLIB_PYTHON_PYHOST_CSAFERUNNER_SRC_SCORE_H_942C47EE1F9F11E4B2A084383555E6CC

#include <string>
#include <vector>
#include <iosfwd>
#include "gettext.h"

struct HwPartialScore
{
  GetTextString name;
  double score;
  double weight;
  VariantPtr time;
  GetTextString brief;
  std::vector<GetTextString> detail;

  HwPartialScore();

  // Serialize this object into Json output stream
  void writeJson(std::ostream *os) const;
};

struct HwScore
{
  // HwScore actually does not carry `uuid`. However, we must contain it
  // in payload when posting to remote api.
  std::string uuid;

  bool accepted;
  GetTextString result;
  std::vector<HwPartialScore> partials;

  HwScore();

  // Serialize this object into Json output stream
  void writeJson(std::ostream *os) const;
};

#endif // RUNLIB_PYTHON_PYHOST_CSAFERUNNER_SRC_SCORE_H_942C47EE1F9F11E4B2A084383555E6CC
