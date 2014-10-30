.. _design_overview:

Technique Overview
==================

System Outline
--------------

Railgun system can be divided into three parts: the :ref:`website_package`, the :ref:`runner_package`, and the :ref:`runlib_package`.

The :ref:`website_package` is the only connection between users and the system.  Students can sign up, sign in, edit their profiles, download their homework, upload their submissions, view the evaluations, and download the uploaded files.  Also, the administrators can manage all the users and submissions, and generate the score sheets.

There's one more functionality of the website: it provides the necessary api for the runner host to report scores of the submissions.

The :ref:`runner_package` stores all pending submissions, and launch the runner hosts to do evaluations.  It usually does not give out scores, unless the submitted program couldn't be launched, or some else errors occurred.

The :ref:`runlib_package` is the actual subsystem to evaluate student submissions.  Student uploaded code wouldn't be executed until a runner host is launched.  These runner hosts usually runs at a low privilege to protect the system from injections.  After the student code has been executed, the runner hosts then collects the statistics to give out scores, and report back to the system via website api.

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


.. _away_from_exploit:

Away from Exploit
-----------------

As an online judger that gives scores to the students, security is indeed one of the most important topics.  We must design the system carefully so that the database will not be filled with fake scores.

However, as is mentioned in :ref:`requirement`, we have so many different ways to evaluate a software engineering homework submission.  So I decided to run every submission in a separated process, use a homework provided script to generate the scores in that process, and to send the score back to database via :ref:`design_webapi`.

To protect the system from being exploit under such a framework, I mainly takes the advantage of system accounts, and thus forms a number of safety guards.

The first critical guard is to run the submission process at a low-privilege system account.  This is efficient and powerful, in that we can protect our whole computer system by such a simple strategy.  Furthermore, if we want to run multiple submissions on a single machine simultaneously, we can also create multiple system accounts, and run each submission at a dedicated account.

In order to assign each submission process a different system account, we must run our :ref:`runner_package` at root privilege, so that we can use `setuid` and `setgid` to downgrade the processes to desired users.  This is not done in the :ref:`runner_package` itself, instead it sets some environmental variables to tell the submission process (we call it a :ref:`runlib_package`) which user they should `setuid` to, since the :ref:`runlib_package` may want to do some extra preparation before the downgrading.

You may refer to :class:`~railgun.runner.host.BaseHost` to see how the process is launched.  In addition, if you want to enable the dedicated system account for each simultaneous submission process, you may refer to :mod:`railgun.userhost` and :mod:`railgun.runner.credential`.

The second guard is to use the encrypted website api.  We want to send back scores in the same process that the user submitted code are running; this is dangerous, because the users may construct a fake score and send to our system.

To make sure the posted score is reliable, we use AES to encrypt the whole communication, while the secret key is stored in a disk file readable only by `root` users.  Because of this, the user code will not have the chance to get in touch with the key after the privilege has been downgraded.  You may refer to the source code of :ref:`Python SafeRunner <python_saferunner>` to learn more about this behaviour.

Finally, to make sure the safety guards are working properly, you may turn on ``config.RUNNER_CHECK_PERM``.  If it is enabled, the file system permissions will be detected at the startup of :ref:`runner_package`.  You may refer to the source code of :mod:`railgun.runner.context` to see more explanation.


.. _i18n_everywhere:

I18n Everywhere
---------------

When I started to draft the Railgun system, I decided to support multi-language for everything, even for the detailed reports of evaluated submissions.

This is not a trivial task.  I must be careful when I'm playing with the texts.  All string literals must be wrapped by a :func:`~flask.ext.babel.gettext`, while the global constants must be wrapped with :func:`~flask.ext.babel.lazy_gettext`.

When it comes to the serialization and transfer of such translated string, things become much more complex.  :func:`~flask.ext.babel.lazy_gettext` will make a :class:`speaklater._LazyString` object, which amazingly holds the function object to generate the translated string!  How can I serialize a Python function and deserialize it in C++ and Java?

So I implemented my own :class:`~railgun.common.lazy_i18n.GetTextString`.  This helps a lot, since it can be serialized to and deserialized from JSON objects.  Perhaps the last inconvenient thing is that :func:`railgun.common.lazy_i18n.lazy_gettext` has the exact same name with :func:`flask.ext.babel.lazy_gettext`, since sometimes it confuses me a lot.
