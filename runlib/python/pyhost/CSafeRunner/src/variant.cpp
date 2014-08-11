// @file: runlib/python/pyhost/CSafeRunner/src/variant.cpp
// ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
// Contributors:
//   public@korepwx.com   <public@korepwx.com>
// ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
// This file is released under BSD 2-clause license.

#include <iostream>
#include "utility.h"
#include "variant.h"

// -------- Variant --------
Variant::Variant() {}
Variant::~Variant() {}

// -------- NullObject --------
NullObject::NullObject() : Variant() {}
void NullObject::writeJson(std::ostream *os) const
{
  *os << "null";
}

// -------- Integer --------
Integer::Integer(int value) : Variant(), value_(value) {}
void Integer::writeJson(std::ostream *os) const
{
  *os << value_;
}

// -------- Double --------
Double::Double(double value) : Variant(), value_(value) {}
void Double::writeJson(std::ostream *os) const
{
  *os << value_;
}

// -------- String --------
String::String(std::string const& value) : Variant(), value_(value) {}
void String::writeJson(std::ostream *os) const
{
  *os << "\"";
  WriteEscapeString(value_, os);
  *os << "\"";
}

// -------- Unicode --------
Unicode::Unicode(UnicodeString const& value) : Variant(), value_(value) {}
void Unicode::writeJson(std::ostream *os) const
{
  *os << "\"";
  WriteEscapeString(value_, os);
  *os << "\"";
}
