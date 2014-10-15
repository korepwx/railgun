#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/common/pyutil.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import sys


def find_object(name):
    """Find object according to `name`.

    This method will try to import all the intermediate modules to find the
    requested object.

    Examples:

        >>> find_object('os')
        <module 'os' from '?'>

        >>> find_object('os.path')
        <module 'posixpath' from '?'>

        >>> find_object('os.remove')
        <function posix.remove>

        >>> find_object('os.path.split')
        <function posixpath.split>

        >>> find_object('os.path.split.__name__')
        'split'

    :param name: The name of the object, should contain full path from the
        global scope.
    :type name: :class:`str`

    :return: The object instance.
    :raises: :class:`ImportError` if object with `name` cannot be found.
    """

    # If name is empty, fail fast
    if not name:
        raise ImportError('Object name should not be empty.')

    # Try to import the closest module according to `name`.
    parts = name.split('.')

    # Try to treat some prefix of the name as module
    obj = None
    for i in xrange(len(parts), 0, -1):
        modname = '.'.join(parts[:i])
        try:
            obj = __import__(modname)
            obj = sys.modules[modname]
            parts = parts[i:]
            break
        except ImportError:
            # We can ignore the exception unless it is ImportError.
            # Otherwise there should be something wrong when importing
            # existing module.
            pass

    # If we failed to import the container module, then we raise an
    # ImportError
    if obj is None:
        raise ImportError("Couldn't find any module along `%s`." % name)

    # Try to get the object along attribute path
    for name in parts:
        if not hasattr(obj, name):
            raise ImportError(
                "Object '%s' does not have attribute '%s'." % (obj, name))
        obj = getattr(obj, name)

    # Now we've got the object
    return obj
