#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/website/scriptlibs.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

"""Modern html pages may rely on Javascript and CSS heavily.  To ease the
development of `dynamic` html pages, there comes some powerful libraries
and frameworks, along with lots of plugins based on these utilities.

For example, the most widely used Javascript extension library, `jQuery`,
is just a dependency of another widely used CSS framework, `Bootstrap`.
Moreover, the Bootstrap framework is also a necessary dependency for
many cool widgets, like `bootstrap-tags`, `bootstrap-timeselector`, and
so on.

It is guaranteed that the dependencies should be loaded before the
libraries who depends on them.  Then how to manage the dependency
relationship, produce the correct loading scripts, is a real problem.

This module provides to utility to register well-known libraries,
to generate dependency graph, and to produce loading scripts.
"""

import re
import operator
from itertools import izip_longest, chain

from flask import g, url_for

from .context import app


class Version(object):
    """Represent a dot splitted version, for example, `1.0.0`.

    :param version: A version literal, or another :class:`Version` object.
    :type version: :class:`str` or :class:`Version`.
    """

    def __init__(self, version):
        self.set(version)

    def __str__(self):
        return '.'.join([str(v) for v in self.data])

    def __repr__(self):
        return '<Version(%s)>' % str(self)

    def __cmp__(self, other):
        for a, b in izip_longest(self.data, other.data):
            c = cmp(a or 0, b or 0)
            if c != 0:
                return c
        return 0

    def set(self, value):
        """Assign the value to this version.

        :param value: A version literal, or another :class:`Version` object.
        :type version: :class:`str` or :class:`Version`.
        """
        if isinstance(value, str) or isinstance(value, unicode):
            self.data = tuple(int(v) for v in value.split('.'))
        elif isinstance(value, Version):
            self.data = value.data
        elif isinstance(value, tuple) or isinstance(value, list):
            self.data = tuple(value)
        else:
            raise TypeError('`value` is not a valid version object.')


class Dependency(object):
    """Represent a dependency.

    :param requirement: Dependency requirement literal or object.
        The literal may be just a simple package name, or a named followed
        by a version requirement.  For example:

        *   jQuery
        *   bootstrap >= 3.0
    :type requirement: :class:`str` or :class:`Dependency`
    """

    def __init__(self, requirement):
        self.set(requirement)

    def __str__(self):
        if self.pkgver:
            return '%s %s %s' % (self.pkgname, self.veropt, self.pkgver)
        else:
            return self.pkgname

    def __repr__(self):
        return '<Dependency(%s)>' % str(self)

    def set(self, requirement):
        """Assign the given value to this dependency object.

        :param requirement: Dependency requirement literal.
        :type requirement: :class:`str`
        :raises: :class:`ValueError` if the given requirement is ill-formed.
        """
        if isinstance(requirement, Dependency):
            self.pkgname = requirement.pkgname
            self.pkgver = requirement.pkgver
            self.veropt = requirement.veropt
            self._checker = requirement._checker
            return

        # Parse the requirement
        p = re.compile(
            '^\\s*(?P<name>\\S+)\\s*'
            '((?P<opt>(>=|>|==|<|<=))\\s*(?P<ver>[0-9.]+)\\s*)?$'
        )
        m = p.match(requirement)
        if not m:
            raise ValueError('ill-formed version requirement.')
        m = m.groupdict()

        # Setup dependency params
        self.pkgname = m['name']
        self.pkgver = Version(m['ver']) if m['ver'] else None
        self.veropt = m['opt']
        if self.veropt:
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
        """Check whether the given version meets the version requirement
        of this dependency.  The package name is not compared.

        :param version: A :class:`Version` object.
        """
        return self._checker(version, self.pkgver)


class DependencySet(object):
    """Store a set of dependencies.

    :param deps: Initialize the :class:`DependencySet` with a set of dependency
        objects.
    :type deps: iterable object over :class:`Dependency` instances
    """

    def __init__(self, deps=None):
        # `depends` should be a dict: pkgname => Dependency()
        deps = [Dependency(d) for d in deps] if deps else []

        #: A :class:`dict` of {pkgname: :class:`Dependency`}
        self.data = {d.pkgname: d for d in deps}

    def __iter__(self):
        return iter(self.data.itervalues())

    def __repr__(self):
        return repr(self.data)

    def deps(self, requirement):
        """Add a dependency to this set.

        If the name of package in the requirement already exists, we will
        replace the old dependency with new one only if the version is
        higher, or the old one does not specify a version.

        .. note::

            This behaviour should be changed!  Consider to combine the
            version requirements, or just store all the dependency
            objects with the same package name.

        :param requirement: A requirement literal or object.
        :type requirement: :class:`str` or :class:`Dependency`.
        """
        deps = Dependency(requirement)
        old_deps = self.data.get(deps.pkgname, None)
        # The following codes equal to these pseudocode:
        #
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
        """Check whether a package with given version can satisfy this
        dependency set.

        :param name: The name of the package.
        :type name: :class:`str`
        :param version: The version object.
        :type version: :class:`Version`
        """
        return self.data[name].check(version)


class ScriptLib(object):
    """Represent a script library, store its name, version, dependencies,
    and all its script resources.

    :param name: The name of this library.
    :type name: :class:`str`
    :param version: A version literal or object.
    :type version: :class:`str` or :class:`Version`
    :param headStyles: A :class:`list` of style sheet urls between
        <head> and </head>.
    :type headStyles: :class:`list` of :class:`str`
    :param headScripts: A :class:`list` of script file urls between
        <head> and </head>.
    :type headScripts: :class:`list` of :class:`str`
    :param tailScripts: A :class:`list` of script file urls before </body>.
    :type tailScripts: :class:`list` of :class:`str`
    """

    def __init__(self, name, version, deps=None, headStyles=None,
                 headScripts=None, tailScripts=None):
        #: The name of the script.
        self.name = name

        #: The :class:`Version` object of this library.
        self.version = Version(version)

        #: The :class:`DependencySet` object of this library.
        self.depends = DependencySet(deps)

        #: A :class:`list` of style sheet urls between <head> and </head>.
        self.headStyles = headStyles or []

        #: A :class:`list` of script file urls between <head> and </head>.
        self.headScripts = headScripts or []

        #: A :class:`list` of script file urls before </body>.
        self.tailScripts = tailScripts or []

    def __str__(self):
        return '%s %s' % (self.name, self.version)

    def __repr__(self):
        return '<Script(%s)>' % str(self)

    def deps(self, requirement):
        """Add a dependency to this script library.

        :param requirement: A dependency literal or object.
        :type requirement: :class:`str` or :class:`Dependency`
        """
        self.depends.add(requirement)

    def checkdep(self, script):
        """Check whether the given script object can be the dependency
        of this script library.

        :param script: The script library object.
        :type script: :class:`ScriptLib`
        """
        return self.depends.checkdep(script.name, script.version)


class ScriptRepo(object):
    """The registry of all script libraries."""

    def __init__(self):
        #: The :class:`dict` of {script-name -> :class:`ScriptLib`}.
        self.scripts = {}

    def addScript(self, script):
        """Add a script object into repo.

        :param script: The script library object.
        :type script: :class:`ScriptLib`
        """

        old_script = self.scripts.get(script.name, None)
        if not old_script or old_script.version < script.version:
            self.scripts[script.name] = script

    def getScript(self, name):
        """Get the script object with given name.

        :param name: Name of requested script library object.
        :type name: :class:`str`
        """
        return self.scripts.get(name, None)


class PageScripts(object):
    """Gather the script libraries used by current page."""

    def __init__(self, deps=None):
        #: The dependency set of this page.
        #: Each may be a script name followed by a version requirement.
        self.depends = DependencySet(deps)

        # Whether or not the dependency tree is fresh?
        self._deporder = None

    def deps(self, requirement):
        """Add a dependency to this page.

        :param requirement: A dependency literal or object.
        :type requirement: :class:`str` or :class:`Dependency`
        """
        dep = Dependency(requirement)
        self.depends.deps(dep)
        self._deporder = None

    def _depScript(self, dep):
        """Get the corresponding script object according to the dependency.

        :param dep: A dependency literal or object.
        :type dep: :class:`str` or :class:`Dependency`
        :return: A :class:`ScriptLib` object corresponding to the requirement.
        :raises: :class:`ValueError` if the requirement cannot be satisfied.
        """

        dep = Dependency(dep)
        script = scripts.getScript(dep.pkgname)
        if not script:
            raise ValueError(
                'Dependency "%s" cannot satisfy: library not installed.' % dep
            )
        if not dep.check(script.version):
            raise ValueError(
                'Dependency "%s" cannot satisfy: installed version is %s.' %
                (dep, script.version)
            )
        return script

    def _discover(self, script, visit_set, trace_set, dep_order):
        """DFS the dependency graph for current page.

        :param script: The visiting script library object.
        :type script: :class:`ScriptLib`
        :param visit_set: The set of visited script library objects.
        :type visit_set: :class:`set` of :class:`ScriptLib`
        :param trace_set: The set of script library objects on the trace.
            This set is used to detect the circular dependency.
        :type trace_set: :class:`set` of :class:`ScriptLib`
        :param dep_order: Output :class:`ScriptLib` in dependency order
            into this :class:`list`.
        :type dep_order: :class:`list`
        """

        # detect cirular dependency
        if script.name in trace_set:
            raise ValueError('Circular dependency "%s".' % script.name)
        trace_set.add(script.name)

        # return if already added to dep_order
        if script.name in visit_set:
            return
        visit_set.add(script.name)

        # add all deps to dep order
        for d in script.depends:
            ds = self._depScript(d)
            self._discover(ds, visit_set, trace_set, dep_order)

        # add this script into dep_order
        dep_order.append(script)

        # remove current library from trace set
        trace_set.remove(script.name)

    def _deptree(self):
        """Sort the scripts in dependency order, and cache the result."""
        if self._deporder:
            return

        visit_set = set()
        self._deporder = []
        for d in self.depends:
            self._discover(
                self._depScript(d), visit_set, set(), self._deporder)

    def _urllist(self, iterable):
        """Some urls provided in :class:`ScriptLib` object may be
        :func:`callable` objects that should be formatted until they are used.
        This method formats all these `lazy` urls.

        :return: A :class:`list` of urls.
        """
        F = lambda u: u() if callable(u) else u
        return [F(u) for u in iterable]

    def headStyles(self):
        """Get the urls of all style sheets between <head> and </head>.

        :return: A :class:`list` of urls.
        """
        self._deptree()
        return self._urllist(chain(*[s.headStyles for s in self._deporder]))

    def headScripts(self):
        """Get the urls of all script files between <head> and </head>.

        :return: A :class:`list` of urls.
        """
        self._deptree()
        return self._urllist(chain(*[s.headScripts for s in self._deporder]))

    def tailScripts(self):
        """Get the urls of all script files before </body>.

        :return: A :class:`list` of urls.
        """
        self._deptree()
        return self._urllist(chain(*[s.tailScripts for s in self._deporder]))


@app.before_request
def __inject_page_scripts():
    g.scripts = PageScripts(deps=[
        'railgun >= 1.0',
    ])


#: The global :class:`ScriptRepo` to register all installed script libraries.
#: In Railgun system, these libraries are registered by default:
#:
#: *    jquery == 1.11.1
#: *    bootstrap == 3.2.0
#: *    railgun == 1.0.0
#: *    handlebars == 1.3.0
#: *    typeahead.js == 0.10.5
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
        lambda: url_for('static', filename='css/bootstrap-theme.min.css'),
    ],
    tailScripts=[
        lambda: url_for('static', filename='js/bootstrap.min.js'),
    ],
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
    ],
    tailScripts=[
        lambda: url_for('static', filename='js/railgun.js'),
    ],
))
scripts.addScript(ScriptLib(
    name='handlebars',
    version='1.3.0',
    tailScripts=[
        lambda: url_for('static', filename='js/handlebars-v1.3.0.js'),
    ]
))
scripts.addScript(ScriptLib(
    name='typeahead.js',
    version='0.10.5',
    deps=[
        'jquery >= 1.9.0',
        'handlebars >= 1.3.0',
        'bootstrap >= 3',
    ],
    headStyles=[
        lambda: url_for('static', filename='css/typeaheadjs.css')
    ],
    tailScripts=[
        lambda: url_for('static', filename='js/typeahead.jquery.min.js'),
        lambda: url_for('static', filename='js/bloodhound.min.js'),
    ]
))
