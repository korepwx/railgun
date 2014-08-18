// @file: runlib/python/pyhost/CSafeRunner/src/gettext.cpp
// ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
// This file is released under BSD 2-clause license.

#include <iostream>
#include "gettext.h"
#include "utility.h"

GetTextString::GetTextString()
{
}

GetTextString::GetTextString(std::string const& text)
{
  UTF8toUnicode(text, &(this->text));
}

GetTextString::GetTextString(UnicodeString const& text) : text(text)
{
}

GetTextString::~GetTextString()
{
}

namespace
{
  void WriteKeyValuePair(UnicodeString const& name, Variant const& value,
                         std::ostream *os)
  {
    *os << "\"";
    WriteEscapeString(name, os);
    *os << "\": ";
    value.writeJson(os);
  }
}

void GetTextString::writeJson(std::ostream* os) const
{
  *os << "{\"text\": \"";
  WriteEscapeString(text, os);
  *os << "\", \"kwargs\": {";

  if (kwargs.size() > 0) {
    auto it = kwargs.begin();
    WriteKeyValuePair(it->first, *(it->second), os);

    while (++it != kwargs.end()) {
      *os << ", ";
      WriteKeyValuePair(it->first, *(it->second), os);
    }
  }

  *os << "}}";
}
