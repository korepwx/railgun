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
import pprint
from datetime import datetime
from xml.etree import ElementTree
from itertools import ifilter, imap

from babel.dates import get_timezone

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


class _UtcDateConvertor(object):
    """Convert datetime instance `dt` to UTC datetime."""

    UTC = get_timezone('UTC')

    @staticmethod
    def convert(dt):
        return dt.astimezone(get_timezone('UTC'))

# the class wrapper is used to store `UTC` timezone instance.
to_utc = _UtcDateConvertor.convert


class ConfigNode(object):
    """Class to represent a configuration node."""

    def __init__(self):
        # a `ConfigNode` can either have a value or children nodes.
        self.name = None
        self.value = None
        self.children = None

        # any type of `ConfigNode` can have attrs
        self.attrs = None

    def __repr__(self):
        def F(c, depth=0):
            ret = {'name': c.name}
            if (c.has_child):
                ret['children'] = [F(cc) for cc in c.children]
            else:
                ret['value'] = c.value
            if (c.attrs):
                ret['attrs'] = c.attrs
            return ret
        return pprint.pformat(F(self))

    def get(self, name, default=None):
        """Get `name` attr value. return `default` if not defined."""
        return self.attrs.get(name, default)

    @property
    def has_child(self):
        """Whether this node has children nodes?"""
        return self.children is not None

    @staticmethod
    def parse_xml(xmlnode):
        """Create the root `ConfigNode` according to given `xmlnode`."""

        def F(nd):
            ret = ConfigNode()
            ret.name = nd.tag
            ret.attrs = nd.attrib

            if (len(nd) > 0):
                # a node can not have both value and children
                # so we should ignore nd.text
                ret.children = []
                for cnd in nd:
                    ret.children.append(F(cnd))
            else:
                ret.value = nd.text.strip() if nd.text else None

            return ret

        return F(xmlnode) if xmlnode is not None else ConfigNode()


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

    def add_action(self, action, pattern):
        """Add (action, pattern) into rule collection."""

        act = None
        if (action.isalpha()):
            act = getattr(FileRules, action.upper(), None)
        if (act is None):
            raise ValueError('Unknown action "%s" in file rule.' % action)
        pat = re.compile(pattern)
        self.data.append((act, pat))

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
        ret.add_action('hide', '^code\\.xml$')

        if (xmlnode is not None):
            for nd in xmlnode:
                ret.add_action(nd.tag, nd.text.strip())
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
        ret.compiler_params = ConfigNode.parse_xml(root.find('compiler'))
        ret.runner_params = ConfigNode.parse_xml(root.find('runner'))

        # parse the file match rules
        ret.file_rules = FileRules.parse_xml(root.find('files'))

        return ret


class Homework(object):
    """Class to parse and process a Railgun homework."""

    def __init__(self):
        """Initialize all homework settings to empty."""

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
        self.lower_better = False
        # file match rules for data directory
        self.data_rules = None
        # list of `HwCode` instances
        self.codes = []

    @staticmethod
    def load(path):
        """Load the contents of homework under `path`."""

        # Stage 1: load the homework meta data from hw.xml
        ret = Homework()
        ret.path = path
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
                        timezone = config.BABEL_DEFAULT_TIMEZONE
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
                ret.lower_better = nd.find('better').text.lower() == 'lower'
            elif (nd.tag == 'data'):
                ret.data_rules = FileRules.parse_xml(nd)

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

        return ret

    def get_name_locales(self):
        """Get the name locales provided by this homework."""
        return [i.lang for i in self.info]

    def get_code_languages(self):
        """Get the programming languages provided by this homework."""
        return [c.lang for c in self.codes]

    def pack_assignment(self, lang, filename):
        """Pack assignment zipfile for `lang` programming language."""

        # select the code package
        code = [c for c in self.codes if c.lang == lang][0]

        # prepare the file list in data directory.
        # only acceptable and locked files are given to students.
        #
        # note that items in dirtree(data-dir) will not contain 'data' in path.
        # so I prepend this structure using imap.
        data_files = imap(
            lambda f: 'data/' + f,
            self.data_rules.filter(
                fileutil.dirtree(os.path.join(self.path, 'data')),
                (FileRules.ACCEPT, FileRules.LOCK)
            )
        )
        data_files = list(data_files)

        # prepare the file list for given `lang`.
        code_files = code.file_rules.filter(
            fileutil.dirtree(code.path),
            (FileRules.ACCEPT, FileRules.LOCK)
        )

        # make target file name
        with fileutil.makezip(filename) as zipf:
            fileutil.packzip(self.path, data_files, zipf)
            fileutil.packzip(code.path, code_files, zipf)
