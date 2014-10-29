.. _runner_package:

Runner Queue
============

.. module:: railgun.runner

This part of the documentation describes the runner package.
It includes all details about the runner queue.


Celery Context Object
---------------------

.. automodule:: railgun.runner.context
    :members:


Tasks of the Runner
-------------------

.. automodule:: railgun.runner.tasks
    :members:

    .. autofunction:: railgun.runner.tasks.run_python(handid, hwid, upload, options)

    .. autofunction:: railgun.runner.tasks.run_netapi(handid, hwid, remote_addr, options)

    .. autofunction:: railgun.runner.tasks.run_input(handid, hwid, csvdata, options)


Handlers of Submissions
-----------------------

.. automodule:: railgun.runner.handin
    :members:


Hosts of the Runners
--------------------

.. automodule:: railgun.runner.host
    :members:


Request for a System Account
----------------------------

.. automodule:: railgun.runner.credential
    :members:


Common Submission Errors
------------------------

.. automodule:: railgun.runner.errors
    :members:


Client of the Website API
-------------------------

.. automodule:: railgun.runner.apiclient
    :members:


Preloaded Homework Objects
--------------------------

.. automodule:: railgun.runner.hw
    :members:
