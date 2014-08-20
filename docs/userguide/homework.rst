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
    ├── code
    │   └── python
    │       ├── code.xml
    │       ├── path.py
    │       └── run.py
    ├── desc
    │   ├── en.md
    │   ├── img
    │   │   └── python-logo.png
    │   └── zh-cn.md
    └── hw.xml

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
and :ref:`hwinput`.

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
      <reportAll>true</reportAll>
      <files />
    </homework>

All nodes in ``hw.xml`` showed above are essential.  Both the website of
Railgun and the background runner will refuse to start up if it lacks
anything.  The functionality of the nodes are described in following table:

.. tabularcolumns:: |p{4cm}|p{11cm}|

=============== ============================================================
Node Name       Description
=============== ============================================================
``uuid``        Unique id of this piece of homework.  Although the
                website uses directory name in the url, it relies on
                ``uuid`` to associate submissions with certain
                homework.  If and only if ``uuid`` matches, two
                pieces of homework will be treated as one.
                You may change the ``uuid`` in ``hw.xml``, so as to
                clear all submissions in the database.

                You may execute
                ``python -c 'import uuid; print uuid.uuid4().get_hex()'``
                to generate a new randomized ``uuid``.
``name``        Define the name of this piece of homework in a
                certain locale.  The website will try to choose
                a best matching name according to the locale of user.
                If no name can match the user, then the name for the
                default locale (specified in ``config.py``) will be
                selected.  If still no name can match, the last name
                will be choosed.
``due``         Define a deadline of this piece of homework.  There
                may be two or three sub nodes in a ``due`` node:

                *   ``date``: The due date of this deadline.
                *   ``scale``: The score scale of this deadline.
                    The final score of submissions will be scaled
                    by this factor before the deadline.
                *   ``timezone``: Optional node to point out the
                    timezone of ``date`` node.  If not given, the
                    default timezone in ``config.py`` will be used.
``reportAll``   Whether the website should display all details about
                the submission?  When set to true, the process standard
                output and error output, as well as detailed runtime
                log will be sent to students.  Enable this may cause
                the homework judging code to be revealed in some
                programming languages.  You may head over to
                :ref:`hwpython`, :ref:`hwnetapi` and :ref:`hwinput`
                to see whether this parameter should be set to true
                or false.
``files``       Archive packing rules for the files in root directory.
                Head over to :ref:`hwpack` for more details.
=============== ============================================================

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
      <files>
        <hide>^run\.py$</hide>
        <accept>^path\.py$</accept>
        <accept>.*\.py$</accept>
      </files>
    </code>

Like ``hw.xml``, all nodes in ``code.xml`` are essential.  The system
will refuse to start up if it lacks anything. The functionality of the
nodes are described in following table:

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
files           Archive packing rules for the files in this language
                directory.
                Head over to :ref:`hwpack` for more details.
=============== =======================================================

.. _hwdesc:

Writing Description
-------------------

.. _hwpack:

Archive Packing
---------------

.. _hwjudge:

Online Judging
--------------

.. _hwpython:

Python Judgement
----------------

.. _hwnetapi:

NetAPI Judgement
----------------

.. _hwinput:

Input Data Judgement
--------------------

