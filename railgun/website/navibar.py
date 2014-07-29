#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/website/navibar.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Contributors:
#   public@korepwx.com   <public@korepwx.com>
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

from flask import url_for, request

from .context import app


class Navibar(object):
    """Object to manage the main navibar of the site."""

    def __init__(self):
        self.pages = []

    def add_page(self, title, endpoint, *args, **kwargs):
        """
        Add a page link to the navibar.

        title: Lazy translated title of the page.
        endpoint: Flask endpoint of this navibar.
        *args, **kwargs: args and kwargs when get url of this page by url_for.
        """

        self.pages.append((title, endpoint, lambda: (args, kwargs)))

    def get_links(self):
        """
        Format links according to request context.
        Return list of (title, url, is_active).
        """

        def get_url(endpoint, mkargs):
            args, kwargs = mkargs()
            return url_for(endpoint, *args, **kwargs)

        def is_active(endpoint):
            return request.endpoint == endpoint

        return [
            (unicode(title), get_url(endpoint, mkargs), is_active(endpoint))
            for title, endpoint, mkargs in self.pages
        ]

navigates = Navibar()


@app.context_processor
def __inject_navigate_links():
    """Inject navigate links into template context."""

    return dict(navigates=navigates, navibar=navigates.get_links())
