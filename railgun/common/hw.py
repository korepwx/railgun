#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/common/hw.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Contributors:
#   public@korepwx.com   <public@korepwx.com>
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import re
import os
from datetime import datetime
from xml.etree import ElementTree
from itertools import ifilter, chain

from babel.dates import get_timezone, UTC

import config
from . import fileutil


def parse_bool(s):
    """Convert a string into bool value."""
    if (not s):
        return False
    s = str(s).lower()
    return (s == 'true' or s == 'on' or s == '1' or s == 'yes')


def file_get_contents(path):
    """Get the content of `path`, or None if exception raised."""
    try:
        with open(path, 'rb') as f:
            return unicode(f.read(), 'utf-8')
    except Exception:
        pass


def to_utc(dt):
    """Convert datetime instance `dt` to UTC datetime."""
    return dt.astimezone(UTC)


def utc_now():
    """get now datetime whose timezone is UTC."""
    return UTC.localize(datetime.utcnow())


class FileRules(object):
    """Store and manipulate file match rules."""

    # The pre-defined actions for files
    ACCEPT, LOCK, HIDE, DENY = range(4)

    def __init__(self):
        # list of (action, pattern)
        self.data = []

    def __repr__(self):
        return repr(self.data)

    def get_action(self, filename):
        """Get the action for given `filename`."""

        for a, p in self.data:
            if (p.match(filename)):
                return a

        # if no rule matches, default takes lock action
        return FileRules.LOCK

    def _make_action(self, action, pattern):
        """Check the type and value of (action, pattern)."""

        act = None
        if (action.isalpha()):
            act = getattr(FileRules, action.upper(), None)
        if (act is None):
            raise ValueError('Unknown action "%s" in file rule.' % action)
        pat = re.compile(pattern)
        return (act, pat)

    def append_action(self, action, pattern):
        """Append (action, pattern) into rule collection."""
        self.data.append(self._make_action(action, pattern))

    def prepend_action(self, action, pattern):
        """Prepend (action, pattern) into rule collection."""
        self.data.insert(0, self._make_action(action, pattern))

    def filter(self, files, allow_actions):
        """Remove items in `files` whose action not in `allow_actions`."""

        return ifilter(
            lambda f: self.get_action(f) in allow_actions,
            files
        )

    @staticmethod
    def parse_xml(xmlnode):
        """Parse the rules defined in `xmlnode`."""

        ret = FileRules()

        # there should be at least one rule in file_rules: code.xml is
        ret.append_action('hide', '^code\\.xml$')

        if (xmlnode is not None):
            for nd in xmlnode:
                ret.append_action(nd.tag, nd.text.strip())
        return ret


class HwInfo(object):
    """Represent human readable information of homework."""

    def __init__(self, lang, name, desc):
        # the language name of this info.
        # compatible with request.accept_languages
        self.lang = lang
        # the name of this homework
        self.name = name
        # the description of this homework
        self.desc = desc

    def __repr__(self):
        __s = lambda s: s.encode('utf-8') if isinstance(s, unicode) else s
        return '<HwInfo(lang=%s,name=%s)>' % (self.lang, __s(self.name))


class HwCode(object):
    """Represent code package of homework."""

    def __init__(self, path, lang):
        # the base path of code package, under [hw.path]/code/[lang]
        self.path = path
        # the programming language of this code package
        self.lang = lang

        # the compiler parameters of this code package
        self.compiler_params = None
        # the runner parameters of this code package
        self.runner_params = None
        # the file match rules of this code package
        self.file_rules = None

    def __repr__(self):
        return '<HwCode(%s)>' % self.path

    @staticmethod
    def load(path, lang):
        """Load the code package under `path`."""

        ret = HwCode(path, lang)
        tree = ElementTree.parse(os.path.join(path, 'code.xml'))
        root = tree.getroot()

        # store compiler & runner param nodes
        ret.compiler_params = root.find('compiler')
        ret.runner_params = root.find('runner')

        # parse the file match rules
        ret.file_rules = FileRules.parse_xml(root.find('files'))

        # set default hidden rules
        ret.file_rules.prepend_action('hide', '^code\\.xml$')
        for r in config.DEFAULT_HIDE_RULES:
            ret.file_rules.prepend_action('hide', r)

        return ret


class Homework(object):
    """Class to parse and process a Railgun homework."""

    def __init__(self):
        """Initialize all homework settings to empty."""

        # url slug of this homework, usually last part of path
        self.slug = None
        # root path of this homework
        self.path = None
        # string of unique id
        self.uuid = None
        # list of `HwInfo` instances
        self.info = []
        # list of (date, scale) to represent deadlines
        self.deadlines = []
        # settings of scoring
        self.reportAll = False
        # file match rules for root directory
        self.file_rules = None
        # list of `HwCode` instances
        self.codes = []

    @staticmethod
    def load(path):
        """Load the contents of homework under `path`."""

        # Stage 1: load the homework meta data from hw.xml
        ret = Homework()
        ret.path = path
        ret.slug = os.path.split(path)[1]
        tree = ElementTree.parse(os.path.join(path, 'hw.xml'))

        for nd in tree.getroot():
            if (nd.tag == 'uuid'):
                ret.uuid = nd.text.strip()
            elif (nd.tag == 'names'):
                for name in nd.iter('name'):
                    lang = name.get('lang')
                    name = name.text.strip()
                    # To define the desc of homework information, [lang].md
                    # should be created under desc directory.
                    desc = file_get_contents(
                        os.path.join(path, 'desc/%s.md' % lang)
                    )
                    ret.info.append(HwInfo(lang, name, desc))
            elif (nd.tag == 'deadlines'):
                for due in nd.iter('due'):
                    # get the timezone of due date
                    timezone = due.find('timezone')
                    timezone = timezone.text if timezone is not None else None
                    if (not timezone):
                        timezone = config.DEFAULT_TIMEZONE
                    timezone = get_timezone(timezone.strip())
                    # parse the date string
                    duedate = timezone.localize(
                        datetime.strptime(due.find('date').text.strip(),
                                          '%Y-%m-%d %H:%M:%S')
                    )
                    # parse the factor
                    scale = float(due.find('scale').text.strip())
                    # add to deadline list
                    ret.deadlines.append((to_utc(duedate), scale))
            elif (nd.tag == 'scoring'):
                ret.reportAll = parse_bool(nd.find('reportAll').text)
            elif (nd.tag == 'files'):
                ret.file_rules = FileRules.parse_xml(nd)

        # Stage 2: discover all programming languages
        code_path = os.path.join(path, 'code')
        for pl in os.listdir(code_path):
            pl_path = os.path.join(code_path, pl)
            pl_meta = os.path.join(pl_path, 'code.xml')
            # only the directories with contains 'code.xml' may be programming
            # language definition
            if (not os.path.isfile(pl_meta)):
                continue
            # load the programming language definition
            ret.codes.append(HwCode.load(pl_path, pl))

        # Stage 3: check integrity
        if (not ret.info):
            raise ValueError('Homework name is missing.')

        # Stage 4: set default hidden rules
        ret.file_rules.prepend_action('hide', '^hw\\.xml$')
        ret.file_rules.prepend_action('hide', '^code/\\.*')
        ret.file_rules.prepend_action('hide', '^code$')
        ret.file_rules.prepend_action('hide', '^desc/\\.*')
        ret.file_rules.prepend_action('hide', '^desc$')
        for r in config.DEFAULT_HIDE_RULES:
            ret.file_rules.prepend_action('hide', r)

        return ret

    def get_name_locales(self):
        """Get the name locales provided by this homework."""
        return [i.lang for i in self.info]

    def get_code_languages(self):
        """Get the programming languages provided by this homework."""
        return sorted([c.lang for c in self.codes])

    def get_code(self, lang):
        """Get HwCode instance for `lang`"""
        return [c for c in self.codes if c.lang == lang][0]

    def pack_assignment(self, lang, filename):
        """Pack assignment zipfile for `lang` programming language."""

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
        """List all files for `lang` programming language."""
        # select the code package
        code = self.get_code(lang)

        # get list of root files
        root_hide = re.compile('^code$|^code/\\.*|^desc$|^desc/\\.*|^hw\\.xml$')
        root_files = ifilter(
            lambda s: not root_hide.match(s),
            fileutil.dirtree(self.path)
        )

        # get list of code files
        code_files = fileutil.dirtree(code.path)

        return chain(root_files, code_files)

    def get_next_deadline(self):
        """get the next deadline of this homework. return (date, scale)."""

        now = utc_now()
        for ddl in self.deadlines:
            if (ddl[0] >= now):
                return (ddl[0], ddl[1])


class HwSet(object):
    """Collection of all homeworks."""

    def __init__(self, hwdir):

        # `hwdir` is the root path of homework
        self.hwdir = hwdir
        # `items` store all discovered homeworks in order of `slug`.
        self.items = None

        # hash uuid & slug to items
        self.__uuid_to_hw = {}
        self.__slug_to_hw = {}

        self.reload()

    def reload(self):
        """reload the homeworks from directory."""

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
        """get iterable object through all homeworks."""
        return iter(self.items)

    def get_by_uuid(self, uuid):
        return self.__uuid_to_hw.get(uuid, None)

    def get_by_slug(self, slug):
        return self.__slug_to_hw.get(slug, None)
