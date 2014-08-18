// @file: runlib/python/pyhost/CSafeRunner/src/apiclient.h
// ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
// This file is released under BSD 2-clause license.

#ifndef RUNLIB_PYTHON_PYHOST_CSAFERUNNER_SRC_APICLIENT_H_4E9786231FBF11E4960284383555E6CC
#define RUNLIB_PYTHON_PYHOST_CSAFERUNNER_SRC_APICLIENT_H_4E9786231FBF11E4960284383555E6CC

#include <string>
#include "score.h"

/// @brief Remote API client
class ApiClient
{
public:
  ApiClient(std::string const& baseUrl, std::string const& commKey);
  ~ApiClient();

  // Post final score to remote api
  void report(HwScore const& score);

private:
  // NOTE: in order not to include curl.h, I hardcoded typedef void CURL;
  void* curl_;

  // The base url of all api routines.
  std::string baseUrl_;

  // The comm key of remote api
  std::string commKey_;

  // Do POST and get result
  std::string doPOST(std::string const& action, std::string const& payload);

  // Callback to append data at end of string
  static size_t curlWriteData(char* ptr, size_t size, size_t nmemb, void* obj);
};

#endif // RUNLIB_PYTHON_PYHOST_CSAFERUNNER_SRC_APICLIENT_H_4E9786231FBF11E4960284383555E6CC
