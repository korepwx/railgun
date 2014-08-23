#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/common/hw.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import re
import os
from datetime import datetime
from xml.etree import ElementTree
from itertools import ifilter, chain

from markdown import markdown
from babel.dates import timedelta, get_timezone, UTC

import config
from . import fileutil
from .fileutil import file_get_contents
from .lazy_i18n import lazystr_to_plain, plain_to_lazystr
from .url import reform_path, UrlMatcher


def parse_bool(s):
    """Convert a string into bool value."""
    if (not s):
        return False
    s = str(s).lower()
    return (s == 'true' or s == 'on' or s == '1' or s == 'yes')


def to_utc(dt):
    """Convert datetime instance `dt` to UTC datetime."""
    return dt.astimezone(UTC)


def utc_now():
    """get now datetime whose timezone is UTC."""
    return UTC.localize(datetime.utcnow())


def get_comm_key():
    """Load encryption key from `keys/commKey.txt`."""
    with open(os.path.join(config.RAILGUN_ROOT, 'keys/commKey.txt'), 'rb') as f:
        return f.read().strip()


class FileRules(object):
    """Store and manipulate file match rules."""

    # The pre-defined actions for files
    ACCEPT, LOCK, HIDE, DENY = range(4)

    def __init__(self):
        # list of (action, pattern)
        self.data = []

    def __repr__(self):
        return repr(self.data)

    def get_action(self, filename, default_action=LOCK):
        """Get the action for given `filename`."""

        for a, p in self.data:
            if (p.match(filename)):
                return a

        # if no rule matches, default takes lock action
        return default_action

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
        # the formatted description of this homework, used for caching
        # pre-calculated value
        self.formatted_desc = None

    def format_desc(self, hwslug):
        """Format the markdown description in `lang` locale."""
        # To expose static resources in homework desc directory, we need to
        # convert all "hw://<path>" urls to hwstatic view urls.
        def translate_url(u):
            # Get rid of 'hw://' and leading '/'
            u = reform_path(u[5:])
            if (u.startswith('/')):
                u = u[1:]
            # translate to hwstatic file
            filename = '%s/%s' % (hwslug, u)
            # NOTE: here I hardcoded the url for hwstatic!
            ret = '/hwstatic/%s' % filename
            # we also need to prepend website base url
            return config.WEBSITE_BASEURL + ret

        text = UrlMatcher(['hw']).replace(self.desc, translate_url)
        self.formatted_desc = markdown(
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

        # whether or not this code package provides attachment
        self.has_attach = True
        # the compiler parameters of this code package
        self.compiler_params = None
        # the runner parameters of this code package
        self.runner_params = None
        # the file match rules of this code package
        self.file_rules = None
        # settings for display the submission
        self.reportCompile = True
        self.reportRuntime = False

    def __repr__(self):
        return '<HwCode(%s)>' % self.path

    @staticmethod
    def load(path, lang):
        """Load the code package under `path`."""

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

        # Pre-build all descriptions
        ret.cache_formatted_desc()
        return ret

    def cache_formatted_desc(self):
        """Format and cache the descriptions in all locales.

        In the performance profiler, formatting the homework description
        can take up to 100ms.  So I decide to pre-calculate and cache all
        formatted descriptions.
        """
        for i in self.info:
            i.format_desc(self.slug)

    def get_name_locales(self):
        """Get the name locales provided by this homework."""
        return [i.lang for i in self.info]

    def get_code_languages(self):
        """Get the programming languages provided by this homework."""
        return sorted([c.lang for c in self.codes])

    def get_code(self, lang):
        """Get HwCode instance for `lang`"""
        return [c for c in self.codes if c.lang == lang][0]

    def count_attach(self):
        """Count the number of HwCode packages having attachment."""
        ret = 0
        for c in self.codes:
            if (c.has_attach):
                ret += 1
        return ret

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

    def get_last_deadline(self):
        """get the last deadline of this homework. return (date, scale)."""

        now = utc_now()
        ddl = self.deadlines[-1]
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

    def get_uuid_list(self):
        """Get uuid list of all homeworks."""
        return [hw.uuid for hw in self.items]


class HwPartialScore(object):
    """A serializable partial score object."""

    def __init__(self, scorer_name, scorer_type_name, score, weight, time,
                 brief_report, detail_report):
        self.name = scorer_name
        self.typeName = scorer_type_name
        self.score = score
        self.weight = weight
        self.time = time
        self.brief = brief_report
        self.detail = detail_report

    def to_plain(self):
        """Convert this partial score object to plain object."""
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
        """Get timedelta object for the run time."""
        return timedelta(seconds=self.time) if self.time else None

    @staticmethod
    def from_plain(obj):
        """Convert plain object to partial score object."""
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
    """A serializable final score object, set of `HwPartialScore`."""

    def __init__(self, accepted, result=None, compile_error=None,
                 partials=None):
        # `accepted` indicate whether final state of this handin is Accepted
        # or Rejected.
        self.accepted = accepted
        # brief result message string
        self.result = result
        # detailed compile error message
        self.compile_error = compile_error
        # all partial scores to be sumed up
        self.partials = partials or []

    def get_score(self):
        """Sum the final score."""
        total_weight = float(sum([p.weight for p in self.partials]))
        return sum([p.weight * p.score / total_weight for p in self.partials])

    def add_partial(self, partial):
        """Add a partial score into this final score."""
        self.partials.append(partial)

    def to_plain(self):
        """Convert this final score object to plain object."""
        return {
            'accepted': self.accepted,
            'result': lazystr_to_plain(self.result),
            'compile_error': lazystr_to_plain(self.compile_error),
            'partials': [p.to_plain() for p in self.partials],
        }

    @staticmethod
    def from_plain(obj):
        """Convert plain object to final score object."""

        ret = HwScore(obj['accepted'], plain_to_lazystr(obj['result']),
                      plain_to_lazystr(obj['compile_error']))
        for p in obj['partials']:
            ret.partials.append(HwPartialScore.from_plain(p))
        return ret
