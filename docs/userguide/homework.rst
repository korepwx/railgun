.. _homework:

Homework
========

The `Railgun Source Code`_ contains some example homework in /hw directory.
To start drafting your own homework, you may copy the files from the example
which close to your needs mostly.

This page intends to give you some more details about the homework.

.. _Railgun Source Code: https://github.com/korepwx/railgun

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

To provide nice and clear descriptions for homework, you may need the
knowledge of `Markdown <http://www.example.org>`_ language.  Railgun
uses an extended flavour of Markdown similar to the one github uses.
You may head over to :ref:`hwdesc` to learn more.

Students can download attachments from the homework information pages.
You don't need to pack up these attachments by hand, in that Railgun will
do it for you.  It will pack all files for particular programming language
in ``code`` directory along with the resource files at the root of homework
into zip archive files.  Students can thus choose their preferred programming
language and download the archive files to start their work.
You may head over to :ref:`hwpack` to learn more.

After the students hand in their submissions, Railgun will judge their
work.  As an online judger for Software Enginneering, Railgun uses a very
handy method to obtain the greatest compatibility for different programming
languages: it runs each submission as an external process, while the scoring
is done in that process rather than Railgun.  The score is then sent back
to Railgun through Json API in AES encrypted channel.  Because of this,
you must provide runnable entries for each programming language of homework.
You may head over to :ref:`hwjudge` to learn more.
of Railgun.

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

Here's a basic example provided by `Railgun Source Code`_:

.. code-block:: xml

    <?xml version="1.0"?>
    <homework>
      <uuid>b388ad5b25ee44bbac9be46c43851768</uuid>
      <names>
        <name lang="zh-cn">格式化路径</name>
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

.. _hwdesc:

Draft Description
-----------------

.. _hwpack:

Archive Packing
---------------


.. _hwjudge:

Online Judging
--------------

