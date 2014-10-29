#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: runlib/python/pyhost/objschema.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

"""This module provides the utilities to define the rules of object
structures, and to validate the student submissions using these rules.
"""

import sys

from railgun.common.lazy_i18n import lazy_gettext


class SchemaResultCollector(object):
    """The collector of the results of schema.
    Detailed messages of the schema should be LazyString instances.
    """

    def __init__(self):
        self.clear()

    def clear(self):
        """Clear all the statistics of this result set."""
        self.errors = []
        self.total = 0
        self.error = 0

    def addSuccess(self):
        """Add a success check point to this result collector."""
        self.total += 1

    def addError(self, msg):
        """Add an error check point to this result collector."""
        self.errors.append(msg)
        self.total += 1
        self.error += 1


class SchemaExistRule(object):
    """The existence rule of objects."""

    #: The related object is required to exist.
    REQUIRE = 0

    #: The related object is allowed to exist.
    ALLOW = 1

    #: The related object is not allowed to exist.
    DENY = 2


class BaseSchema(object):
    """The base class for all kinds of schemas.

    A `schema` is a set of rules that defines the structure of particular
    objects.  It takes a regular expression as pattern to match the objects,
    and check the object according the defined rules.

    The basic rule of any schema is the existence of object.  The object
    may be marked as `REQUIRE`, `ALLOW` or `DENY`.  If not defined, default
    rule is `ALLOW`.

    :param parent: The parent object whose members will be validated by
        this schema.
    :type parent: :class:`object`
    :param pattern: The name pattern to filter members in the parent.
        The matched elements will be validated by this schema.
    :type pattern: :class:`str` or :class:`~_sre.SRE_Pattern`
    """

    def __init__(self, parent, pattern):
        if (pattern is not None and
                not isinstance(pattern, basestring) and
                not hasattr(pattern, 'match')):
            raise TypeError("`pattern` must be a string or a regex object.")
        #: The parent object whose members will be validated by this schema.
        self.parent = parent
        #: The name pattern to filter members in the parent.
        self.pattern = pattern
        #: Whether any object matched by this schema exists?
        self.exist = False
        #: The rule of existence for objects matched by this schema.
        self.exist_rule = SchemaExistRule.ALLOW
        #: Store the objects matched by this schema.
        self.objects = []
        #: Store the schemas who takes the items in :attr:`objects` as
        #: parents (or, the children of this schema).
        self.children = []

    def _match_attrs(self):
        """Select the members in the whose name matches :attr:`pattern`.

        :return: An iterable object over the members.
        """
        # If parent not exist, no attrs could match
        if not self.parent.exist:
            return
        # match the objects from each parent
        for po in self.parent.objects:
            if isinstance(self.pattern, basestring):
                if hasattr(po, self.pattern):
                    yield getattr(po, self.pattern)
            else:
                for objn in dir(po):
                    if self.pattern.match(objn):
                        yield getattr(po, objn)

    def _pattern_string(self):
        """Get the string representation of pattern."""
        if self.pattern is None:
            return
        if isinstance(self.pattern, basestring):
            return self.pattern
        # The pattern is not string, so it should be regex object.
        return self.pattern.pattern

    def print_tree(self, pad=0):
        """Recursively print the schema tree."""
        print '%s%s' % (' ' * pad, self.get_description())
        for c in self.children:
            c.print_tree(pad+2)

    def get_description(self):
        """Get a one line description of this schema."""
        raise NotImplementedError()

    def allow(self):
        """Mark this schema as ALLOW, and return this schema itself."""
        self.exist_rule = SchemaExistRule.ALLOW
        return self

    def deny(self):
        """Mark this schema as DENY, and return this schema itself."""
        self.exist_rule = SchemaExistRule.DENY
        return self

    def require(self):
        """Mark this schema as REQUIRE, and return this schema itself."""
        self.exist_rule = SchemaExistRule.REQUIRE
        return self

    def check(self, collector):
        """Check all the rules from this schema to its children recursively,
        and put the results in `collector`.
        """
        #: Gather the objects related to this schema, and set :attr:`exist`
        #: flag.
        self.check_self(collector)
        #: Test the :attr:`exist` flag again :attr:`exist_rule`.
        self.check_require(collector)
        #: If any object matching this schema exists, check the children
        #: schema.
        self.check_children(collector)

    def check_self(self, collector):
        """Check all the rules of this schema.

        Derived classes should update `exist` value, indicating whether
        the object of this schema exists.
        """

    def check_children(self, collector):
        """If this schema exists, check all children."""
        for c in self.children:
            c.check(collector)

    def check_require(self, collector):
        """Check whether this schema is marked as `REQUIRE` but the object
        does not exist.  All the children schema will also be notified.
        """
        if self.exist_rule == SchemaExistRule.REQUIRE and not self.exist:
            collector.addError(lazy_gettext(
                '%(schema)s is required but the object does not exist or '
                'could not be loaded.',
                schema=self.get_description()
            ))
        elif self.exist_rule == SchemaExistRule.DENY and self.exist:
            collector.addError(lazy_gettext(
                '%(schema)s is denied but the object exists.',
                schema=self.get_description()
            ))
        else:
            collector.addSuccess()


class RootSchema(BaseSchema):
    """The root schema that manages a set of file schema instances.

    :param rootpath: The root path of the files matched by this schema.
    :type rootpath: :class:`str`
    """

    def __init__(self, rootpath):
        super(RootSchema, self).__init__(parent=None, pattern=None)
        self.rootpath = rootpath

    def get_description(self):
        return 'ROOT'

    def module(self, pattern):
        """Add a :class:`ModuleSchema` to this :class:`RootSchema`.

        :param pattern: The full name of module.
        :type pattern: :class:`str`
        :return: This :class:`RootSchema` instance itself.
        """
        ms = ModuleSchema(self, pattern)
        self.children.append(ms)
        return ms

    def check_self(self, collector):
        self.exist = True

    def check_require(self, collector):
        # Root schema should report neither success or failure.
        pass


class ModuleSchema(BaseSchema):
    """The object structure rules for a module.

    :param parent: The parent :class:`RootSchema`.
    :param pattern: The module name.
    """

    def __init__(self, parent, pattern):
        if not isinstance(pattern, basestring):
            raise TypeError("Module schema only takes string patterns.")
        super(ModuleSchema, self).__init__(parent, pattern)

    def get_description(self):
        return self._pattern_string()

    def check_self(self, collector):
        try:
            __import__(self.pattern)
            self.objects = [sys.modules[self.pattern]]
            self.exist = True
        except:
            # We must catch all types of exceptions, otherwise the user
            # uploaded code may raise KeyboardInterrupt to reveal server
            # files, in that SchemaScorer often outputs the detail output.
            self.objects = []
            self.exist = False

    def class_(self, pattern):
        """Add a :class:`ClassSchema` to this :class:`ModuleSchema`.

        :param pattern: The name pattern to match the classes.
        :type pattern: :class:`str` or :class:`~_sre.SRE_Pattern`
        :return: This :class:`ModuleSchema` instance itself.
        """
        cs = ClassSchema(self, pattern)
        self.children.append(cs)
        return cs


class ClassSchema(BaseSchema):
    """The object structure rules for the classes belong to a parent module.

    :param parent: The parent :class:`ModuleSchema`
    :param pattern: The name pattern to match member classes.
    """

    def __init__(self, parent, pattern):
        super(ClassSchema, self).__init__(parent, pattern)

    def get_description(self):
        return '%s.%s' % (
            self.parent.get_description(), self._pattern_string())

    def check_self(self, collector):
        self.objects = list(self._match_attrs())
        self.exist = not not self.objects

    def method(self, pattern):
        """Add a :class:`MethodSchema` to this :class:`ClassSchema`.

        :param pattern: The name pattern to match the methods.
        :type pattern: :class:`str` or :class:`~_sre.SRE_Pattern`
        :return: This :class:`ClassSchema` instance itself.
        """
        ms = MethodSchema(self, pattern)
        self.children.append(ms)
        return ms


class MethodSchema(BaseSchema):
    """The object structure rules for the methods belong to a parent class.

    :param parent: The parent :class:`ClassSchema`
    :param pattern: The name pattern to match member methods.
    """

    def __init__(self, parent, pattern):
        super(MethodSchema, self).__init__(parent, pattern)

    def get_description(self):
        return '%s.%s' % (
            self.parent.get_description(), self._pattern_string())

    def check_self(self, collector):
        self.objects = list(self._match_attrs())
        self.exist = not not self.objects
