#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/common/url.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import re


class UrlMatcher(object):
    """Match and replace URL in given string."""

    def __init__(self, schemas=['http', 'https', 'ftp']):
        schema_pattern = '|'.join(schemas)
        self.pattern = (r"(%s)://[A-Za-z0-9-_.~!\*';:@&=+$,/?#]*" %
                        schema_pattern)
        self.regex = re.compile(self.pattern)

    def findall(self, payload):
        """List all URLs in `payload`."""
        for m in self.regex.finditer(payload):
            return m.group()

    def replace(self, payload, callback):
        """Replace the matching urls by callback(old) -> new."""
        cb = lambda m: callback(m.group())
        return self.regex.sub(cb, payload)


def reform_path(path):
    path = path.replace('\\', '/')
    lead_slash = path.startswith('/')
    ret = []

    for p in path.split('/'):
        # skip continous slashes, or single '.'
        if (p == '.' or not p):
            continue
        # remove parent dir if p is '..'
        if (p == '..'):
            if (not ret):
                raise ValueError('.. out of root')
            ret.pop()
        # otherwise add the simple part into ret
        else:
            ret.append(p)

    ret = '/'.join(ret)
    if (lead_slash):
        ret = '/' + ret
    return ret
