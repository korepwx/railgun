// @file: runlib/python/pyhost/CSafeRunner/src/apiclient.cpp
// ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
// This file is released under BSD 2-clause license.

#include <stdexcept>
#include <iostream>
#include <sstream>
#include <curl/curl.h>
#include "apiclient.h"
#include "crypto.h"

ApiClient::ApiClient(std::string const& baseUrl, std::string const& commKey)
: baseUrl_(baseUrl), commKey_(commKey)
{
  curl_ = curl_easy_init();
  if (!curl_)
    throw std::runtime_error("Cannot create CURL handle.");
}

ApiClient::~ApiClient()
{
  curl_easy_cleanup(curl_);
}

void ApiClient::report(HwScore const& score)
{
  // Construct the post data
  std::ostringstream oss;
  score.writeJson(&oss);
  AESCipher aes(commKey_);
  std::string cipher = aes.encrypt(oss.str());

  // Construct post action
  char action[128];
  std::string uuid_s;
  UnicodetoUTF8(score.uuid, &uuid_s);
  snprintf(action, sizeof(action), "/handin/report/%s/", uuid_s.c_str());

  // Do post
  std::string result = doPOST(action, cipher);
  if (result != "OK") {
    char exmsg[256];
    snprintf(exmsg, sizeof(exmsg), "Save result failed for handin(%s): %s.",
             uuid_s.c_str(), result.c_str());
    throw std::runtime_error(exmsg);
  }
}

size_t ApiClient::curlWriteData(char* ptr, size_t size, size_t nmemb, void* obj)
{
  size_t n = size * nmemb;
  std::string* target = (std::string*)obj;
  target->append(ptr, n);
  return n;
}

std::string ApiClient::doPOST(std::string const& action,
                              std::string const& payload)
{
  bool success = true;
  std::string url = baseUrl_ + action;
  struct curl_slist* headers = NULL;

  // CURL error buffer
  char errmsg[CURL_ERROR_SIZE];
  curl_easy_setopt(curl_, CURLOPT_ERRORBUFFER, errmsg);

  // Basic parameters
  curl_easy_setopt(curl_, CURLOPT_URL, url.c_str());
  curl_easy_setopt(curl_, CURLOPT_FOLLOWLOCATION, 1L);
  curl_easy_setopt(curl_, CURLOPT_POST, 1L);
  curl_easy_setopt(curl_, CURLOPT_POSTFIELDS, payload.data());
  curl_easy_setopt(curl_, CURLOPT_POSTFIELDSIZE, long(payload.size()));

  // Prepare HTTP headers list
  headers = curl_slist_append(
    headers, "Content-Type: application/octet-stream");
  curl_easy_setopt(curl_, CURLOPT_HTTPHEADER, headers);

  // Prepare for result obtaining
  std::string result;
  curl_easy_setopt(curl_, CURLOPT_WRITEDATA, &result);
  curl_easy_setopt(curl_, CURLOPT_WRITEFUNCTION, &ApiClient::curlWriteData);

  // Perform the request
  if (curl_easy_perform(curl_) != CURLE_OK) {
    success = false;
  }

  // Destroy all resources
  curl_slist_free_all(headers);

  // Throw exception, or return result
  if (!success) {
    char exmsg[64 + CURL_ERROR_SIZE];
    snprintf(exmsg, sizeof(exmsg), "Could not post to remote API: %s.", errmsg);
    throw std::runtime_error(exmsg);
  }
  return result;
}
