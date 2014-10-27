#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/website/navibar.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

"""Railgun has a site-wide navigation bar.

Navigation bar is a two-level menu.  Each item is related to some
certain page.  When the user is visiting some page, the corresponding
item as well as its parent items should be marked as `active`.

This module provides the utility to track active navibar items and maintain
the navigation bar object for each request.  Each navibar item should be
given a `navibar identity`.

The identity is stored in :token:`g.navibar_identity`.  At the start of
each request, :data:`flask.request.endpoint` will be used as the initial
value of :token:`g.navibar_identity`.  If you wish to change the identity,
you may call :func:`set_navibar_identity` anytime before render the
template.
"""

from flask import request, g, url_for

from .context import app


class NaviItem(object):
    """Store the information of a navibar item.

    Many fields in a :class:`NaviItem` object can be `lazy`, which means
    you could give a :func:`callable` object as the value of some field,
    and the actual value will not be calculated until the navibar is
    being rendered.  For example::

        admin_menu = NaviItem(
            title=lazy_gettext('Admin Page'),
            url=lambda: url_for('admin.index', user=current_user.name),
            identity='admin_menu',
            adminpage=True,
            subitems=lambda: [
                NaviItem(title=itm.title, url=itm.url, identity=itm.id,
                         adminpage=True)
                for itm in Database.LoadAdminPages()
            ])

    The :attr:`title` of this menu bar will be translated, the :attr:`url`
    will be generated according to the visitor's username, and the items of
    :attr:`subitems` will be loaded from database.

    :param title: The title of this navi item.
    :type title: A :class:`str`, a lazy string or a :func:`callable` object.
    :param url: The url of this navi item.
    :type url: A :class:`str` or a :func:`callable` object.
    :param identity: The identity of this navi item. (`static`)
    :type identity: :class:`str`
    :param adminpage: Whether this navibar item links to an admin page?
        (`static`)
    :type adminpage: :class:`bool`
    :param subitems: Lists of subitems.
    :type subitems: :class:`list` or a :func:`callable` object.
    """

    def __init__(self, title, url, identity, adminpage=None, subitems=None):
        # information of this navi item
        self.__title = title
        self.__url = url

        #: The identity of this navi item. (`static`)
        self.identity = identity

        #: Whether this navibar item links to an admin page? (`static`)
        self.adminpage = adminpage

        # list of sub navi items
        self.__subitems = subitems

    @property
    def title(self):
        """Perform the `lazy` calculation and get the title."""
        if callable(self.__title):
            return self.__title()
        return unicode(self.__title)

    @property
    def url(self):
        """Perform the `lazy` calculation and get the url."""
        if callable(self.__url):
            return self.__url()
        return self.__url

    @property
    def subitems(self):
        """Perform the `lazy` calculation and get the subitems."""
        if callable(self.__subitems):
            return self.__subitems()
        return self.__subitems or []

    @property
    def is_active(self):
        """Whether this navibar item is active?

        This method only compares the :attr:`identity` of itself with
        :token:`g.navibar_identity`.  If you wish to check the activeness
        of all subitems, you may put the :class:`NaviItem` into a
        :class:`NaviItemProxy`.
        """
        return g.navibar_identity == self.identity

    @property
    def has_child(self):
        """Whether this navibar item has subitems?"""
        return not not self.subitems

    @staticmethod
    def make_view(title, endpoint, *args, **kwargs):
        """A shortcut to make a :class:`NaviItem` linking to a standard
        Flask view.  Equal to the following statement:

        .. code-block:: python

            NaviItem(
                title=title,
                url=lambda: url_for(endpoint, *args, **kwargs),
                identity=endpoint
            )

        :param title: The title of new :class:`NaviItem`
        :param endpoint: The endpoint of target view.
        :type endpoint: :class:`str`
        :param args: The unnamed arguments to :func:`flask.url_for` when
            generating the `url`.
        :param kwargs: The named arguments to :func:`flask.url_for` when
            generating the `url`.
        """
        return NaviItem(title, lambda: url_for(endpoint, *args, **kwargs),
                        endpoint)


class NaviItemProxy(object):
    """Per-request proxy to a :class:`NaviItem` instance.

    Once this proxy is created, all the `lazy` fields of :class:`NaviItem`
    object will be calculated and cached, including all its subitems.
    Moreover, if a subitem is active, then the parent is marked `active`
    as well.

    :param navi: The navibar item.
    :type navi: :class:`NaviItem`
    """

    def __init__(self, navi):
        # build the proxy tree
        self.navi = navi
        self.title = navi.title
        self.url = navi.url
        if not self.url:
            self.url = '#'
        self.is_active = navi.is_active
        self.subitems = [NaviItemProxy(i) for i in self.navi.subitems]

        # build cache of recursive is_active
        if not self.is_active:
            for i in navi.subitems:
                if i.is_active:
                    self.is_active = True
                    break

    def __getattr__(self, name):
        return getattr(self.navi, name)


class Navibar(object):
    """Manage all the :class:`NaviItem` instances in a navigation bar."""

    def __init__(self):
        #: List of the first-level navibar items.
        self.items = []

    def add(self, item):
        """Add a first-level navibar item.

        :param item: A navibar item.
        :type item: :class:`NaviItem`
        """
        self.items.append(item)

    def add_view(self, title, endpoint, *args, **kwargs):
        """Shortcut to add a view to this navibar.

        :param title: The title of this navibar.
        :param endpoint: The endpoint of target view.
        :type endpoint: :class:`str`
        :param args: The unnamed arguments to :func:`flask.url_for` when
            generating the `url`.
        :param kwargs: The named arguments to :func:`flask.url_for` when
            generating the `url`.
        """
        self.items.append(
            NaviItem(title, lambda: url_for(endpoint, *args, **kwargs),
                     endpoint)
        )

    def get_proxies(self):
        """Contruct all the :class:`NaviItemProxy` instances.

        :return: :class:`list` of :class:`NaviItemProxy`.
        """
        return [NaviItemProxy(i) for i in self.items]


class NavibarProxy(object):
    """A proxy to :class:`NavibarProxy`, that delays the call to
    :meth:`Navibar.get_proxies` until the navigation bar is actually
    accessed.
    The :class:`NaviItemProxy` instances are then cached in this class.

    Do not access :attr:`items` explicitly!  The only way to use
    :class:`NavibarProxy` is to iterate over it.  For example::

        for item in navibar:
            print item.title
    """

    def __init__(self, navibar):
        self.__navibar = navibar
        #: The cached :class:`NaviItemProxy` instances.
        self.items = None

    def __iter__(self):
        if self.items is None:
            self.items = self.__navibar.get_proxies()
        return iter(self.items)

#: The global :class:`Navibar` registry.
navigates = Navibar()


@app.context_processor
def __inject_navigate_links():
    """inject navigate links into template context."""
    return dict(navibar=NavibarProxy(navigates))


def set_navibar_identity(identity):
    """Set the identity of nagivation item for current request.

    :param identity: The navibar item identity.
    :type identity: :class:`str`
    """
    g.navibar_identity = identity


@app.before_request
def __mark_navibar_identity(*args, **kwargs):
    """set default value of g.navibar_identity to '[request.endpoint]'."""
    set_navibar_identity(request.endpoint)
