#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/maintain/base.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import logging
from logging import StreamHandler
from cStringIO import StringIO


class Task(object):
    """The base class for all maintain tasks."""

    def __init__(self, logstream=None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)

        # Setup log stream
        if not logstream:
            logstream = StringIO()
        self._stream = logstream
        self._handler = StreamHandler(logstream)
        self._handler.setLevel(logging.INFO)
        self.logger.addHandler(self._handler)

    def logflush(self):
        """Flush the output cache of logger."""
        self._handler.flush()
        self._stream.flush()

    def logstream(self):
        """Get the log stream."""
        return self._stream

    def execute(self, *args, **kwargs):
        """Execute the maintain task."""
        raise NotImplementedError()


class TaskSet(object):
    """Set of constructors of maintain tasks."""

    def __init__(self):
        self.tasks = {}

    def add(self, name, taskmaker):
        """Add a task constructor into set."""
        if name in self.tasks:
            raise KeyError('Task %(name)s already exists!' % name)
        self.tasks[name] = taskmaker

    def create(self, __name, *args, **kwargs):
        """Create a task with given `__name` with (*args, **kwargs)."""
        return self.tasks[__name](*args, **kwargs)

    def __iter__(self):
        return self.tasks.iteritems()

tasks = TaskSet()
