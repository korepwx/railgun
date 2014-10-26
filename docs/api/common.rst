Common Library
==============

.. module:: railgun.common

This part of the documentation describes the common library.
All of the components, including the runner, the website, and
even the submitted program, can import this module.


Homework Definition
-------------------

.. automodule:: railgun.common.hw

.. autoclass:: railgun.common.hw.FileRules

    .. autoattribute:: ACCEPT

    .. autoattribute:: LOCK

    .. autoattribute:: HIDE

    .. autoattribute:: DENY

    .. automethod:: get_action

    .. automethod:: append_action

    .. automethod:: prepend_action

    .. automethod:: filter

    .. automethod:: parse_xml

.. autoclass:: railgun.common.hw.HwInfo
    :members:

.. autoclass:: railgun.common.hw.HwScorerSetting
    :members:

.. autoclass:: railgun.common.hw.HwCode
    :members:

.. autoclass:: railgun.common.hw.Homework
    :members:

.. autoclass:: railgun.common.hw.HwSet
    :members:

.. autoclass:: railgun.common.hw.HwPartialScore
    :members:

.. autoclass:: railgun.common.hw.HwScore
    :members:

.. autofunction:: railgun.common.hw.parse_bool


AES Encryption
--------------

.. automodule:: railgun.common.crypto

.. autoclass:: railgun.common.crypto.AESCipher
    :members:
    :inherited-members:

.. autofunction:: railgun.common.crypto.EncryptMessage

.. autofunction:: railgun.common.crypto.DecryptMessage


CSV Object Parser
-----------------

.. automodule:: railgun.common.csvdata

.. autoclass:: railgun.common.csvdata.CsvField
    :members:

.. autoclass:: railgun.common.csvdata.CsvInteger
    :members:

.. autoclass:: railgun.common.csvdata.CsvString
    :members:

.. autoclass:: railgun.common.csvdata.CsvFloat
    :members:

.. autoclass:: railgun.common.csvdata.CsvBoolean
    :members:

.. autoclass:: railgun.common.csvdata.CsvSchema
    :members:


DateTime Utility
----------------

.. automodule:: railgun.common.dateutil
    :members:


FileSystem and Path Utility
---------------------------

.. automodule:: railgun.common.fileutil
    :members:


Translation Utility
-------------------

.. automodule:: railgun.common.lazy_i18n
    :members:


Operation System Utility
------------------------

.. automodule:: railgun.common.osutil
    :members:


Python Language Utility
-----------------------

.. automodule:: railgun.common.pyutil
    :members:

Temporary Directory Utility
---------------------------

.. automodule:: railgun.common.tempdir
    :members:


URL Utility
-----------

.. automodule:: railgun.common.url
    :members:

