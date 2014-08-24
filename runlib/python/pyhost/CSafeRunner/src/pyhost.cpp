// @file: runlib/python/pyhost/CSafeRunner/src/pyhost.cpp
// ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
// This file is released under BSD 2-clause license.

// Because of some conflict between boost::python and C++11, we must include
// cmath and boost/python.hpp at the beginning of source file.
#include <cmath>
#include <boost/python.hpp>
namespace bp = boost::python;

// Include other C++ headers from here.
#include <stdlib.h>
#include <unistd.h>
#include <string>
#include <iostream>
#include <curl/curl.h>

// Project header files
#include "gettext.h"
#include "score.h"
#include "apiclient.h"

namespace
{
  // Flag to indicate whether SafeRunner.run is called twice
  bool PyHostExecuted = false;

  // Secret PyHost context variables
  std::string PyHostCommKey;
  int PyHostUserId = 0;
  int PyHostGroupId = 0;

  // General PyHost context variables
  std::string PyHostApiBaseUrl;
  std::string PyHostRailgunRoot;
  std::string PyHostHandId;
  std::string PyHostHwId;

  // Common Utilities
  std::string LoadCommKey(std::string const& railgun_root)
  {
    std::string commkey_file = railgun_root + "/keys/commKey.txt";

    // Load key from file
    FILE *fin = fopen(commkey_file.c_str(), "rb");
    if (!fin)
      throw std::runtime_error("Cannot load commKey.txt.");
    char keystr[1024];
    fgets(keystr, sizeof(keystr), fin);
    fclose(fin);

    // Strip newline marks at end of key
    int pos = strlen(keystr) - 1;
    while (pos >= 0 && (keystr[pos] == '\n' || keystr[pos] == '\r'))
      keystr[pos--] = 0;

    return std::string(keystr, pos+1);
  }

  std::string TypeName(bp::object const& obj)
  {
    return bp::extract<std::string>(obj.attr("__class__").attr("__name__"));
  }

  UnicodeString ExtractUnicode(bp::object const& obj)
  {
    UnicodeString ret;
    std::string objType = TypeName(obj);

    if (objType == "str") {
      UTF8toUnicode(bp::extract<std::string>(obj), &ret);
    } else {
      std::string s = bp::extract<std::string>(obj.attr("encode")("utf-8"));
      UTF8toUnicode(s, &ret);
    }
    return ret;
  }

  // TODO: add more type coversions here!
  VariantPtr ExtractVariant(bp::object const& obj)
  {
    if (obj.is_none()) {
      return NullObject::New();
    }
    std::string objType = TypeName(obj);
    if (objType == "int") {
      return Integer::New(bp::extract<int>(obj));
    } else if (objType == "float") {
      return Double::New(bp::extract<double>(obj));
    } else if (objType == "str" || objType == "unicode") {
      return Unicode::New(ExtractUnicode(obj));
    }

    char errmsg[128];
    snprintf(errmsg, sizeof(errmsg), "Could not convert %s to C++ variant.",
             objType.c_str());
    throw std::runtime_error(errmsg);
  }

  void FillLazyString(bp::object const& obj, GetTextString *target)
  {
    target->text.clear();
    target->kwargs.clear();

    if (obj.is_none())
      return;
    std::string objType = TypeName(obj);

    // Convert pure string / unicode to lazy string
    if (objType == "str" || objType == "unicode") {
      target->text = UTF8toUnicode("%(RAW_MESSAGE)s");
      target->kwargs[UTF8toUnicode("RAW_MESSAGE")] =
        Unicode::New(ExtractUnicode(obj));
      return;
    }

    // Extract GetTextString instance
    target->text = ExtractUnicode(obj.attr("text"));
    bp::dict kwargs = bp::extract<bp::dict>(obj.attr("kwargs"));
    bp::list keys = kwargs.keys();

    for (bp::ssize_t i=0; i<bp::len(keys); ++i) {
      UnicodeString key = ExtractUnicode(keys[i]);
      target->kwargs[key] = ExtractVariant(kwargs[keys[i]]);
    }
  }

  void RunScorers(bp::list const& scorers)
  {
    // Prevent user handin from calling this routine again.
    if (PyHostExecuted) {
      throw std::runtime_error(
        "You cannot call SafeRunner.run twice in a same process!"
      );
    }
    PyHostExecuted = true;

    // The returned score object
    HwScore score;
    UTF8toUnicode(PyHostHandId, &score.uuid);
    score.accepted = false;

    try {
      // Run each scorer to evaluate the handin
      bp::ssize_t n = bp::len(scorers);

      if (!n) {
        score.result = GetTextString("No scorer defined, please contact TA.");
      }
      for (bp::ssize_t i=0; i<n; ++i) {
        bp::tuple scorer_weight = bp::extract<bp::tuple>(scorers[i]);
        bp::object scorer = scorer_weight[0];
        double weight = bp::extract<double>(scorer_weight[1]);

        // Run the scorer!
        scorer.attr("run")();

        // Extract scorer results
        HwPartialScore partial;
        FillLazyString(scorer.attr("name"), &partial.name);
        UTF8toUnicode(TypeName(scorer), &(partial.typeName));
        partial.score = bp::extract<double>(scorer.attr("score"));
        FillLazyString(scorer.attr("brief"), &partial.brief);

        // The details should be list instance
        bp::object detail = scorer.attr("detail");
        bp::ssize_t detail_n = bp::len(detail);
        for (bp::ssize_t j=0; j<detail_n; ++j) {
          GetTextString lazystr;
          FillLazyString(detail[j], &lazystr);
          partial.detail.push_back(lazystr);
        }

        // Set other properties
        partial.weight = weight;
        partial.time = ExtractVariant(scorer.attr("time"));

        // Add this partial score the total scorer
        score.partials.push_back(partial);
      }

      // We've now run all scorers, accept this score
      score.accepted = (n > 0);

    } catch (UnicodeError) {
      score = HwScore();
      UTF8toUnicode(PyHostHandId, &score.uuid);
      score.accepted = false;
      score.result = GetTextString("Not valid UTF-8 sequence produced.");
    }

    // Post the score object to remote API
    ApiClient client(PyHostApiBaseUrl, PyHostCommKey);
    client.report(score);
  }

  // Parse an environmental variable into int.
  int env2int(const char* name, int default_value = 0)
  {
    const char* value = getenv(name);
    if (!value)
      return default_value;
    return atoi(value);
  }
}

BOOST_PYTHON_MODULE(SafeRunner)
{
  bp::def("run", &RunScorers);
}

// Initialize the PyHost context
void PyHostInit()
{
  // Initialize the CURL library
  curl_global_init(CURL_GLOBAL_ALL);

  // Save some environment variables
  PyHostApiBaseUrl = getenv("RAILGUN_API_BASEURL");
  PyHostRailgunRoot = getenv("RAILGUN_ROOT");
  PyHostHandId = getenv("RAILGUN_HANDID");
  PyHostHwId = getenv("RAILGUN_HWID");

  // Get user id and group id that this process should run at.
  PyHostUserId = env2int("RAILGUN_USER_ID");
  PyHostGroupId = env2int("RAILGUN_GROUP_ID");

  // Load comm key from keys/commKey.txt
  PyHostCommKey = LoadCommKey(PyHostRailgunRoot);

  // Downgrade user privilege
  if (PyHostGroupId != 0) {
    if (setgid(PyHostGroupId) != 0) {
      fprintf(stderr, "Could not set gid to %d.", PyHostGroupId);
      exit(-1);
    }
  }
  if (PyHostUserId != 0) {
    if (setuid(PyHostUserId) != 0) {
      fprintf(stderr, "Could not set uid to %d.", PyHostUserId);
      exit(-1);
    }
  }

  // Initialize the Python interpreter
  Py_Initialize(); 

  // Import `SafeRunner` module into Python interpreter
  initSafeRunner();
}

// Destroy the pyhost context
void PyHostDestroy()
{
  Py_Finalize();
  curl_global_cleanup();
}
