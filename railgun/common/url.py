#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/common/url.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import re


class UrlMatcher(object):
    """A useful class to find all the urls from given text, and replace them
    with a callback function.

    For example, if you want to replace all ``file:///`` urls to ``http://``
    ones, where all the files are located under ``/var/www/share/``, and all
    the http urls should start with ``http://localhost/files/``, then we
    may write::

        def ReplaceUrl(url):
            if url.startswith('file:///var/www/share/'):
                return 'http://localhost/files/%s' % url[22:]
            return url

        matcher = UrlMatcher(schemas=['file'])
        payload = "Here is the movie: " \\
            "file:///var/www/share/favourites/Harry-Potter.mov"
        print matcher.replace(payload, ReplaceUrl)

    Note that we only consider the following characters as components of
    urls::

        A-Z, a-z, 0-9, and any one of "-_.~!*';:@&=+$,/?#"

    :param schemas: Interested url schemas.
    :type schemas: :class:`list`
    """

    def __init__(self, schemas=['http', 'https', 'ftp']):
        schema_pattern = '|'.join(schemas)
        self.pattern = (r"(%s)://[A-Za-z0-9-_.~!\*';:@&=+$,/?#]*" %
                        schema_pattern)
        self.regex = re.compile(self.pattern)

    def findall(self, payload):
        """Get all matching urls from given `payload`.

        :param payload: Text that may contain urls.
        :type payload: :class:`str`
        :return: Iterable urls.
        """
        for m in self.regex.finditer(payload):
            yield m.group()

    def replace(self, payload, callback):
        """Replace all matching urls in given `payload` with `callback`.

        :param payload: Text that may contain urls.
        :type payload: :class:`str`
        :param callback: Function to generate new urls from old ones.
        :type callback: method(:class:`str`) -> :class:`str`

        :return: Replaced text.
        """
        cb = lambda m: callback(m.group())
        return self.regex.sub(cb, payload)


def reform_path(path):
    """Reformat the given path to Unix style.

    The given path will be modified according to following rules:

    *   "/" is the delimieter among different components of the path.
    *   "\\\\" will be treated as "/".
    *   Continous "/" will be considered as one.
    *   Component "." will be removed from the path.
    *   Component ".." will consume one parent in the path.
    *   A leading "/" will be reserved, while a trailing "/" will be removed.
    *   Other components will be output without translation.

    There's some special cases:

    *   "/" will result in "/", since the only slash is both a leading and
        a trailing one.
    *   Empty string will remain empty.

    Examples::

        >>> reform_path('1\\\\2')
        '1/2'
        >>> reform_path('////1////2')
        '/1/2'
        >>> reform_path('/1/2/3/../4/../..')
        '/1'
        >>> reform_path('/1/..')
        '/'
        >>> reform_path('../')
        Traceback (most recent call last):
          File "a.py", line 63, in <module>
            reform_path('../')
          ...
        ValueError: .. out of root

    :param path: Original path string.
    :type path: :class:`str`
    :return: The translated new path.

    :raises: :class:`ValueError` if ".." could not find any parent to consume.
    """

    path = path.replace('\\', '/')
    lead_slash = path.startswith('/')
    ret = []

    for p in path.split('/'):
        # skip continous slashes, or single '.'
        if p == '.' or not p:
            continue
        # remove parent dir if p is '..'
        if p == '..':
            if not ret:
                raise ValueError('.. out of root')
            ret.pop()
        # otherwise add the simple part into ret
        else:
            ret.append(p)

    ret = '/'.join(ret)
    if lead_slash:
        ret = '/' + ret
    return ret
