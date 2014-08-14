#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/website/scriptlibs.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Contributors:
#   public@korepwx.com   <public@korepwx.com>
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import re
import operator
from itertools import izip_longest, chain

from flask import g, url_for

from .context import app


class Version(object):
    """Represent a dot splitted version."""

    def __init__(self, version):
        self.set(version)

    def __str__(self):
        return '.'.join([str(v) for v in self.version])

    def __cmp__(self, other):
        for a, b in izip_longest(self.data, other.data):
            c = cmp(a or 0, b or 0)
            if (c != 0):
                return c
        return 0

    def set(self, value):
        """Set the version with given `value`."""
        if (isinstance(value, str) or isinstance(value, unicode)):
            self.data = tuple(int(v) for v in value.split('.'))
        elif (isinstance(value, Version)):
            self.data = value.data
        elif (isinstance(value, tuple) or isinstance(value, list)):
            self.data = tuple(value)
        else:
            raise TypeError('`value` is not a valid version object.')


class Dependency(object):
    """Represent a dependency (pkgname, pkgver)."""

    def __init__(self, requirement):
        self.set(requirement)

    def __str__(self):
        if (self.pkgver):
            return '%s %s %s' % (self.pkgname, self.veropt, self.pkgver)
        else:
            return self.pkgname

    def set(self, requirement):
        """Set the requirement value."""
        if (isinstance(requirement, Dependency)):
            self.pkgname = requirement.pkgname
            self.pgkver = requirement.pkgver
            self.veropt = requirement.veropt
            self._checker = requirement._checker
            return

        # Parse the requirement
        p = re.compile(
            '^\\s*(?P<name>\\S+)\\s*'
            '((?P<opt>(>=|>|==|<|<=))\\s*(?P<ver>[0-9.]+)\\s*)?$'
        )
        m = p.match(requirement)
        if (not m):
            raise ValueError('ill-formed version requirement.')
        m = m.groupdict()

        # Setup dependency params
        self.pkgname = m['name']
        self.pkgver = m['ver']
        self.veropt = m['opt']
        if (self.veropt):
            self._checker = {
                '>=': operator.ge,
                '>': operator.gt,
                '==': operator.eq,
                '<': operator.lt,
                '<=': operator.le,
            }.get(self.veropt)
        else:
            self._checker = lambda v1, v2: True

    def check(self, version):
        """Check whether given `version` meets requirement."""
        return self._checker(version, self.pkgver)


class DependencySet(object):
    """Manage a set of dependencies."""

    def __init__(self, deps=None):
        # `depends` should be a dict: pkgname => Dependency()
        deps = [Dependency(d) for d in deps] if deps else []
        self.data = {d.pkgname: d for d in deps}

    def __iter__(self):
        return iter(self.data)

    def deps(self, requirement):
        deps = Dependency(requirement)
        old_deps = self.data.get(deps.pkgname, None)
        # if old_deps not exist:
        #   add this dependency.
        # if old_deps exist:
        #    if old_deps.pkgver is None:
        #      replace this dependency
        #    elif deps.pkgver is not None, and deps.pkgver > old_deps.pkgver:
        #      replace this dependency
        if ((not old_deps) or (not old_deps.pkgver) or
                (deps.pkgver and deps.pkgver > old_deps.pkgver)):
            self.data[deps.pkgname] = deps

    def checkdep(self, name, version):
        return self.data[name].check(version)


class ScriptLib(object):
    """Manage the name, version, URL, and dependencies of external script."""

    def __init__(self, name, version, deps=None, headStyles=None,
                 headScripts=None, tailScripts=None):
        self.name = name
        self.version = Version(version)

        # `depends` should be a dict: pkgname => Dependency()
        self.depends = DependencySet(deps)

        # headStyles is the CSS files between <head></head>
        # headScripts is the JS files between <head></head>
        # tailScripts is the JS files between <head></head>
        self.headStyles = headStyles or []
        self.headScripts = headScripts or []
        self.tailScripts = tailScripts or []

    def __str__(self):
        return '%s %s' % (self.name, self.version)

    def deps(self, requirement):
        """Add dependency on ScriptLib `requirement`."""
        self.depends.add(requirement)

    def checkdep(self, script):
        """Check whether `script` can be provided as dependency `name` for
        this library."""
        return self.depends.checkdep(script.name, script.version)


class ScriptRepo(object):
    """Register all script libs in a repo."""

    def __init__(self):
        self.scripts = {}

    def addScript(self, script):
        """Add a script into repo."""

        old_script = self.scripts.get(script.name, None)
        if ((not old_script) or (old_script.version < script.version)):
            self.scripts[script.name] = script

    def getScript(self, name):
        """Get the script with given `name`."""
        return self.scripts.get(name, None)


class PageScripts(object):
    """Manage the script libs used by current page."""

    def __init__(self, deps=None):
        self.depends = DependencySet(deps)
        # Whether or not the dependency tree is fresh?
        self._deporder = None

    def deps(self, requirement):
        dep = Dependency(requirement)
        self.depends.deps(dep)
        self._deporder = None

    def _depScript(self, dep):
        """Get the script object from `dep`."""
        dep = Dependency(dep)
        script = scripts.getScript(dep.pkgname)
        if (not script):
            raise ValueError(
                'Dependency "%s" cannot satisfy: library not installed.' % dep
            )
        if (not dep.check(script.version)):
            raise ValueError(
                'Dependency "%s" cannot satisfy: only "%s" is installed.' %
                (dep, script)
            )
        return script

    def _discover(self, script, visit_set, trace_set, dep_order):
        """Recursively discover the dependency tree."""

        # detect cirular dependency
        if (script.name in trace_set):
            raise ValueError('Circular dependency "%s".' % script.name)
        trace_set.add(script.name)

        # return if already added to dep_order
        if (script.name in visit_set):
            return
        visit_set.add(script.name)

        # add all deps to dep order
        for d in script.depends:
            ds = self._depScript(d)
            self._discover(ds, visit_set, trace_set, dep_order)

        # add this script into dep_order
        dep_order.append(script)

    def _deptree(self):
        """Build dependency tree and sort all dependencies in order of tree."""
        if (self._deporder):
            return

        visit_set = set()
        self._deporder = []
        for d in self.depends:
            self._discover(self._depScript(d), visit_set, set(), self._deporder)

    def _urllist(self, iterable):
        """Some urls may be generated until used."""
        F = lambda u: u() if callable(u) else u
        return [F(u) for u in iterable]

    def headStyles(self):
        """Get list of all head styles."""
        self._deptree()
        return self._urllist(chain(*[s.headStyles for s in self._deporder]))

    def headScripts(self):
        """Get list of all head scripts."""
        self._deptree()
        return self._urllist(chain(*[s.headScripts for s in self._deporder]))

    def tailScripts(self):
        """Get list of all tail scripts."""
        self._deptree()
        return self._urllist(chain(*[s.tailScripts for s in self._deporder]))


@app.before_request
def __inject_page_scripts():
    g.scripts = PageScripts(deps=[
        'railgun >= 1.0'
    ])


# Initialize the script repo, and add default libraries
scripts = ScriptRepo()
scripts.addScript(ScriptLib(
    name='jquery',
    version='1.11.1',
    tailScripts=[
        # url_for can only be used until request is constructed
        # so pass in a lambda object.
        lambda: url_for('static', filename='js/jquery-1.11.1.min.js'),
    ]
))
scripts.addScript(ScriptLib(
    name='bootstrap',
    version='3.2.0',
    deps=[
        'jquery >= 1.9.0',
    ],
    headStyles=[
        lambda: url_for('static', filename='css/bootstrap.min.css'),
    ],
    tailScripts=[
        lambda: url_for('static', filename='js/bootstrap.min.js'),
    ]
))
scripts.addScript(ScriptLib(
    name='railgun',
    version='1.0.0',
    deps=[
        'bootstrap >= 3',
    ],
    headStyles=[
        lambda: url_for('static', filename='css/railgun.css'),
        lambda: url_for('static', filename='css/codehilite.css'),
    ]
))
