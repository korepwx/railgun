// @file: runlib/python/pyhost/CSafeRunner/src/main.cpp
// ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
// This file is released under BSD 2-clause license.

#include <cmath>
#include <boost/python.hpp>
#include "pyhost.h"

int main(int argc, char** argv)
{
  PyHostInit();
  try {
    Py_Main(argc, argv);
  } catch (boost::python::error_already_set) {
    PyErr_Print();
  }
  PyHostDestroy();
  return 0;
}
