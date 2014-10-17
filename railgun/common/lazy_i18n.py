#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/common/lazy_i18n.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

"""
this module contains a serializable lazy gettext utility.
"""

from flask.ext.babel import gettext as _babel_gettext


class GetTextString(object):
    """keyword formattable and serializable lazy gettext string"""

    def __init__(self, __s, **kwargs):
        self.text = __s
        self.kwargs = kwargs

    def render(self):
        """render lazy string and get translated text"""

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


def lazy_gettext(__s, **kwargs):
    return GetTextString(__s, **kwargs)


def lazystr_to_plain(s):
    """Convert string or unicode or GetTextString to plain object."""
    if s is None or isinstance(s, str) or isinstance(s, unicode):
        return s
    if isinstance(s, GetTextString):
        return {'text': s.text, 'kwargs': s.kwargs}
    raise TypeError('"%s" is not a string object.' % s)


def plain_to_lazystr(s):
    """Convert plain object to unicode or GetTextString."""
    if s is None or isinstance(s, str) or isinstance(s, unicode):
        return s
    return GetTextString(s['text'], **s['kwargs'])
