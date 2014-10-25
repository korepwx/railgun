.. _installation:

Installation
============

Basic Setup
-----------

The basic setup instruction will guide you to setup the Railgun system
on a development server.

Debian 7.0
~~~~~~~~~~

First, let's setup all the dependency by apt-get:

.. code-block:: bash

    sudo apt-get install python python-virtualenv python-pip    \
        python-dev cmake libboost-python-dev build-essential    \
        git libxml2-dev libxslt1-dev libcrypto++-dev            \
        libcurl4-openssl-dev libmysqlclient-dev

Then let's checkout the source code from github:

.. code-block:: bash

    git clone https://github.com/korepwx/railgun.git

The first thing to do with the source code is to compile the `SafeRunner`.
`SafeRunner` is the sandbox of Python judger.

.. code-block:: bash

    cd runlib/python/pyhost/CSafeRunner
    mkdir -p build
    cd build
    cmake ..
    make               
    cp SafeRunner ../../../../..

Each time you update the source code of `SafeRunner` (for example, pulling
from github), you should run ``cmake .. && make``, and copy the `SafeRunner`
to root directory of railgun.

The second thing to do is to setup Python virtual environment for Railgun
system.  Change to the root directory of Railgun, and execute:

.. code-block:: bash

    virtualenv env
    . env/bin/activate
    pip install -r requirements.txt

After all the Python requirements are installed, you may run the website by:

.. code-block:: bash

    . env/bin/activate
    python website.py

The error logs will be output to ``logs/website.log``.  However, if you wish
to view the logs on screen, and to enable the website to auto-relaunch after
any modifications to the code, you may execute:

.. code-block:: bash

    mkdir -p config
    echo "DEBUG = True" >> config/website.py
    echo "DEBUG_TB_INTERCEPT_REDIRECTS = False" >> config/website.py

Then you may restart ``website.py``.

To start the runner queue, you will need to install the Redis server as
the efficient job queue:

.. code-block:: bash

    sudo apt-get install redis-server

If you wish to support the extraction of rar files, you will need to install
`unrar`.
Be sure that `non-free` is enabled in your Debian sources.  A typical sources
list (``/etc/apt/sources.list``) for Debian 7.0 with `non-free` enabled may
be like::

    deb http://mirrors.aliyun.com/debian/ wheezy main contrib non-free
    deb-src http://mirrors.aliyun.com/debian/ wheezy main contrib non-free

    deb http://security.debian.org/ wheezy/updates main contrib non-free
    deb-src http://security.debian.org/ wheezy/updates main contrib non-free

    # wheezy-updates, previously known as 'volatile'
    deb http://mirrors.aliyun.com/debian/ wheezy-updates main contrib non-free
    deb-src http://mirrors.aliyun.com/debian/ wheezy-updates main contrib non-free

Then you may execute the following commands:

.. code-block:: bash

    sudo apt-get install unrar

.. note::

    The package name is `unrar`, not `unrar-free`!  The latter one is not
    compatible with the Python package `rarfiles`.

After all the dependencies are correctly installed, you may start the runner
queue by the following commands:

.. code-block:: bash

    . env/bin/activate
    python runner.py

The final step is to create a default admin account.  Create a new file
``config/users.csv`` and copy the following text into this file::

.. code-block:: csv

    name,password,email,admin
    "admin","pbkdf2:sha1:1000$aWa1MeYA$812c7fe6cfa00060b6e3fe0dfbbe99da98b6d1eb","admin@example.org",True

Open a web browser and navigate to
`http://localhost:5000 <http://localhost:5000>`_, and you may log into the
system by `admin` account, of which the password is `admin123`.
