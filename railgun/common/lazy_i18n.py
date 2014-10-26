#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/common/lazy_i18n.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

"""Utilities for serializable lazy translated strings.

As mentioned in :ref:`i18n_everywhere`, we want our Railgun system to
support translations, even for the strings already stored in databases.

We know that a simple solution to the translations in a website system
is to use the :mod:`gettext` package.  Suppose we've created a message
category including the translation from "My name is %(name)s." to
"我的姓名是 %(name)s.", then we may write::

    from gettext import gettext

    >>> type(gettext('My name is %(name)s.'))
    str

    >>> print gettext('My name is %(name)s.') % {'name': 'Alice'}
    '我的姓名是 Alice.'

The main functionality of `gettext` is to lookup a translation table,
find the suitable translated text for input string, and then return it.
However, :mod:`gettext` can only be configured to use a global locale.

To support multi-users in a website environment, we may use the gettext
and lazy_gettext method from :mod:`flask.ext.babel`::

    from flask.ext.babel import gettext, lazy_gettext

    >>> gettext('My name is %(name)s.', name='Alice')
    '我的姓名是 Alice.'

    >>> type(gettext('My name is %(name)s.', name='Alice'))
    :class:`str`

    >>> type(lazy_gettext('My name is %(name)s.', name='Alice'))
    :class:`speaklater._LazyString`

The `gettext` from :mod:`flask.ext.babel` will use the locale settings
from current request, but it will translate the string at once, so you may
not create a global translated text with `gettext`.

On the other side, the `lazy_gettext` will store all the arguments
and create a :class:`speaklater._LazyString` instance, and will only
do the translation until it is being output.  So you can make a global
translated text with `lazy_gettext`.

However, we still have problems. :class:`speaklater._LazyString` could not
be serialized into a JSON message, nor could it be stored into database.

This is why I create my own :class:`GetTextString` and :func:`lazy_gettext`
method.  However, these utilities do have some limitations:

*   The arguments passed to :func:`lazy_gettext` must be "plain"
    objects, including :class:`bool`, :class:`str`, :class:`unicode` and
    the numeric types.
*   `ngettext`, `dgettext` and `ndgettext` are not supported.
"""

from flask.ext.babel import gettext as _babel_gettext


class GetTextString(object):
    """Make a serializable lazy gettext object.

    :param __s: The text to be translated.
    :type __s: :class:`basestring`
    :param kwargs: Keyword arguments to be formatted.
    :type kwargs: :class:`dict`
    """

    def __init__(self, __s, **kwargs):
        self.text = __s
        self.kwargs = kwargs

    def render(self):
        """Render the lazy gettext object into :class:`unicode` string."""

        # There's a very strange behaviour: gettext('') will return the version
        # string of babel. Get rid of it!
        if not self.text:
            return ''
        return _babel_gettext(self.text, **self.kwargs)

    def __unicode__(self):
        return unicode(self.render())

    def __str__(self):
        return str(self.render())

    def __repr__(self):
        return '<GetText(%s)>' % self.render()


lazy_gettext = GetTextString


def lazystr_to_plain(s):
    """Convert a :class:`basestring` or a :class:`GetTextString` object to
    a JSON serializable plain object.
    You may refer to :ref:`json_GetTextString` for more details about the
    JSON format.

    :param s: The string object to be converted.
    :return: A plain object that is composed only with :class:`dict`,
            :class:`list`, :class:`str`, :class:`bool` and numeric types.
    :raises: :class:`TypeError` if `s` is not converible.
    """
    if s is None or isinstance(s, str) or isinstance(s, unicode):
        return s
    if isinstance(s, GetTextString):
        return {'text': s.text, 'kwargs': s.kwargs}
    raise TypeError('"%s" is not a string object.' % s)


def plain_to_lazystr(s):
    """Convert a plain object to :class:`basestring` or :class:`GetTextString`.
    You may refer to :ref:`json_GetTextString` for more details about the
    JSON format.

    :param s: The plain object.
    :return: A :class:`basestring` or a :class:`GetTextString` object.

    :raises: :class:`KeyError` if `s` is not converible.
    """
    if s is None or isinstance(s, str) or isinstance(s, unicode):
        return s
    return GetTextString(s['text'], **s['kwargs'])
