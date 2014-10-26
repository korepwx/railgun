#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/common/hw.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

"""Homework assignments in Railgun are defined by xml files.  All the
definition xml files along with the resources should be placed in a
single directory.  You may refer to :ref:`homework` for more details
about how to define a homework assignment.

When the Railgun system is booted, it will scan all the directories
under ``config.HOMEWORK_DIR`` to load the assignments.  Each homework
assignment is stored in a :class:`Homework`.  Also, the loaded
:class:`Homework` instances are gathered in a global :class:`HwSet`
instance.

All the classes to represent the homework assignments are defined
in this module.  The relationships between these classes are:

    .. uml::

        HwSet o-- Homework : aggregation
        Homework "1" *-- "many" HwInfo : contains
        Homework "1" *-- "1" FileRules : contains
        Homework "1" *-- "many" HwCode : contains
        HwCode "1" *-- "1" FileRules : contains
        HwCode "1" *-- "many" HwScorerSettings: contains

In addition, the JSON objects carrying the scores for a submission used
in the communication between the runner host and the website are also
defined in this module.  The relationships between these classes are:

    .. uml::

        HwScore "1" *-- "many" HwPartialScore : contains

You may head over to read more about these classes.
"""

import re
import os
from datetime import datetime
from xml.etree import ElementTree
from itertools import ifilter, chain

from markdown import markdown
from babel.dates import timedelta, get_timezone

import config
from . import fileutil
from .fileutil import file_get_contents
from .dateutil import utc_now, to_utc_date, from_plain_date
from .lazy_i18n import lazystr_to_plain, plain_to_lazystr
from .url import reform_path, UrlMatcher


def parse_bool(s):
    """Convert a string literal into its boolean value.

    :param s: The string literal that represents a boolean value.
    :type s: :class:`str`
    :return: :data:`True` if s.lower() is one of (true, on, 1, yes),
        :data:`False` otherwise.
    """
    if not s:
        return False
    s = str(s).lower()
    return (s == 'true' or s == 'on' or s == '1' or s == 'yes')


class FileRules(object):
    """Manage a set of file rules.

    A file rule is a 2-element tuple (pattern, action), where :token:`pattern`
    determines what files to be ruled, and :token:`action` determines what
    operations these files will take.

    :token:`pattern` is a regular expression.  It should contain patterns
    to the relative paths of files.

    :token:`action` may be one of the following operations: `ACCEPT`,
    `LOCK`, `HIDE` and `DENY`.

    Since the file rules are mainly used to determine what files in a homework
    pack can be revealed to students, and what files submitted from the
    students can be received.

    You may refer to :ref:`hwpack` for more details about these four actions.
    """

    #: Indicate that the matching files are revealed to students in the
    #: homework attachment, and students can overwrite these files in
    #: their submissions.
    ACCEPT = 0

    #: Indicate that the matching files are revealed to students in the
    #: homework attachment, but the students cannot overwrite these files
    #: in their submissions.
    LOCK = 1

    #: Indicate that the matching files are `NOT` revealed to students,
    #: `NOR` should they been overwritten.
    HIDE = 2

    #: Indicate that the matching files are denied, and the submission
    #: containing these files will be `REJECTED` immediately.
    DENY = 3

    def __init__(self):
        # list of (action, pattern)
        self.data = []

    def __repr__(self):
        return repr(self.data)

    def get_action(self, filename, default_action=LOCK):
        """Get the action to take on given file.

        :param filename: The name of the file.
        :type filename: :class:`str`
        :param default_action: If no rule in this set is matched, what action
            should this file take?

        :return: One action out of ``(ACCEPT, LOCK, HIDE, DENY)``.
        """

        for a, p in self.data:
            if p.match(filename):
                return a

        # if no rule matches, default takes lock action
        return default_action

    def _make_action(self, action, pattern):
        act = None
        if action.isalpha():
            act = getattr(FileRules, action.upper(), None)
        if act is None:
            raise ValueError('Unknown action "%s" in file rule.' % action)
        pat = re.compile(pattern)
        return (act, pat)

    def append_action(self, action, pattern):
        """Append a file rule (action, pattern) to the end of rule list.

        The rules are matched in list order.  If a given file is matched
        by some rule in the list, all the remaining rules after it will
        not be checked any longer.

        :param action: The action of the rule.
        :type action: One action out of ``(ACCEPT, LOCK, HIDE, DENY)``
        :param pattern: The file name pattern of the rule.
        :type pattern: Regular expression :class:`str`
        """
        self.data.append(self._make_action(action, pattern))

    def prepend_action(self, action, pattern):
        """Prepend a file rule (action, pattern) to the front of rule list.

        :param action: The action of the rule.
        :type action: One action out of ``(ACCEPT, LOCK, HIDE, DENY)``
        :param pattern: The file name pattern of the rule.
        :type pattern: Regular expression :class:`str`
        """
        self.data.insert(0, self._make_action(action, pattern))

    def filter(self, files, allow_actions, default_action=LOCK):
        """Return a new iterator on given file iterator, where files not
        taking operations from `allowed_actions` should be removed.

        Because this method return the new file name iterator, not a new list,
        you must store the list somewhere if you want to use the result for
        more than one times, for example::

            rules = FileRules()
            accepted_files = rules.filter(
                dirtree('.'),
                (FileRules.ACCEPT, FileRules.LOCK),
            )

        :param files: The input file name iterator.
        :type files: Iterable file names
        :param allow_actions: Set of file rules ``(ACCEPT, LOCK, HIDE, DENY)``.
        :type allow_actions: :class:`set` or :class:`tuple`
        :param default_action: If no rule in rule list is matched, what action
            should a given file take?

        :return: The new file name iterator.
        """

        return ifilter(
            lambda f: self.get_action(f) in allow_actions,
            files
        )

    @staticmethod
    def parse_xml(xmlnode):
        """Load file rules from an xml node object.

        This method does not care about the tag name of the given node.
        It only parses the children of given node.  Here's an example of
        a file rule node:

        .. code-block:: xml

            <rules>
                <accept>.*\\.py$</accept>
                <lock>.*\\.conf$</lock>
                <hide>.*\\.pyc$</hide>
                <deny>.*\\.exe$</deny>
            <rules>

        :param xmlnode: The xml node object that contains file rules.
        :type xmlnode: :class:`xml.etree.ElementTree.Element`
        """

        ret = FileRules()

        # there should be at least one rule in file_rules: code.xml is
        ret.append_action('hide', '^code\\.xml$')

        if xmlnode is not None:
            for nd in xmlnode:
                ret.append_action(nd.tag, nd.text.strip())
        return ret


class HwInfo(object):
    """Object to store the homework info (name, description & solution).

    The description and the solution should be written in Markdown syntax.
    There are some extensions to the original Markdown standard.  Refer to
    :ref:`hwdesc` for more details.

    :param lang: The language for name, description and solution.
    :type lang: :class:`str`
    :param name: The homework name.
    :type name: :class:`str`
    :param desc: The homework description (Markdown source code).
    :type desc: :class:`str`
    :param solve: The homework solution (Markdown source code).
    :type solve: :class:`str`
    """

    def __init__(self, lang, name, desc, solve):
        #: The language name of this info object,
        #: should be compatible with request.accept_languages.
        self.lang = lang
        #: The name of the homework.
        self.name = name
        #: The description of the homework (Markdown source code).
        self.desc = desc
        #: The solution of this homework (Markdown source code).
        self.solve = solve
        #: The formatted description of this homework.
        #: :class:`Homework` will call `format_markdown` to set this
        #: field, so you may use it for free.
        self.formatted_desc = None
        #: The formatted solution of this homework.
        #: :class:`Homework` will call `format_markdown` to set this
        #: field, so you may use it for free.
        self.formatted_solve = None

    def format_markdown(self, hwslug):
        """Generate html description and solution from Markdown source code.

        After this method is called, `formatted_desc` and `formatted_solve`
        will be set.

        :param hwslug: The slug of owner homework.  Necessary when formatting
            markdown sources.
        :type hwslug: :class:`str`
        """
        # To expose static resources in homework desc directory, we need to
        # convert all "hw://<path>" urls to hwstatic view urls.
        def translate_url(u):
            # Get rid of 'hw://' and leading '/'
            u = reform_path(u[5:])
            if u.startswith('/'):
                u = u[1:]
            # translate to hwstatic file
            filename = '%s/%s' % (hwslug, u)
            # NOTE: here I hardcoded the url for hwstatic!
            ret = '/hwstatic/%s' % filename
            # we also need to prepend website base url
            return config.WEBSITE_BASEURL + ret

        def format(text):
            return markdown(
                text=text,
                output_format='xhtml1',
                extensions=[
                    'extra',
                    'tables',
                    'smart_strong',
                    'codehilite',
                    'nl2br',
                    'toc',
                    'fenced_code',
                ]
            )

        # the description
        desc = UrlMatcher(['hw']).replace(self.desc, translate_url)
        self.formatted_desc = format(desc)

        # the solution
        if self.solve:
            solve = UrlMatcher(['hw']).replace(self.solve, translate_url)
            self.formatted_solve = format(solve)

    def __repr__(self):
        __s = lambda s: s.encode('utf-8') if isinstance(s, unicode) else s
        return '<HwInfo(lang=%s,name=%s)>' % (self.lang, __s(self.name))


class HwScorerSetting(object):
    """Store the settings for a particular scorer in ``code.xml``.

    This class is a component in :class:`HwCode`.  Different programming
    languages may carry different scorers, and may reveal different
    level of program output to the students.

    :param detail: Whether this scorer should show detail reports?
    """

    def __init__(self, detail=None):
        #: Whether or not to display the detail of this scorer?
        #: If None, Railgun will use `HwCode.reportRuntime` as value.
        self.detail = detail

    @staticmethod
    def parse_xml(xmlnode):
        """Get scorer settings from given xml node object.

        An xml node to configure a particular scorer may be like this:

        .. code-block:: xml

            <scorer name="CodeStyleScorer" detail="true" />

        :param xmlnode: Xml node object holding the settings.
        :type xmlnode: :class:`xml.etree.ElementTree.Element`
        """

        ret = HwScorerSetting()
        if xmlnode.get('detail'):
            ret.detail = parse_bool(xmlnode.get('detail'))
        return ret


class HwCode(object):
    """Store the definition of a particular programming language in a
    homework assignment.

    The Railgun system is designed to allow the students to choose their
    preferred programming language the finish their homework.  Because of
    these, each homework should contain seperated code files for each
    individual language.

    :class:`HwCode` is the class to store language definitions and settings.
    The settings may include compiler parameters, runner parameters and
    verbosity of output messages.

    All the configurations are loaded from ``code.xml``.  Refer to
    :ref:`hwstruct` to see how ``code.xml`` is organized.

    :param path: The root path of the code package.
    :type path: :class:`str`
    :param lang: The name of programming language.
    :type lang: :class:`str`
    """

    def __init__(self, path, lang):
        #: The root path of code package, should be ``[hw.path]/code/[lang]``.
        self.path = path
        #: The programming language of this code package.
        self.lang = lang

        #: Whether or not students can download an attachment for this
        #: programming language?
        self.has_attach = True

        #: An xml node object that stores the compiler parameters.
        #: Let the runner host to parse the parameters.
        self.compiler_params = None

        #: An xml node object that stores the runner parameters.
        #: Let the runner host to parse the parameters.
        self.runner_params = None

        #: The file match rules of this code package.
        self.file_rules = None

        #: Whether the compiler messages should be revealed to students?
        #: Default value is :data:`True`.
        self.reportCompile = True

        #: Whether the runtime messages should be revealed to students?
        #: Default value is :data:`False`.
        self.reportRuntime = False

        #: A dict ("Scorer's Type Name" -> :class:`HwScorerSetting`).
        #: Store the specialized settings for various scorers.
        self.scorers = {}

    def __repr__(self):
        return '<HwCode(%s)>' % self.path

    def get_scorer(self, typeName):
        """Get the settings of a particular scorer.

        :param typeName: The scorer type name.  It may be the full name of
            the scorer, or a partial name that matches the last part of
            the type name.  For example, if we call `get_scorer` with:

            *   common.scorers.BaseScorer
            *   BaseScorer

            We will both get the `common.scorers.BaseScorer`.

        :type typeName: :class:`str`

        :return: The scorer setting object if found, or :data:`None` otherwise.
        :rtype: :class:`HwScorerSetting` or :data:`None`
        """

        if typeName in self.scorers:
            return self.scorers[typeName]
        # Truncate full type name
        rpos = typeName.rfind('.')
        if rpos >= 0:
            typeName = typeName[rpos+1:]
            return self.scorers.get(typeName, None)

    @staticmethod
    def load(path):
        """Load the definitions as a code package under `path`.

        This method will create a :class:`HwCode` object that loads settings
        from ``[path]/code.xml``, of which the programming language will be
        set to ``os.path.split(path)[1]``.

        :param path: The root directory of the code package.
        :type path: :class:`str`

        :return: A :class:`HwCode` object.
        """

        lang = os.path.split(path)[1]
        ret = HwCode(path, lang)
        tree = ElementTree.parse(os.path.join(path, 'code.xml'))
        root = tree.getroot()

        # whether or not this HwCode provides download attachment
        # default value is True if not given
        has_attach_node = root.find('attachment')
        ret.has_attach = ((has_attach_node is None) or
                          parse_bool(has_attach_node.text))

        # store compiler & runner param nodes
        ret.compiler_params = root.find('compiler')
        ret.runner_params = root.find('runner')

        # get display settings
        ret.reportCompile = parse_bool(root.find('reportCompile').text)
        ret.reportRuntime = parse_bool(root.find('reportRuntime').text)

        # parse the file match rules
        ret.file_rules = FileRules.parse_xml(root.find('files'))

        # set default hidden rules
        ret.file_rules.prepend_action('hide', '^code\\.xml$')
        for r in config.DEFAULT_HIDE_RULES:
            ret.file_rules.prepend_action('hide', r)

        # Iterate through scorer settings
        scorer_node = root.find('scorers')
        if scorer_node is not None:
            for scorer in scorer_node:
                name = scorer.get('name')
                if not name:
                    continue
                ret.scorers[name] = HwScorerSetting.parse_xml(scorer)

        return ret


class Homework(object):
    """Store the definition of a homework assignment.

    The constructor of this class will only create an empty :class:`Homework`
    object.  You may use `Homework.load(path)` to construct the instance
    according to external homework definition files.
    """

    def __init__(self):
        #: The url slug of this homework assignment.
        self.slug = None
        #: The root directory of this homework assignment.
        self.path = None
        #: Unique id of this homework.  The submissions and final scores
        #: are associated with homework according to `uuid`.
        self.uuid = None
        #: :class:`HwInfo` objects for different speaking languages.
        self.info = []
        #: List of (deadline datetime, scale factor).
        self.deadlines = []
        #: The file matching rules that affects all programming languages.
        self.file_rules = None
        #: :class:`HwCode` objects for different programming languages.
        self.codes = []
        #: Cache the mapping from locale name to :class:`HwInfo` object.
        self._locale_to_info = {}
        #: Cache the mapping from language name to :class:`HwCode` object.
        self._lang_to_code = {}

    @staticmethod
    def load(path):
        """Load the definitions of homework under `path`.

        This method will load the settings from ``[path]/hw.xml``, and create
        all :class:`HwInfo` and :class:`HwCode` objects according to the
        sub-directories.

        Also, the descriptions and solutions in every locale will be formatted
        from Markdown source code to html display text.  You may get the html
        from the `formatted_desc` and `formatted_solve` attribute of
        :class:`HwInfo`.

        :param path: The root directory of homework.
        :type path: :class:`str`

        :return: A :class:`Homework` object.
        :raises: :class:`ValueError` if the homework definition is wrong.
        """

        # Stage 1: load the homework meta data from hw.xml
        ret = Homework()
        ret.path = path
        ret.slug = os.path.split(path)[1]
        tree = ElementTree.parse(os.path.join(path, 'hw.xml'))

        for nd in tree.getroot():
            if nd.tag == 'uuid':
                ret.uuid = nd.text.strip()
            elif nd.tag == 'names':
                for name in nd.iter('name'):
                    lang = name.get('lang')
                    name = name.text.strip()
                    # To define the desc of homework information, [lang].md
                    # should be created under desc directory.
                    desc = file_get_contents(
                        os.path.join(path, 'desc/%s.md' % lang)
                    )
                    # solution may be empty
                    solve_file = os.path.join(path, 'solve/%s.md' % lang)
                    solve = None
                    if os.path.isfile(solve_file):
                        solve = file_get_contents(solve_file)
                    ret.info.append(HwInfo(lang, name, desc, solve))
            elif nd.tag == 'deadlines':
                for due in nd.iter('due'):
                    # get the timezone of due date
                    timezone = due.find('timezone')
                    timezone = timezone.text if timezone is not None else None
                    if not timezone:
                        timezone = config.DEFAULT_TIMEZONE
                    timezone = get_timezone(timezone.strip())
                    # parse the date string
                    duedate = from_plain_date(
                        datetime.strptime(due.find('date').text.strip(),
                                          '%Y-%m-%d %H:%M:%S'),
                        timezone
                    )
                    # parse the factor
                    scale = float(due.find('scale').text.strip())
                    # add to deadline list
                    ret.deadlines.append((to_utc_date(duedate), scale))
            elif nd.tag == 'files':
                ret.file_rules = FileRules.parse_xml(nd)

        # Stage 2: discover all programming languages
        code_path = os.path.join(path, 'code')
        for pl in os.listdir(code_path):
            pl_path = os.path.join(code_path, pl)
            pl_meta = os.path.join(pl_path, 'code.xml')
            # only the directories with contains 'code.xml' may be programming
            # language definition
            if not os.path.isfile(pl_meta):
                continue
            # load the programming language definition
            ret.codes.append(HwCode.load(pl_path))

        # Stage 3: check integrity
        if not ret.info:
            raise ValueError('Homework name is missing.')

        # Stage 4: set default hidden rules
        ret.file_rules.prepend_action('hide', '^hw\\.xml$')
        ret.file_rules.prepend_action('hide', '^code/\\.*')
        ret.file_rules.prepend_action('hide', '^code$')
        ret.file_rules.prepend_action('hide', '^desc/\\.*')
        ret.file_rules.prepend_action('hide', '^desc$')
        ret.file_rules.prepend_action('hide', '^solve/\\.*')
        ret.file_rules.prepend_action('hide', '^solve$')
        for r in config.DEFAULT_HIDE_RULES:
            ret.file_rules.prepend_action('hide', r)

        # Stage 5: Cache necessary objects
        ret._cache_formatted_markdown()
        ret._cache_mappings()

        return ret

    def _cache_mappings(self):
        """Cache mappings from key to value."""
        self._lang_to_code = {c.lang: c for c in self.codes}
        self._locale_to_info = {i.lang: i for i in self.info}

    def _cache_formatted_markdown(self):
        """Format the descriptions and solutions in all :class:`HwInfo`.

        In the performance profiler, formatting the homework description
        can take up to 100ms.  So I decide to pre-calculate and cache all
        formatted descriptions.
        """
        for i in self.info:
            i.format_markdown(self.slug)

    def get_name_locales(self):
        """Get the locale names of all :class:`HwInfo` objects.

        :return: :class:`list` of all locale names.
        """
        return [i.lang for i in self.info]

    def get_code_languages(self):
        """Get the programming language names of all :class:`HwCode` objects.

        :return: :class:`list` of all programming language names.
        """
        return sorted([c.lang for c in self.codes])

    def get_code(self, lang):
        """Get the :class:`HwCode` object whose programming language is `lang`.

        :return: The requested :class:`HwCode` object.
        :raises: :class:`KeyError` if given language is not found.
        """
        return self._lang_to_code[lang]

    def count_attach(self):
        """Count the number of :class:`HwCode` objects with attachment."""
        ret = 0
        for c in self.codes:
            if c.has_attach:
                ret += 1
        return ret

    def pack_assignment(self, lang, filename):
        """Pack the attachment for given programming language into `filename`.

        All the code and resource files will be packed into a new zip archive
        file.  This behaviour is controlled by :class:`FileRules` in the
        :class:`Homework` and the :class:`HwCode` objects.  You may refer
        to :ref:`hwpack` for more details.

        :param lang: The programming language name.
        :type lang: :class:`str`
        :param filename: The zip attachment file path.
        :type filename: :class:`str`
        """

        # select the code package
        code = self.get_code(lang)

        # prepare the file list in root directory.
        # only acceptable and locked files are given to students.
        #
        # note that `code` and `desc` directories are defaultly hidden.
        root_files = self.file_rules.filter(
            fileutil.dirtree(self.path),
            (FileRules.ACCEPT, FileRules.LOCK)
        )

        # prepare the file list for given `lang`.
        code_files = code.file_rules.filter(
            fileutil.dirtree(code.path),
            (FileRules.ACCEPT, FileRules.LOCK)
        )

        # make target file name
        with fileutil.makezip(filename) as zipf:
            path_prefix = self.slug + '/'
            fileutil.packzip(self.path, root_files, zipf, path_prefix)
            fileutil.packzip(code.path, code_files, zipf, path_prefix)

    def list_files(self, lang):
        """List all runtime files for given programming language.

        This method is typically called when you want to get the list of
        files that will be copied to runtime directory when executing
        a submission in the given programming language.

        .. note::
            Some files in the result of this method should not be revealed
            to students in a downloadable attachment!  Use with caution!

        :param lang: The programming language name.
        :type lang: :class:`str`

        :return: An iterable object of file names.
        """
        # select the code package
        code = self.get_code(lang)

        # get list of root files
        root_hide = \
            re.compile('^code$|^code/\\.*|^desc$|^desc/\\.*|^hw\\.xml$')
        root_files = ifilter(
            lambda s: not root_hide.match(s),
            fileutil.dirtree(self.path)
        )

        # get list of code files
        code_files = fileutil.dirtree(code.path)

        return chain(root_files, code_files)

    def get_next_deadline(self):
        """Get the next deadline of this homework.

        :return: A :class:`tuple` of (deadline datetime, score scale) if the
            next deadline exists, or :data:`None` if the homework has already
            expired.
        """

        now = utc_now()
        for ddl in self.deadlines:
            if ddl[0] >= now:
                return (ddl[0], ddl[1])

    def get_last_deadline(self):
        """Get the final deadline of this homework.

        :return: A :class:`tuple` of (deadline datetime, score scale) if the
            final deadline exists, or :data:`None` if the homework has already
            expired.
        """

        now = utc_now()
        ddl = self.deadlines[-1]
        if ddl[0] >= now:
            return (ddl[0], ddl[1])


class HwSet(object):
    """Collection of :class:`Homework` definition objects.

    Given the root directory of all homework definitions, :class:`HwSet`
    will discover and load all homework assignments under that directory.

    :param hwdir: The root directory of all homework definitions.
    :type hwdir: :class:`str`
    """

    def __init__(self, hwdir):

        #: The root directory of all homework definitions.
        self.hwdir = hwdir
        #: :class:`Homework` objects in the order of `slug`.
        self.items = None

        #: Cache the mapping from `uuid` to :class:`Homework`.
        self.__uuid_to_hw = {}

        #: Cache the mapping from `slug` to :class:`Homework`.
        self.__slug_to_hw = {}

        self.reload()

    def reload(self):
        """Reload the homeworks under root directory.

        You may manually call this method to reload the definitions.
        :class:`HwSet` will not monitor the file changes.
        """

        # load all homeworks
        self.items = []
        for fn in os.listdir(self.hwdir):
            fp = os.path.join(self.hwdir, fn)
            if (os.path.isdir(fp) and
                    os.path.isfile(os.path.join(fp, 'hw.xml'))):
                self.items.append(Homework.load(fp))
        self.items = sorted(self.items, cmp=lambda a, b: cmp(a.slug, b.slug))

        # hash all items
        self.__uuid_to_hw = {hw.uuid: hw for hw in self.items}
        self.__slug_to_hw = {hw.slug: hw for hw in self.items}

    def __iter__(self):
        """Iterate over :class:`Homework` objects."""
        return iter(self.items)

    def get_by_uuid(self, uuid):
        """Get the :class:`Homework` object with given `uuid`."""
        return self.__uuid_to_hw.get(uuid, None)

    def get_by_slug(self, slug):
        """Get the :class:`Homework` object with given `slug`."""
        return self.__slug_to_hw.get(slug, None)

    def get_uuid_list(self):
        """Get the list of `uuid` of all :class:`Homework` objects."""
        return [hw.uuid for hw in self.items]


class HwPartialScore(object):
    """A serializable partial score object.

    The final score of a submission is a combinition of all scorers.
    The scores from every scorer are multiplied with a given `weight`,
    and sumed up to form the final score.  A :class:`HwPartialScore` is
    the score of one scorer.

    You may refer to :ref:`json_HwPartialScore` for more details about
    the JSON format.

    :param scorer_name: The human readable name of this scorer.
    :type scorer_name: :class:`railgun.common.lazy_i18n.GetTextString`
    :param scorer_type_name: The type name of this scorer.
    :type scorer_type_name: :class:`str`
    :param score: The final score, range in [0, 100].
    :type score: :class:`float`
    :param weight: The weight of this scorer.
    :type weight: :class:`float`
    :param time: The running time of this scorer (in seconds).
    :type time: :class:`float`
    :param brief_report: The brief output message of this scorer.
    :type brief_report: :class:`railgun.common.lazy_i18n.GetTextString`
    :param detail_report: The detailed output messages of this scorer.
    :type detail_report: :class:`list` of
        :class:`railgun.common.lazy_i18n.GetTextString`
    """

    def __init__(self, scorer_name, scorer_type_name, score, weight, time,
                 brief_report, detail_report):
        #: The human readable name of this scorer.
        #: (:class:`railgun.common.lazy_i18n.GetTextString`)
        self.name = scorer_name
        #: The type name of this scorer.
        self.typeName = scorer_type_name
        #: The final score, range in [0, 100].
        self.score = score
        #: The weight of this scorer.
        self.weight = weight
        #: The running time of this scorer (in seconds).
        self.time = time
        #: The brief output message of this scorer.
        #: (:class:`railgun.common.lazy_i18n.GetTextString`)
        self.brief = brief_report
        #: The detailed output messages of this scorer.
        #: (class:`list` of :class:`railgun.common.lazy_i18n.GetTextString`)
        self.detail = detail_report

    def to_plain(self):
        """Convert this partial score object to a plain object that can be
        serialized in JSON message.

        :return: A plain object that is composed only with :class:`dict`,
            :class:`list`, :class:`str`, :class:`bool` and numeric types.
        """
        return {
            'name': lazystr_to_plain(self.name),
            'typeName': self.typeName,
            'score': self.score,
            'weight': self.weight,
            'time': self.time,
            'brief': lazystr_to_plain(self.brief),
            'detail': [lazystr_to_plain(d) for d in self.detail]
        }

    @property
    def get_time(self):
        """Get the running time of this scorer.

        :return: A :class:`datetime.timedelta` object, or :data:`None`
            if timing is not performed.
        """
        return timedelta(seconds=self.time) if self.time else None

    @staticmethod
    def from_plain(obj):
        """Make a :class:`HwPartialScore` object from a plain object.

        :raises: :class:`TypeError` or :class:`KeyError` if the given plain
            object does not represent a valid :class:`HwScore` object.
        """
        return HwPartialScore(
            plain_to_lazystr(obj['name']),
            obj['typeName'],
            obj['score'],
            obj['weight'],
            obj['time'],
            plain_to_lazystr(obj['brief']),
            [plain_to_lazystr(o) for o in obj['detail']],
        )


class HwScore(object):
    """A serializable final score object.

    :param accepted: Whether the submission is accepted?
    :type accepted: :class:`bool`
    :param result: A brief comment on the submission.
    :type result: :class:`railgun.common.lazy_i18n.GetTextString`
    :param compile_error: The compiler error message.
    :type compile_error: :class:`railgun.common.lazy_i18n.GetTextString`
        or :class:`basestring`
    :param partials: The :class:`HwPartialScore` objects.
    :type partials: :class:`list` of :class:`HwPartialScore`
    """

    def __init__(self, accepted, result=None, compile_error=None,
                 partials=None):
        # Whether the state of the submission is accepted?
        self.accepted = accepted
        #: A brief comment on the submission.
        #: (:class:`railgun.common.lazy_i18n.GetTextString`)
        self.result = result
        #: The compiler error message.
        #: (:class:`railgun.common.lazy_i18n.GetTextString` or
        #: :class:`basestring`)
        self.compile_error = compile_error
        #: The :class:`HwPartialScore` objects.
        #: (:class:`list` of :class:`HwPartialScore`)
        self.partials = partials or []

    def get_score(self):
        """Sum up the final score."""
        return sum([p.weight * p.score for p in self.partials])

    def add_partial(self, partial):
        """Add a :class:`HwPartialScore` object."""
        self.partials.append(partial)

    def to_plain(self):
        """Convert this partial score object to a plain object that can be
        serialized in JSON message.

        :return: A plain object that is composed only with :class:`dict`,
            :class:`list`, :class:`str`, :class:`bool` and numeric types.
        """
        return {
            'accepted': self.accepted,
            'result': lazystr_to_plain(self.result),
            'compile_error': lazystr_to_plain(self.compile_error),
            'partials': [p.to_plain() for p in self.partials],
        }

    @staticmethod
    def from_plain(obj):
        """Make a :class:`HwScore` object from a plain object.

        :raises: :class:`TypeError` or :class:`KeyError` if the given plain
            object does not represent a valid :class:`HwScore` object.
        """
        ret = HwScore(obj['accepted'], plain_to_lazystr(obj['result']),
                      plain_to_lazystr(obj['compile_error']))
        for p in obj['partials']:
            ret.partials.append(HwPartialScore.from_plain(p))
        return ret
