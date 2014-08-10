// @file: runlib/python/pyhost/CSafeRunner/src/variant.h
// ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
// Contributors:
//   public@korepwx.com   <public@korepwx.com>
// ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
// This file is released under BSD 2-clause license.

#ifndef RUNLIB_PYTHON_PYHOST_CSAFERUNNER_SRC_VARIANT_H_FB54E4571FA611E4BE9C84383555E6CC
#define RUNLIB_PYTHON_PYHOST_CSAFERUNNER_SRC_VARIANT_H_FB54E4571FA611E4BE9C84383555E6CC

#include <string>
#include <iosfwd>
#include <memory>

/// @brief Raised when given `Variant` cannot convert to desired type.
class ConversionError {};

/// @brief The base class for all Variant objects
class Variant
{
public:
  Variant();
  virtual ~Variant();

  // check if desired value is given type
  virtual bool isNull() const { return false; }
  virtual bool isInt() const { return false; }
  virtual bool isDouble() const { return false; }
  virtual bool isString() const { return false; }

  // extract variant values
  virtual int asInt() const { throw ConversionError(); }
  virtual double asDouble() const { throw ConversionError(); }
  virtual std::string asString() const { throw ConversionError(); }

  // Write given value to json output stream
  // This method should output "full" representation of Json value
  virtual void writeJson(std::ostream *os) const = 0;
};

typedef std::shared_ptr<Variant> VariantPtr;

/// @brief Variant object for null
class NullObject : public Variant
{
public:
  NullObject();

  virtual bool isNull() const { return true; }
  virtual void writeJson(std::ostream *os) const;

  static VariantPtr New() {
    return VariantPtr(new NullObject());
  }
};

/// @brief Variant object for int values
class Integer : public Variant
{
public:
  Integer(int value);

  virtual bool isInt() const { return true; }
  virtual int asInt() const { return value_; }
  virtual void writeJson(std::ostream *os) const;

  static VariantPtr New(int value) {
    return VariantPtr(new Integer(value));
  }
private:
  int value_;
};

/// @brief Variant object for double values
class Double : public Variant
{
public:
  Double(double value);

  virtual bool isDouble() const { return true; }
  virtual double asDouble() const { return value_; }
  virtual void writeJson(std::ostream *os) const;

  static VariantPtr New(double value) {
    return VariantPtr(new Double(value));
  }
private:
  double value_;
};

// @brief Variant object for string values
class String : public Variant
{
public:
  String(std::string const& value);

  virtual bool isString() const { return true; }
  virtual std::string asString() const { return value_; }
  virtual void writeJson(std::ostream *os) const;

  static VariantPtr New(std::string const& value) {
    return VariantPtr(new String(value));
  }
private:
  std::string value_;
};

#endif // RUNLIB_PYTHON_PYHOST_CSAFERUNNER_SRC_VARIANT_H_FB54E4571FA611E4BE9C84383555E6CC
