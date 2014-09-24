#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: runlib/python/pyhost/objschema.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

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

    REQUIRE = 0
    ALLOW = 1
    DENY = 2


class BaseSchema(object):
    """The base class for all kinds of schemas.

    A `schema` is a set of rules that defines the structure of particular
    objects.  It takes a regular expression as pattern to match the objects,
    and check the object according the defined rules.

    The basic rule of any schema is the existence of object.  The object
    may be marked as REQUIRE, ALLOW or DENY.  If not defined, default is
    ALLOW.
    """

    def __init__(self, parent, pattern):
        if (pattern is not None and
                not isinstance(pattern, basestring) and
                not hasattr(pattern, 'match')):
            raise TypeError("`pattern` must be a string or a regex object.")
        self.parent = parent
        self.pattern = pattern
        # The object existence of this schema. This value should be updated
        # in `check_self` method.
        self.exist = False
        self.exist_rule = SchemaExistRule.ALLOW
        # If `exist`, `objects` should store the reference to the objects
        # matching this schema after `check_self` is called.
        self.objects = []
        # The children rules of this schema
        self.children = []

    def _match_attrs(self):
        """Select the objects from parent matching `pattern` by getattr."""
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
        """Get the string of pattern."""
        if self.pattern is None:
            return
        if isinstance(self.pattern, basestring):
            return self.pattern
        # The pattern is not string, so it should be regex object.
        return self.pattern.pattern

    def get_description(self):
        """Get the one-line description of this schema."""
        raise NotImplementedError()

    def allow(self):
        """Mark this schema as ALLOW, and return the schema instance."""
        self.exist_rule = SchemaExistRule.ALLOW
        return self

    def deny(self):
        """Mark this schema as DENY, and return the schema instance."""
        self.exist_rule = SchemaExistRule.DENY
        return self

    def require(self):
        """Mark this schema as REQUIRE, and return the schema instance."""
        self.exist_rule = SchemaExistRule.REQUIRE
        return self

    def check(self, collector):
        """Check this schema with 3 steps: check_self, check_children,
        check_require.
        """
        self.check_self(collector)
        self.check_require(collector)
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
        """Check whether this schema is marked as REQUIRE but the object
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
    """The root schema that manages a set of file schema instances."""

    def __init__(self, rootpath):
        super(RootSchema, self).__init__(parent=None, pattern=None)
        self.rootpath = rootpath

    def get_description(self):
        return 'ROOT'

    def module(self, pattern):
        """Add a `ModuleSchema` to this `RootSchema` and return it."""
        ms = ModuleSchema(self, pattern)
        self.children.append(ms)
        return ms

    def check_self(self, collector):
        self.exist = True


class ModuleSchema(BaseSchema):
    """Define the schema rules of particular module."""

    def __init__(self, parent, pattern):
        if not isinstance(pattern, basestring):
            raise TypeError("Module schema only takes string patterns.")
        super(ModuleSchema, self).__init__(parent, pattern)

    def get_description(self):
        return self._pattern_string()

    def check_self(self, collector):
        """Try to import the given module."""
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
        """Add a `ClassSchema` to this `ModuleSchema` and return it."""
        cs = ClassSchema(self, pattern)
        self.children.append(cs)
        return cs


class ClassSchema(BaseSchema):
    """Define the schema rules of particular class."""

    def __init__(self, parent, pattern):
        super(ClassSchema, self).__init__(parent, pattern)

    def get_description(self):
        return '%s.%s' % (
            self.parent.get_description(), self._pattern_string())

    def check_self(self, collector):
        self.objects = list(self._match_attrs())
        self.exist = not not self.objects

    def method(self, pattern):
        """Add a `MethodSchema` to this `ClassSchema` and return it."""
        ms = MethodSchema(self, pattern)
        self.children.append(ms)
        return ms


class MethodSchema(BaseSchema):
    """Define the schema rules of particular class methods."""

    def __init__(self, parent, pattern):
        super(MethodSchema, self).__init__(parent, pattern)

    def get_description(self):
        return '%s.%s' % (
            self.parent.get_description(), self._pattern_string())

    def check_self(self, collector):
        self.objects = list(self._match_attrs())
        self.exist = not not self.objects
