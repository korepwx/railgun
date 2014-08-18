// @file: runlib/python/pyhost/CSafeRunner/src/score.cpp
// ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
// This file is released under BSD 2-clause license.

#include <iostream>
#include "score.h"
#include "utility.h"

// -------- HwPartialScore --------
HwPartialScore::HwPartialScore()
: score(0), weight(1), time(NullObject::New())
{
}

void HwPartialScore::writeJson(std::ostream* os) const
{
  *os << "{\"name\": ";
  name.writeJson(os);
  *os << ", \"typeName\": \"";
  WriteEscapeString(typeName, os);
  *os << "\", \"score\": " << score << ", \"weight\": " << weight
      << ", \"time\": ";
  this->time->writeJson(os);
  *os << ", \"brief\": ";
  brief.writeJson(os);
  *os << ", \"detail\": [";

  // Write detail strings
  if (detail.size() > 0) {
    auto it = detail.begin();
    it->writeJson(os);

    while (++it != detail.end()) {
      *os << ", ";
      it->writeJson(os);
    }
  }

  *os << "]}";
}

// -------- HwScore --------
HwScore::HwScore() : accepted(false) {}
void HwScore::writeJson(std::ostream* os) const
{
  *os << "{\"uuid\": \"";
  WriteEscapeString(uuid, os);
  *os << "\", \"accepted\": " << (accepted ? "true" : "false")
      << ", \"result\": ";
  result.writeJson(os);
  *os << ", \"partials\": [";

  // write partial scores
  if (partials.size() > 0) {
    auto it = partials.begin();
    it->writeJson(os);

    while (++it != partials.end()) {
      *os << ", ";
      it->writeJson(os);
    }
  }

  *os << "]}";
}
