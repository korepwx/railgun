#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/website/navibar.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Contributors:
#   public@korepwx.com   <public@korepwx.com>
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

from flask import request, g, url_for

from .context import app


class NaviItem(object):
    """Basis of navibar item."""

    def __init__(self, title, url, identity, subitems=None):
        """construct a new `NaviItem` instance.

        `title`: title of this navi item, may be lazy string or callable.
        `url`: url of this navi item, may be callable object.
        `identity`: identity of this navi item, may be callable object.

        this object contains too many dynamic properties. so `NaviItemProxy`
        should be used to cache these properties once the request context is
        made."""

        # information of this navi item
        self.__title = title
        self.__url = url
        self.identity = identity

        # list of sub navi items
        self.__subitems = subitems

    @property
    def title(self):
        if (callable(self.__title)):
            return self.__title()
        return unicode(self.__title)

    @property
    def url(self):
        if (callable(self.__url)):
            return self.__url()
        return self.__url

    @property
    def subitems(self):
        if (callable(self.__subitems)):
            return self.__subitems()
        return self.__subitems or []

    @property
    def is_active(self):
        """test whether this navi item is active."""
        return g.navibar_identity == self.identity

    @property
    def has_child(self):
        """test whether this navi item has children."""
        return not not self.subitems


class NaviItemProxy(object):
    """Proxy to `NaviItem` instances, cache all properties of `NaviItem`.
    this proxy is very important in that all properties of `NaviItem` can
    be callable object."""

    def __init__(self, navi):
        # build the proxy tree
        self.navi = navi
        self.title = navi.title
        self.url = navi.url
        if (not self.url):
            self.url = '#'
        self.is_active = navi.is_active
        self.subitems = [NaviItemProxy(i) for i in self.navi.subitems]

        # build cache of recursive is_active
        if (not self.is_active):
            for i in navi.subitems:
                if (i.is_active):
                    self.is_active = True
                    break

    def __getattr__(self, name):
        """proxy attribute to navi item."""
        return getattr(self.navi, name)


class Navibar(object):
    """Object to manage the main navibar of the site."""

    def __init__(self):
        self.items = []

    def add(self, item):
        """add a navi item into this navi bar."""
        self.items.append(item)

    def add_view(self, title, endpoint, *args, **kwargs):
        """add view `endpoint` into this navi bar."""
        self.items.append(
            NaviItem(title, lambda: url_for(endpoint, *args, **kwargs),
                     endpoint)
        )

    def get_proxies(self):
        """get `NaviItemProxy` instances of items."""
        return [NaviItemProxy(i) for i in self.items]


class NavibarProxy(object):
    """callable properties of `NaviItem` and `is_active` can be affected
    by request context. so build `NaviItemProxy` instances until they are
    used."""

    def __init__(self, navibar):
        self.__navibar = navibar
        self.items = None

    def __iter__(self):
        if (self.items is None):
            self.items = self.__navibar.get_proxies()
        return iter(self.items)

navigates = Navibar()


@app.context_processor
def __inject_navigate_links():
    """inject navigate links into template context."""
    return dict(navigates=navigates, navibar=NavibarProxy(navigates))


def set_navibar_identity(identity):
    """manually set the identity of navibar for current request."""
    g.navibar_identity = identity


@app.before_request
def __mark_navibar_identity(*args, **kwargs):
    """set default value of g.navibar_identity to '[request.endpoint]'."""
    set_navibar_identity(request.endpoint)
