#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/website/manual.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

"""This module formats markdown manuals into html pages.

The manual pages support translations.  They are written in markdown and
stored under ``railgun/website/manual``.
Each directory is one single manual page, where each locale holds the
translated contents of this manual page in "``[lang].md``".
"""

import os

from flask import render_template
from markdown import markdown
from jinja2 import FileSystemLoader, Environment

from railgun.common.url import reform_path, UrlMatcher
from .i18n import get_best_locale_name
from .context import app
from .utility import format_size


class ManualPage(object):

    # The environment shared by all manual page instances
    template_env = Environment(
        loader=FileSystemLoader(
            os.path.join(os.path.dirname(__file__), 'manual')
        )
    )
    template_env.filters['sizeformat'] = format_size

    # Main body of the ManualPage
    def __init__(self, name):
        self.name = name
        self.root = os.path.join(os.path.dirname(__file__), 'manual/%s' % name)
        if os.path.isdir(self.root):
            files = os.listdir(self.root)
            self.locales = [f[:-3] for f in files if f.endswith('.md')]
        else:
            self.locales = []
        self._title = {l: self._make_title(l) for l in self.locales}
        self._formatted = {
            l: self._format_webpage(self._make_markdown(l))
            for l in self.locales
        }

    def _make_title(self, locale):
        """Load the title of this manual page."""
        with open(os.path.join(self.root, '%s.md' % locale), 'rb') as f:
            for l in f:
                if l.startswith('#'):
                    return l[1:].strip().decode('utf-8')

    def _make_template_kwargs(self):
        """Make the dictionary passed to template render."""
        return dict(
            max_upload=app.config['MAX_SUBMISSION_SIZE'],
            max_archive_file=app.config['MAX_SUBMISSION_FILE_COUNT'],
            max_pending=app.config['MAX_USER_PENDING_PER_HW'],
        )

    # To expose static resources in homework desc directory, we need to
    # convert all "hw://<path>" urls to hwstatic view urls.
    def _translate_url(self, u):
        # Get rid of 'hw://' and leading '/'
        u = reform_path(u[5:])
        if u.startswith('/'):
            u = u[1:]
        # translate to hwstatic file
        filename = '%s/%s' % (self.name, u)
        # NOTE: here I hardcoded the url for hwstatic!
        ret = '/static/img/%s' % filename
        # we also need to prepend website base url
        return app.config['WEBSITE_BASEURL'] + ret

    def _make_markdown(self, locale, webpage=True):
        """Render manual page in given `locale` into markdown source."""
        path = '%s/%s.md' % (self.name, locale)
        tpl = ManualPage.template_env.get_template(path)
        kwargs = self._make_template_kwargs()
        mkd = tpl.render(webpage=webpage, **kwargs)
        return UrlMatcher(['rc']).replace(mkd.strip(), self._translate_url)

    def _format_webpage(self, mkd):
        """Format markdown source into html."""
        return markdown(
            text=mkd,
            output_format='xhtml1',
            extensions=[
                'extra',
                'tables',
                'codehilite',
                'nl2br',
                'toc',
                'fenced_code',
            ]
        )

    def get(self):
        """Get the most suitable manual (title, content) for current locale."""
        best_locale = get_best_locale_name(self.locales)
        return self._title[best_locale], self._formatted[best_locale]

    def markdown(self):
        """Make pure markdown source targeted for general usage."""
        best_locale = get_best_locale_name(self.locales)
        return self._make_markdown(locale=best_locale, webpage=False)


def translated_page(name):
    """Render the requested manual page to visitor.
    The best locale for current user will be detected automatically.

    :template: manual.html
    :param name: The manual page name.
    :type name: :class:`str`
    """
    title, content = manual_pages[name].get()
    return render_template('manual.html', title=title, content=content)


def translated_page_source(name):
    """Render the source of requested manual page to visitor.
    The best locale for current user will be detected automatically.

    :param name: The manual page name.
    :type name: :class:`str`
    """
    return manual_pages[name].markdown(), 200, \
        {'Content-Type': 'text/x-markdown; charset=utf-8'}

#: Cache all the manual page instances in memory, so that the markdown
#: source code will only be formatted once.
manual_pages = {
    k: ManualPage(k)
    for k in os.listdir(os.path.join(os.path.dirname(__file__), 'manual'))
}
