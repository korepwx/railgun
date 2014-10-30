Configuration
=============

Build-in Config Files
---------------------

Railgun comes along with some built-in config files::

    railgun
    |-- railgun
    |   |-- website
    |   |   +-- webconfig.py
    |   +-- runner
    |       +-- runconfig.py
    +-- config.py

The ``config.py``, ``railgun/website/webconfig.py`` and ``railgun/runner/runconfig.py`` are build-in config files which are version controlled by git.  They define the basic yet default values of the configuration items.

These 3 config files are targeted to different part of the system.  ``config.py`` determines the behaviour of all components, including the :ref:`common_package`, the :ref:`website_package`, the :ref:`runner_package`, the :ref:`runlib_package` and even the :ref:`userhost_package`.

In addition to ``config.py``, the :ref:`website_package` takes ``railgun/website/webconfig.py`` as the extra config file.  It can overwrite the values in ``config.py``.  Similarly, the :ref:`runner_package` takes ``railgun/runner/runconfig.py`` as the extra config file.


Customize the Config Files
--------------------------

The build-in files provides a basis of the configuration values.  However, it's not convenient to edit these files directly, since they are version controlled by git.  To ease the deployment, I introduced the custom config directory, where all subfiles will not be tracked by git::

    railgun
    +-- config
        |-- general.py
        |-- website.py
        +-- runner.py

There are 3 files under ``config`` directory.  The ``general.py`` will overwrite all values in ``config.py``,
the ``website.py`` will overwrite ``railgun/website/webconfig.py``, and the ``runner.py`` will overwrite ``railgun/runner/runconfig.py``.

Be careful when you are playing with ``general.py``!  Remember, it can only overwrite the values in ``config.py``, not ``railgun/website/webconfig.py`` or ``railgun/runner/runconfig.py``.  For example, if you store the following content in ``general.py``::

    DEBUG = True

It will not affect the `DEBUG` value in ``railgun/website/webconfig.py``.


Access the Config in Code
-------------------------

Given the organization of the config files, you should have different ways to access the config value in different parts of the system.

In the :ref:`common_package`, the :ref:`runlib_package` and the :ref:`userhost_package`, you should import `config` module and access the config attributes, for example::

    import config

    print config.WEBSITE_BASEURL

In the :ref:`runner_package`, you should import `runconfig` instead of `config`, for example::

    from railgun.runner import runconfig

    print runconfig.BROKER_URL

In the :ref:`website_package`, things become a bit more different.  You should access the config values via :data:`~railgun.website.context.app` instead of the `webconfig` module.  For example::

    from railgun.website.context import app

    print app.config['SQLALCHEMY_DATABASE_URI']

The way to access the config is very important!  You should always use the correct way to read these values.
