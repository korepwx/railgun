.. _design_webapi:

Website API
===========

.. _list_of_api:

List of APIs
------------

First, let's list all the API views in the following table:

.. tabularcolumns:: |p{9cm}|p{6cm}|

=============================================== ========================================
View Function                                   Description
=============================================== ========================================
:func:`railgun.website.api.api_handin_report`   Store the detailed reports of a given
                                                submission.
:func:`railgun.website.api.api_handin_start`    Change the state of a given submission
                                                from `Pending` to `Running`.
:func:`railgun.website.api.api_handin_proclog`  Update the process output of a given
                                                submission.
:func:`railgun.website.api.api_myip`            Display the visitor's ip address.
=============================================== ========================================


Protocol
--------

A request from the client is carried in a standard HTTP request, while the
result is sent back in the HTTP response.

The request from client may carry important objects that must not be revealed
to student users.  These objects should be serialized in JSON format, encrypted
by AES crypto, and sent to the server through a POST request.  Moreover, the
POST requests should carry an additional header::

    Content-Type: application/octet-stream

To create compatible encrypted data with Railgun system, you may refer to
:class:`railgun.common.crypto.AESCipher`.


Object Types
------------

Basic Types
~~~~~~~~~~~

Since the objects are serialized in JSON format, the following tables shows
all the basic types in a JSON message:

.. tabularcolumns:: |p{4cm}|p{11cm}|

=============== ================================================
Type            Description
=============== ================================================
boolean         :token:`true` or :token:`false`.
int             Integral number literals.
float           Real number literals.
string          String literals surrounded by pairs of "``"``".
list            A sequence of objects separated by "``,``", while
                the whole literal surrounded by "``[``" and "``]``",
                for example::

                    [1, 2.0, 3e-8, true, "Alice", []]

dict            A collection of ``"name": object`` separated by
                "``,``", while the whole literal surrounded by "``{``"
                and "``}``", for example::

                    {"int": 1, "float": 2.0, "bool": true,
                     "string": "Alice", "list": [3e-8],
                     "dict": {}}
=============== ================================================

.. _json_GetTextString:

GetTextString
~~~~~~~~~~~~~

:class:`railgun.common.lazy_i18n.GetTextString` could be encoded to
JSON format.  For example, if we have the following
:class:`~railgun.common.lazy_i18n.GetTextString` object::

    lazy_gettext('My name is %(name)s, and I am a %(nation)s',
                 name='Alice', nation='American')

Then we can serialize the object by
:func:`railgun.common.lazy_i18n.lazystr_to_plain`:

.. code-block:: javascript

    {
        "text": "My name is %(name)s, and I am a %(nation)s",
        "kwargs": {
            "name": "Alice",
            "nation": "American"
        }
    }

.. note::

    If `kwargs` is empty, you must keep an empty dict in the JSON serialized
    message.

.. _json_HwPartialScore:

HwPartialScore
~~~~~~~~~~~~~~

:class:`railgun.common.hw.HwPartialScore` could be encoded to JSON format.
The JSON object should follow the schema:

.. code-block:: javascript

    {
        "name": GetTextString or string,
        "typeName": string,
        "score": float,
        "weight": float,
        "time": float,
        "brief": GetTextString or string,
        "detail": [
            GetTextString or string,
            ...
        ]
    }

`GetTextString or string` means the mentioned attribute could either be
a :class:`~railgun.common.lazy_i18n.GetTextString` object, or a basic
string object.  However, it is always recommended to use a
:class:`~railgun.common.lazy_i18n.GetTextString` rather than basic string,
to provide translations to different users.

.. _json_HwScore:

HwScore
~~~~~~~

:class:`railgun.common.hw.HwScore` could be encoded to JSON format.
The JSON object should follow the schema:

.. code-block:: javascript

    {
        "accepted": boolean,
        "result": GetTextString or string,
        "compile_error": GetTextString or string,
        "partials": [
            HwPartialScore,
            ...
        ]
    }


Two Examples of HwScore
-----------------------

To make you better understand the transfered HwScore object, I'll show you
two examples.  The first one is an HwScore object for an `Accepted` submission,
while the latter one for a failure and `Rejected` submission.

HwScore for Accepted
~~~~~~~~~~~~~~~~~~~~

.. code-block:: json

    {
      "accepted": true, 
      "compile_error": {
        "text": "", 
        "kwargs": {}
      }, 
      "result": {
        "text": "Your submission is accepted.", 
        "kwargs": {}
      },
      "partials": [
        {
          "name": {
            "text": "InputClass Scorer", 
            "kwargs": {}
          },
          "typeName": "InputClassScorer",
          "time": 0.000146151,
          "score": 15.3846,
          "weight": 0.6,
          "brief": {
            "text": "%(rate).2f%% rules (%(cover)s out of %(total)s) covered", 
            "kwargs": {
              "rate": 15.3846, 
              "total": 13, 
              "cover": 2
            }
          }, 
          "detail": [
            {
              "text": "NOT COVERED: %(checker)s", 
              "kwargs": {
                "checker": "regular triangle"
              }
            }, 
            {
              "text": "NOT COVERED: %(checker)s", 
              "kwargs": {
                "checker": "isosceles triangle (a, b, c > 0) and (a == b != c)"
              }
            }
          ]
        }, 
        {
          "name": {
            "text": "BoundaryValue Scorer", 
            "kwargs": {}
          }, 
          "typeName": "BoundaryValueScorer", 
          "time": 6.79493e-05,
          "score": 0, 
          "weight": 0.4, 
          "brief": {
            "text": "%(rate).2f%% rules (%(cover)s out of %(total)s) covered", 
            "kwargs": {
              "rate": 0, 
              "total": 2, 
              "cover": 0
            }
          }, 
          "detail": [
            {
              "text": "NOT COVERED: %(checker)s", 
              "kwargs": {
                "checker": "zero data (one of a, b, c == 0)"
              }
            }, 
            {
              "text": "NOT COVERED: %(checker)s", 
              "kwargs": {
                "checker": "zero data (all of a, b, c == 0)"
              }
            }
          ]
        }
      ]
    }

HwScore for Rejected
~~~~~~~~~~~~~~~~~~~~

.. code-block:: json

    {
      "partials": [], 
      "accepted": false, 
      "compile_error": null, 
      "result": {
        "text": "Exitcode %(exitcode)s != 0.", 
        "kwargs": {
          "exitcode": -5
        }
      }
    }
