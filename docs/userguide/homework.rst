.. _homework:

Homework
========

The `Railgun Source Code`_ contains some example homework in ``HOMEWORK_DIR``.
To start drafting your own homework, you may copy the files from the example
which close to your needs mostly.

This page intends to give you some more details about the homework.

.. _Railgun Source Code: https://github.com/korepwx/railgun

.. _hwoutline:

Outline
-------

Although the scores of submissions are stored in database, homework
is not.  All data of homework are stored in the directory configured in
``config.py`` as following::

    # HOMEWORK_DIR stores the definitions of homework
    HOMEWORK_DIR = os.path.join(RAILGUN_ROOT, 'hw')

Each directory under ``HOMEWORK_DIR`` carrying ``hw.xml`` will be treated
as a homework item.  The directory tree of a typical item may be like this::

    reform_path
    +-- code
    |   +-- python
    |       +-- code.xml
    |       +-- path.py
    |       +-- run.py
    +-- desc
    |   +-- en.md
    |   +-- img
    |   |   +-- python-logo.png
    |   +-- zh-cn.md
    +-- hw.xml

``hw.xml`` is the definition file for the homework.  Guided by ``hw.xml``,
``desc`` directory carries the descriptions of homework in different locales.
Since that Railgun is designed to allow the students to use different
programming languages when solving a single question, ``code`` directory
stores all the code files and resources for these languages, each in an
individual folder.
You may head over to :ref:`hwstruct` to learn more.

Students can download attachments from the homework information pages.
You don't need to pack up these attachments by hand, in that Railgun will
do it for you.  It will pack all files for particular programming language
in ``code`` directory along with the resource files at the root of homework
into zip archive files.  Students can thus choose their preferred programming
language and download the archive files to start their work.
You may head over to :ref:`hwpack` to learn more.

After the students have handed in their submissions, Railgun will judge their
work.  As an online judger for Software Enginneering, Railgun uses a very
handy method to obtain the greatest compatibility for different programming
languages: it runs each submission as an external process, while the judging
is done in that process rather than Railgun.  The score is then sent back
to Railgun through Json API in AES encrypted channel.  Because of this,
you must provide runnable entries for each programming language of homework.
You may head over to :ref:`hwjudge` to learn more.

The rest of this page reveals everything you will need to know when you'd
like to write judgement code for particular programming language.
This includes all technical details about :ref:`hwpython`, :ref:`hwnetapi`
and :ref:`hwinput`, as well as some :ref:`hwnotes`.

.. _hwstruct:

File Structure
--------------

The most basic component of a homework item is ``hw.xml``.  It defines the
unique id of homework, which associates the submissions in database with
the homework on disk.  It also defines the localized names of homework,
the submission deadlines, and the score scale at each deadline.

What's more, it determines what information should be revealed to the
students: whether or not the students can view the standard output of
process, which files should be given to students and which shouldn't.

Here's a basic example of ``hw.xml`` provided by `Railgun Source Code`_:

.. code-block:: xml

    <?xml version="1.0"?>
    <homework>
      <uuid>b388ad5b25ee44bbac9be46c43851768</uuid>
      <names>
        <name lang="zh-cn">(Some Chinese name)</name>
        <name lang="en">Format Path</name>
      </names>
      <deadlines>
        <due>
          <timezone>Asia/Shanghai</timezone>
          <date>2014-8-11 23:59:59</date>
          <scale>1.0</scale>
        </due>
        <due>
          <timezone>Asia/Shanghai</timezone>
          <date>2014-8-21 23:59:59</date>
          <scale>0.5</scale>
        </due>
        <due>
          <date>2014-8-31 23:59:59</date>
          <scale>0.0</scale>
        </due>
      </deadlines>
      <files />
    </homework>

All nodes in ``hw.xml`` showed above are essential.  Both the website of
Railgun and the background runner will refuse to start up if it lacks
anything.  The functionality of the nodes are described in the following
table:

.. tabularcolumns:: |p{4cm}|p{11cm}|

================== =========================================================
Node Name          Description
================== =========================================================
uuid               Unique id of this piece of homework.  Although the
                   website uses directory name in the url, it relies on
                   ``uuid`` to associate submissions with certain
                   homework.  If and only if ``uuid`` matches, two
                   pieces of homework will be treated as one.
                   You may change the ``uuid`` in ``hw.xml``, so as to
                   clear all submissions in the database.

                   You may execute
                   ``python -c 'import uuid; print uuid.uuid4().get_hex()'``
                   to generate a new randomized ``uuid``.
name               Define the name of this piece of homework in a
                   certain locale.  The website will try to choose
                   a best matching name according to the locale of user.
                   If no name can match the user, then the name for the
                   default locale (specified in ``config.py``) will be
                   selected.  If still no name can match, the last name
                   will be choosed.
due                Define a deadline of this piece of homework.  There
                   may be two or three sub nodes in a ``due`` node:

                   *   ``date``: The due date of this deadline.
                   *   ``scale``: The score scale of this deadline.
                       The final score of submissions will be scaled
                       by this factor before the deadline.
                   *   ``timezone``: Optional node to point out the
                       timezone of ``date`` node.  If not given, the
                       default timezone in ``config.py`` will be used.
files              Archive packing rules for the files in root directory.
                   Head over to :ref:`hwpack` for more details.
================== =========================================================

Besides localized names, homework should provide localized descriptions
as well.  The localized descriptions should be placed in ``[locale].md``
under ``desc`` directory.  There must exist a localized description for
each localized name.

To provide nice and clear descriptions for homework, you may need the
knowledge of `Markdown`_ language.  Railgun uses an extended flavour
which is very similar to `GitHub Flavoured Markdown`_.
You may head over to :ref:`hwdesc` to learn more.

.. _Markdown: http://en.wikipedia.org/wiki/Markdown
.. _GitHub Flavoured Markdown: https://help.github.com/articles/github-flavored-markdown

As is mentioned in :ref:`hwoutline`, Railgun is designed to allow students
solve the same question with different languages.  The definition files
for different languages are placed under ``code`` directory.  The name of
the directory determines what programming language it is.  Currently only
three programming languages are valid:

.. tabularcolumns:: |p{4cm}|p{11cm}|

=============== ==========================================================
Language        Description
=============== ==========================================================
python          Students may write Python programs and upload
                python script files to the server as submission.
                You may head over to :ref:`hwpython` to learn more.
netapi          Students should deploy a web application to a
                public accessible server, and submit the url
                address.
                You may head over to :ref:`hwnetapi` to learn more.
input           Students may provide a set of input values to
                perform a black-box test, where the data should
                be organized as csv data sheet.
                You may head over to :ref:`hwinput` to learn more.
=============== ==========================================================

Different programming languages may require various files to compose
the homework.  Among all of them, ``code.xml`` is the only one that
is essential in all languages.  An example of ``code.xml`` provided
by `Railgun Source Code`_ is:

.. code-block:: xml

    <?xml version="1.0"?>
    <code>
      <attachment>true</attachment>
      <compiler version="2.7" />
      <runner entry="run.py" timeout="3" />
      <reportCompile>false</reportCompile>
      <reportRuntime>false</reportRuntime>
      <files>
        <hide>^run\.py$</hide>
        <accept>^path\.py$</accept>
        <accept>.*\.py$</accept>
      </files>
    </code>

Like ``hw.xml``, all nodes in ``code.xml`` are essential.  The system
will refuse to start up if it lacks anything. The functionality of the
nodes are described in the following table:

.. tabularcolumns:: |p{4cm}|p{11cm}|

=============== =======================================================
Node Name       Description
=============== =======================================================
attachment      Whether this programming language provides
                downloadable archive for students?
                Some programming languages, such as ``input``
                for black-box test, may not provide an archive.
compiler        Parameters which will be passed to the compiler.
                Different programming languages may have
                different parameters.
runner          Parameters which will be passed to the runner.
reportCompile   Whether the website should display all compilation
                messages?  Enable this option may cause the homework
                judging code to be revealed in some programming
                languages.  You may head over to
                :ref:`hwpython`, :ref:`hwnetapi` and :ref:`hwinput`
                to see whether this parameter should be set to true
                or false.
reportRuntime   Whether the website should display all runtime details?
                When set to true, the process standard output,
                error output, and runtime log will be displayed to
                students.  Enable this option may cause
                the homework judging code to be revealed in some
                programming languages.  You may head over to
                :ref:`hwpython`, :ref:`hwnetapi` and :ref:`hwinput`
                to see whether this parameter should be set to true
                or false.
files           Archive packing rules for the files in this language
                directory.
                Head over to :ref:`hwpack` for more details.
=============== =======================================================

.. note::

    The Railgun website and the runner will load the homework definitions
    at boot time.  So if you updated the homework, you should restart
    the two applications.

.. _hwdesc:

Writing Description
-------------------

The syntax of `Markdown`_ can be easily retrieved on internet. The
extensions to original Markdown syntax is very similar to
`GitHub Flavoured Markdown`_.  There's only one important addition
to these two standards, which exposes static resources under ``desc``
directory to client browsers.

Suppose we have the following ``desc`` directory::

    desc
    +-- 1.jpg
    +-- en.md
    +-- img
        +-- 2.jpg

``en.md`` is the description for English locale.  We want to display
``1.jpg`` and ``2.jpg`` on homework page, thus we write::

    ![The first image](hw://1.jpg)
    ![The second image](hw://img/2.jpg)

Railgun will change all the urls beginning with ``hw://`` into
absolute http urls.  The url patterns are replaced full text, with
no analysis on Markdown syntax.  Any string matching the following
regular expression will be treated as ``hw://`` urls::

    hw://[A-Za-z0-9-_.~!\*';:@&=+$,/?#]*

There are two more things before the images can display correctly.
You should set the correct value for ``WEBSITE_BASEURL`` in
``config.py`` (or in ``config/general.py``, which is more recommended).
You should then execute ``Manage - Build Cache`` in the navigation
bar after you have logged into the website as an administrator.
This will gather all static resources in ``desc`` directories
into a single place, so as to be ready for browser requests.

.. _hwpack:

Archive Packing
---------------

On the homework page, students are given links to download the archive
file of their chosen programming language.  These archive files are
packed by Railgun according to homework definitions.  Different
programming languages will generate different archive files.

Suppose we have the following homework definition::

    example
    +-- code
    |   +-- java
    |   |   +-- code.xml
    |   |   +-- main.java
    |   |   +-- utility.java
    |   +-- python
    |       +-- code.xml
    |       +-- func.py
    |       +-- run.py
    +-- desc
    |   +-- en.md
    |   +-- zh-cn.md
    +-- hw.xml
    +-- readme.pdf

Railgun will then generate two archive files for this piece of
homework: ``java.zip`` and ``python.zip``.  If properly configured,
``java.zip`` may contain ``readme.pdf``, ``main.java`` and
``utility.java``, while ``python.zip`` may contain ``readme.pdf``,
``func.py`` and ``run.py``.

The basic rule for Railgun to generate the archive is that,
the archive file for a certain programming language only contains
the files from that language directory, and from the root directory
of the homework.  What's more, there're some files and directories
that will not be packed into the archive, such as ``hw.xml``,
``code.xml``, ``desc`` and ``code``.

However, these rules are far from enough.  You may intend to
have a more detailed control on which files to be packed and
which not.  For example, you may intend to hide ``run.py``
and provide only ``func.py`` to the students.

On the other hand, as is mentioned above at :ref:`hwoutline`,
after the students have uploaded their submissions, Railgun
will extract them somewhere and execute the programs.
However, you may not want the students to overwrite some of
your original code, such as the code in ``run.py``, in that
it will give the scores to the submissions.

Both these two goals can be achieved by the file packing rules
defined in ``hw.xml`` and in ``code.xml``.  For example, if
we have the following set of rules in ``code.xml``:

.. code-block:: xml

    <files>
      <accept>^func\.py$</accept>
      <lock>^run\.py$</lock>
      <hide>^secret\.py$</hide>
      <deny>^virus\.py$</deny>
    </files>

Railgun will pack ``func.py`` and ``run.py`` into the archive file, but
will only extract ``func.py`` from the submissions from students and
copy ``run.py`` from the original homework definition instead of
student provided version.  This protects the judging code from being
overwritten.

What's more, if there exists ``secret.py`` in code directory, it will
not be packed into the archive file, but will indeed be copied to
submission runtime directory.  At last, if ``virus.py`` appears in
student submissions, then these submissions will be rejected
immediately.

File packing rules control the behaviour of packing downloadable
homework archive file, and extracting code files from user uploaded
submissions.  All the rules should be carried in a single ``<files>``
node, in both ``hw.xml`` and ``code.xml``.  There are totally
4 types of actions taken by rules, as is mentioned above:

.. tabularcolumns:: |p{4cm}|p{11cm}|

=========== ==============================================================
Action      Description
=========== ==============================================================
accept      *   files will be packed into archive file.
            *   files can be overwritten by student submissions.
lock        *   files will be packed into archive file.
            *   files **CANNOT** be overwritten by student submissions.
hide        *   files **WILL NOT** be packed into archive file.
            *   files **CANNOT** be overwritten by student submissions.
deny        *   files **WILL NOT** be packed into archive file.
            *   the submissions carrying files matching this type
                of rules will be rejected.
=========== ==============================================================


.. note::

    The matching pattern of file rules are regular expressions.
    Be careful about the syntax!  You must add ``^`` at the
    beginning of the expression, and ``$`` at the end of the expression,
    if you want to match the whole file path.
    However, you may not following this restriction as your need.

Rules are distributed in two individual files: ``hw.xml`` and
``code.xml``.  Futhermore, there may be multiple rules in the same file.
All the rules in the same file are matched in definition order, and
the actions are taken immediately after any one rule is matched,
regardless of later rules.

When packing archive files, files from the root directory will be packed
first, according to the file rules in ``hw.xml``.  Then the files from
certain programming language will be packed later, according to
``code.xml``.  The behaviour is not specified if two files from different
directory conflicts, so please avoid such situations.

After the students have uploaded their submissions, files from the
root directory and the directory of certain programming language
will be copied to runtime directory first.  File rules are not tested
during this progress, and the Railgun system copies anything it can
find.  Later, files from the students will be extracted, and tested
by rules in the two files.  *Rules in* ``code.xml`` *will be tested
first, and if not matched,* ``hw.xml``.  Files not matching
any rules will be treated as if they have matched the ``lock`` rules.

.. note::

    Because of the nature order of extraction progress,
    student submitted files will overwrite original files unless the
    rules are specified correctly. You must take care when contructing
    the file matching rules.

In addition to user constructed file matching rules, there
are several ``hide`` rules pre-configured in ``config.py``, which
are superior to all user rules::

    DEFAULT_HIDE_RULES = (
        'Thumbs\\.db$',         # windows picture preview database
        '\\.DS_Store$',         # OS X directory meta
        '__MACOSX',             # OS X archive file meta data
        '^\\._.*$|/\\._.*$',    # OS X special backup files
        '\\.directory$',        # dolphin directory meta
        '\\.py[cdo]$',          # hide all python binary files
        '^(py|java)host.*',     # prevent runlib from overwritten
        '^railgun.*',           # prevent railgun lib from overwritten
    )

.. _hwjudge:

Judge Runner
------------

The submissions from the students will be extracted to a runtime
directory, and execute as an external program.  The program then
evaluate the submission, give out a score, and send back to
Railgun website.  This is the basic skeleton of how the judge
runner works.

The runtime directory is created and managed by the runner
in ``TEMPORARY_DIR``, specified in ``config.py``.  The name of
the runtime directory is same as the ``uuid`` of the submission,
which is generated by Railgun.  The default value of
``TEMPORARY_DIR`` is specified in ``config.py``::

    TEMPORARY_DIR = os.path.join(RAILGUN_ROOT, 'tmp')

where the runtime directory of a submission with given ``uuid``,
for example, ``440225a1db2e47bbbd377c0cbcc5caea``, should be::

    [TEMPORARY_DIR]/440225a1db2e47bbbd377c0cbcc5caea

After all the files have been copied and extracted into this
runtime directory, Railgun will compile the program if necessary.
The complication progress is not same for different programming
languages.

If the complication progress is successful, then the program is
executed.  The user code is then executed.  The judging code must
be designed carefully to prevent injections from the user code.
Downgrading the privileges is always a good idea.

.. note::
    Railgun will start the program with the highest
    possible user privilege, which is generally, the superuser
    privilege.  The design purpose is to allow the external program
    to do some special bootstrap operations before executing the
    student submissions, such as downgrading to a low-privileged user.

.. note::
    Some programming languages are designed to downgrade the user privilege
    of external program once launched, such as the Python language.
    You may head over to :ref:`hwpython` for more details.

Once the user code is finished, the runner should give out the score.
The score should be sent back to Railgun via website API.  The payload
should be encrypted by AES, with the key loaded from
``[RAILGUN_ROOT]/keys/commKey.txt``.  The key file is set to mode
``0700``, so if the runner downgrades the privilege before executing
user code, this file will not be accessible again.

Parameters such as the base url of website API is given to external
program via environmental variables.  Different programming languages
may set different variables, but the following ones should be set
regardless of the language:

.. tabularcolumns:: |p{6cm}|p{9cm}|

======================= =======================================================
Variable Name           Description
======================= =======================================================
RAILGUN_USER_ID         The recommended user id for the program to downgrade
                        privileges to.  May be ``0`` if not provided.
                        
                        If the program failed to `setuid` via syscall, the
                        process should exit with failure at once.

RAILGUN_GROUP_ID        The recommended group id for the program to downgrade
                        privileges to.  May be ``0`` if not provided.
                        
                        If the program failed to `setgid` via syscall, the
                        process should exit with failure at once.

                        Remember to call `setgid` before `setuid`, otherwise
                        you'll always fail on `setgid`.

RAILGUN_ROOT            The root directory of Railgun source.
RAILGUN_API_BASEURL     The API address of Railgun website.
RAILGUN_HANDID          The uuid of this running submission.
RAILGUN_HWID            The uuid of the homework this submission belongs to.
======================= =======================================================

.. _hwpython:

Python Judging
--------------

This section provides all the information about how to construct the
judging code for Python programming language.  Bear in mind that the
basic skeleton of Railgun judger is to run an external program.  If
you want to construct a piece of homework aimed for Python language,
you should at least compose the main Python script.

.. note::

    ``reportCompile`` and ``reportRuntime`` are **NOT** recommended to
    be enabled for Python programming language.

code.xml
~~~~~~~~

Structure of ``code.xml`` for Python programming language does not
apart largely from the above documentation.  The only thing to
mention is the two nodes ``<compiler>`` and ``<runner>``.
Suppose we have the following definitions:

.. code-block:: xml

    <compiler version="2.7" />
    <runner entry="run.py" timeout="3" />

The above settings indicate that the version of Python interpreter
is *2.7*, the main script to execute is *run.py*, while the maximum
run time is *3* seconds.  The two attributes ``version`` and ``entry``
are essential, but ``timeout`` is not.  If ``timeout`` is not given,
``RUNNER_DEFAULT_TIMEOUT`` in ``config.py`` will be selected.

The main script may not be ``run.py``, but must match the value
provided in ``code.xml``.  It is not restricted, but recommended,
since ``run.py`` is not so bad a name.

SafeRunner
~~~~~~~~~~

As is mentioned above, the skeleton of a judge runner is to evaluate
the user code, give a score, and send back to Railgun website API.
The API is validated by AES encryption channel, so it should be
rather reliable.

However, as a scripting language, almost anything in the interpreter
could be accessed by the code it executes.  To ensure that the user
code cannot inject the judger, Railgun provides its own Python
interpreter called `SafeRunner`.

The source of SafeRunner is stored in ``runlib/python/pyhost/CSafeRunner``.
You should build the SafeRunner, and place the executable file at the
root directory of Railgun.

The SafeRunner does two things: it load the communication key from
``commKey.txt`` and downgrade the user privilege before initializing
the Python interpreter, and it provides a module named `SafeRunner`
for the juding code.  There's only one method in `SafeRunner`,
``SafeRunner.run``, which could only be called once, so as to
prevent the user code injection.

The score will be sent back to Railgun in SafeRunner.  In such case,
the comminucation key will never appear in the Python interpreter.
The only thing you need to do is to create certain scorers, set the
score weight of each scorer, and pass them to ``SafeRunner.run``,
for example::

    from pyhost.scorer import CodeStyleScorer, XXXScorer
    import SafeRunner

    if (__name__ == '__main__'):
        scorers = [
            (CodeStyleScorer.FromHandinDir(ignore_files=['func.py']), 0.1),
            (XXXScorer('func.py'), 0.9),
        ]
        SafeRunner.run(scorers)

The above example includes the common ``CodeStyleScorer``, which
evaluates the code style and gives its score.  Another scorer in
the example is ``XXXScorer``, which may be ``UnitTestScorer``,
``CoverageScorer`` or ``InputClassScorer``, depending on the
requirement of your homework.

.. note::

    You shouldn't import any user submitted code in the module scope!
    Otherwise the user may import SafeRunner and call SafeRunner.run
    before your judging code!  For example::

        import sys
        import SafeRunner


        class Scorer(object):
            def __init__(self):
                self.name = 'Injected Scorer'
                self.time = 0
                self.score = 100
                self.brief = 'This score is injected!'
                self.detail = []

            def run(self):
                pass

        SafeRunner.run([(Scorer(), 1.0)])
        sys.exit(0)

    Once this module is imported, the SafeRunner will report a full
    score, and then exit the process gracefully.
    There are some special tricks when importing user modules,
    see :ref:`hwpython-unittest` for more details.

CodeStyleScorer
~~~~~~~~~~~~~~~

The most convenient way to construct a ``CodeStyleScorer`` is
``CodeStyleScorer.FromHandinDir(ignore_files)``.  It will scan all
Python source files in runtime directory except the ones in
``ignore_files``.

.. _`hwpython-unittest`:

UnitTestScorer
~~~~~~~~~~~~~~

The basic functionality of ``UnitTestScorer`` is to run a set of
unit test cases, and then give the score according to the percentage
of passed cases.

You may use this scorer under such situations: you have written
a set of test cases, and you'd like the students to write code that
passes your cases.  This could also judge the ``NetAPI`` homework,
which requires the students to deploy a web application, in that
you may write the unit tests to check whether the web application
runs properly.  Head over to :ref:`hwnetapi` to learn more about
this situation.

To construct a ``UnitTestScorer``, you may use
``UnitTestScorer.FromTestCase(testcase)``.  The basic example to
use ``UnitTestScorer`` can be found in ``reform_path`` from
`Railgun Source Code`_::

    import unittest
    from pyhost.scorer import UnitTestScorer, CodeStyleScorer
    import SafeRunner


    class ReformPathTestCase(unittest.TestCase):

        def _reform_path(self, s):
            # NOTE: any modules upload by student should only be loaded until the
            #       test is actually called. This is because the test runner will
            #       guarded by C module instead of Python, so that the result
            #       reporter will be prevent from injection.
            from path import reform_path
            return reform_path(s)

        def test_translateWinPathSep(self):
            self.assertEqual(self._reform_path('1\\2'), '1/2')
            self.assertEqual(self._reform_path('\\1\\2'), '/1/2')
            self.assertEqual(self._reform_path('\\\\1\\\\2'), '/1/2')

    if (__name__ == '__main__'):
        scorers = [
            (CodeStyleScorer.FromHandinDir(ignore_files=['run.py']), 0.1),
            (UnitTestScorer.FromTestCase(ReformPathTestCase), 0.9),
        ]
        SafeRunner.run(scorers)

Since the test cases are written by you, it's safe to load the test case
classes in the scope of ``run.py``.  You may import test case class,
or just define the test cases in ``run.py``, and pass it to
``UnitTestScorer.FromTestCase(testcase)`` to construct a ``UnitTestScorer``.
For advanced constructors, you can check the :ref:`api`.

.. note::

    You shouldn't import any user submitted module out of the
    methods in a test case.  If you carefully import all the user module only
    in test case methods, the Python interpreter will guarantee that all the
    user code is executed until ``SafeRunner`` has been started.

CoverageScorer
~~~~~~~~~~~~~~

``CoverageScorer`` is designed to evaluate white-box testing homework.
It runs the test cases submitted by the students, and give the score
according to the coverage rate on existing code.  Suppose you have
such method ``myfunc`` defined in ``myfunc.py``::

    def myfunc(a, b, c):
        if a > b:
            if b > c:
                return c
            else:
                return b
        elif a > c:
            if c > b:
                return b
            else:
                return c
        else:
            return a

This file should be protected by ``lock`` rule mentioned in :ref:`hwpack`,
so that it can be packed into the archive file, but not overwritten by
the submissions.

The mission of the students is to write unit test cases to cover as many
statements of ``myfunc`` as possible.  The judging code may be::

    from pyhost.scorer import CodeStyleScorer, CoverageScorer
    import SafeRunner

    if (__name__ == '__main__'):
        scorers = [
            (CodeStyleScorer.FromHandinDir(['run.py']), 0.1),
            (CoverageScorer.FromHandinDir(['myfunc.py']), 0.9),
        ]
        SafeRunner.run(scorers)

Suppose the test cases are placed in ``test_*.py``.  This is required
by ``CoverageScorer``, which you should tell to the students in homework
description.  The above example will run all test cases in ``test_*.py``,
and check the coverage on ``myfunc.py``.

.. _hwnetapi:

NetAPI Judging
--------------

You may assign such homework to the students: they are told to deploy
a web application on a public accessible server, submit the url to
you, and then you would check the functionality of that web application
by unit tests.  ``netapi`` programming language is just what you need.

The main structure of ``netapi`` programming language is just like
that of ``python``, except a few changes to ``code.xml``:

.. code-block:: xml

    <?xml version="1.0"?>
    <code>
      <attachment>true</attachment>
      <compiler version="2.7" url="^http://localhost.*" ip="127\.0\.0\.1" />
      <runner entry="run.py" timeout="10" />
      <reportCompile>true</reportCompile>
      <reportRuntime>true</reportRuntime>
      <files>
        <hide>^run\.py$</hide>
      </files>
    </code>

There are two more attributes to the ``compiler`` node: ``url``
and ``ip``.  They should be both regular expressions, where ``url``
validates the whole address of web application submitted by the
students, and ``ip`` validates the ip address of the domain.

Three environmental variables are provided in additional to the
ones described in :ref:`hwjudge`:

.. tabularcolumns:: |p{6cm}|p{9cm}|

======================= ====================================================
Variable Name           Description
======================= ====================================================
RAILGUN_REMOTE_ADDR     The web application address submitted by student.
RAILGUN_URLRULE         The url pattern defined in ``code.xml``.
RAILGUN_IPRULE          The ip pattern defined in ``code.xml``.
======================= ====================================================

The judging code of ``netapi`` programming language is just like
``python``, in that you may compose a unit test and run it with
``UnitTestScorer``.  To send requests and receive responses from
the remote web application, you may use the builtin library
``urllib``, or you may also use `requests`_ library, which is
one of requirements of Railgun.

.. _requests: http://www.python-requests.org

The complete example of NetAPI provided by `Railgun Source Code`_ is::

    import os
    import json
    import requests
    import unittest

    from pyhost.scorer import UnitTestScorer
    import SafeRunner


    class ArithApiUnitTest(unittest.TestCase):

        def __init__(self, *args, **kwargs):
            super(ArithApiUnitTest, self).__init__(*args, **kwargs)
            self.base_url = os.environ['RAILGUN_REMOTE_ADDR'].rstrip('/')

        def _post(self, action, payload):
            """Do post and get remote api result."""

            payload = json.dumps(payload)
            # Get remote response
            try:
                ret = requests.post(self.base_url + action, data=payload,
                                    headers={'Content-Type': 'application/json'})
            except Exception:
                raise RuntimeError("Cannot get response from remote API.")

            # Check response status
            if (ret.status_code != 200):
                raise RuntimeError("HTTP status %d != 200." % ret.status_code)
            ret = ret.text

            # Convert response to object
            try:
                return json.loads(ret)
            except Exception:
                raise ValueError(
                    "Response '%(msg)s' is not json." % {'msg': ret})

        def _get_result(self, action, payload):
            """Ensure the remote api does not return error, and get 'value' from
            remote api result."""

            ret = self._post(action, payload)
            if (ret['error'] != 0):
                raise RuntimeError("Remote API error: %s." % ret['message'])
            return ret['result']

        def test_add(self):
            self.assertEqual(self._get_result('/add/', {'a': 1, 'b': 2}), 3)

        def test_pow(self):
            self.assertEqual(self._get_result('/pow/', {'a': 2, 'b': 100}), 2**100)

        def test_gcd(self):
            self.assertEqual(self._get_result('/gcd/', {'a': 2, 'b': 4}), 2)

    if (__name__ == '__main__'):
        scorers = [
            (UnitTestScorer.FromTestCase(ArithApiUnitTest), 1.0),
        ]
        SafeRunner.run(scorers)

You may edit the three test cases ``test_add``, ``test_pow`` and ``test_gcd``
to fit your needs.

.. note::

    ``reportCompile`` and ``reportRuntime`` are recommended to
    be enabled for NetAPI programming language.

.. _hwinput:

Input Judging
-------------

The ``input`` programming language is designed for black-box testing
homework.  The students are required to generate a serial of data
to test a certain *unknown* program.  The functionality of such
program should be written in the description, so that the students
can create as many classes of input data as possible to cover the
described program.

The structure of ``input`` programming language is just like
that of ``python``.  However, since the judger of ``input`` language
will put the CSV data submitted by the students into ``data.csv``,
you must add the following file rule into ``code.xml``:

.. code-block:: xml

    <lock>^data\.csv$</lock>

A full example of ``code.xml`` is:

.. code-block:: xml

    <?xml version="1.0"?>
    <code>
      <attachment>false</attachment>
      <compiler version="2.7" />
      <runner entry="run.py" timeout="3" />
      <files>
        <hide>^run\.py$</hide>
        <lock>^data\.csv$</lock>
      </files>
    </code>

.. note::

    ``input`` programming language may not provide the archive file,
    so we can set ``attachment`` option to `false`.

The judging code for ``input`` language is a bit more complex
than the above languages.  First, you should create a ``CsvSchema``,
to parse user submitted csv data::

    from railgun.common.csvdata import CsvSchema, CsvFloat

    class ExampleSchema(CsvSchema):
        a = CsvFloat()
        b = CsvFloat()
        c = CsvFloat()

This schema will accept csv data in the following format::

    a,b,c
    1,2,3
    1,3,3

The header line is essential in the submitted csv data, which you
should tell to the students in homework descriptions.  The order
of the columns is not restricted, but each column in the schema
must also appear in the data.

Besides ``CsvFloat``, there are 3 more types in ``csvdata.py``:

.. tabularcolumns:: |p{5cm}|p{10cm}|

======================= ====================================================
Data Type               Description
======================= ====================================================
CsvFloat                Expect an integral or floating number.
CsvInteger              Expect an integral number.
CsvBoolean              Expect ``true`` or ``false``.
CsvString               Expect a csv quoted string.
======================= ====================================================

After you have created the data schema, you should call
``InputClassScorer(schema, fileobj)`` to construct the scorer as
following::

    from pyhost.scorer import InputClassScorer

    scorer = InputClassScorer(ExampleSchema, open('data.csv', 'rb'))

Next, you should define the input classes.  The syntax to define
the classes is handy, and you may even provide descriptions
for each input class::

    @scorer.rule('all zeros input')
    def all_zeros(obj):
        return (obj.a == 0 and obj.b == 0 and obj.c == 0)

Above example creates the "all-zeros" input class in the ``scorer``,
whose test condition is ``a == 0 and b == 0 and c == 0``.  You may
notice that all fields from ``data.csv`` are stored as attributes
of ``obj``.  The description of such input class is provided
by ``@scorer.rule(description)`` decoration.

After you have defined all input classes, you can then run the
scorer by following code::

    import SafeRunner

    SafeRunner.run([
        (scorer, 1.0)
    ])

.. note::

    ``reportCompile`` and ``reportRuntime`` are recommended to
    be enabled for Input programming language.

.. _hwnotes:

Additional Notes
----------------

*   Whatever programming language, you must use UTF-8 to write your code.
    Tell the students to follow this rule as well!  All the output of the
    program must be also valid UTF-8 sequence!

    To ensure the Python interpreter to use UTF-8 encoding, add the
    following line at the beginning of Python source files::

        # -*- coding: utf-8 -*-

*   You may need some system configurations to restrict the user code
    from accessing the internet (through which your judging code may
    be revealed).  See :ref:`practice-offline` for more details.
