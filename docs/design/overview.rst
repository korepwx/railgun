.. _design_overview:

Technique Overview
==================

System Outline
--------------

Railgun system can be divided into three parts: the :token:`website`, the :token:`runner queue`, and the :token:`runner host`.

The :token:`website` is the only connection between users and the system.  Students can sign up, sign in, edit their profiles, download their homework, upload their submissions, view the evaluations, and download the uploaded files.  Also, the administrators can manage all the users and submissions, and generate the score sheets.

There's one more functionality of the website: it provides the necessary api for the runner host to report scores of the submissions.

The :token:`runner queue` stores all pending submissions, and launch the runner hosts to do evaluations.  It usually does not give out scores, unless the submitted program couldn't be launched, or some else errors occurred.

The :token:`runner host` is the actual subsystem to evaluate student submissions.  Student uploaded code wouldn't be executed until a runner host is launched.  These runner hosts usually runs at a low privilege to protect the system from injections.  After the student code has been executed, the runner hosts then collects the statistics to give out scores, and report back to the system via website api.

Lots of techniques have been used to keep away from exploits.  See :ref:`away_from_exploit` for more details.

Directory Structure
-------------------

The following block shows a simplified tree of directory structure.  Only the most important directories and files are listed here.  Some directories may not appear in the code repository, and you may create it yourself::

    railgun
    |-- config              : Non-versioned config dir.
    |   |-- general.py      : Config values shared by all components,
    |   |                     overwrite `/config.py`.
    |   |-- runner.py       : Config values for the runner queue & host,
    |   |                     overwrite `/railgun/runner/runconfig.py`.
    |   |-- users.csv       : Built-in user definition file.  Defaultly
    |   |                     enabled by `/railgun/website/webconfig.py`.
    |   +-- website.py      : Config values for the website, overwrite
    |                         `/railgun/website/webconfig.py`.
    |-- docs                : Sources of documentation.
    |-- hw                  : Built-in homework definitions.
    |                         You may select another dir by change
    |                         `config.HOMEWORK_DIR`.
    |-- keys                : Directory for secret keys (chmod to 0700).
    |   |-- commKey.txt     : Secret key to encrypt the payload of api.
    |   |-- redisKey.txt    : Secret key of the redis server.
    |   |-- sqlKey.txt      : Secret key of database server.
    |   +-- webKey.txt      : Secret key to store cookies on browsers.
    |-- logs                : Directory for log files (chmod to 0700).
    |-- railgun             : Root of Railgun source files.
    |   |-- common          : Common utilities.
    |   |-- maintain        : Manage utilities.
    |   |-- runner          : Implementations of the runner queue.
    |   |-- userhost        : Server to distribute system accounts.
    |   |                     To enable multi-process runner queue,
    |   |                     you must launch a system account server
    |   |                     to assign user ids to different runner
    |   |                     hosts.
    |   +-- website         : Implementations of the website.
    |-- runlib              : The libraries and sandbox for runner hosts.
    |   +-- python          : Python runner hosts.  This includes a safe
    |                         runner for Python submissions.
    |-- sql                 : Example initial sql scripts.
    |-- tests               : Unit tests.
    |-- tmp                 : Parent of all temp dir for runner hosts.
    |                         You may select another dir by change
    |                         `config.TEMPORARY_DIR`.
    |-- upload              : Directory to store student submissions.
    |                         You may select another dir by change
    |                         `config.UPLOAD_STORE_DIR`.
    |-- manage.py           : Main entry of manage utitlies.
    |-- requirements.txt    : Dependency of Railgun.
    |-- runner.py           : Script to launch the runner queue.
    |-- runtests.py         : Script to run all unit tests.
    |-- userhost.py         : Script to launch the account server.
    +-- website.py          : Script to launch the website.

RunQueue & RunHost
------------------

.. _away_from_exploit:

Away from Exploit
-----------------

I18n Everywhere
---------------

Other Topics
------------
