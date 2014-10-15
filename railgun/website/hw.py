#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/website/hw.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import os

from flask import g, url_for
from flask.ext.login import current_user

from railgun.common.hw import HwSet, utc_now
from .context import app
from .i18n import get_best_locale_name


class HwProxy(object):
    """per-request proxy to a given `Homework` instance. access to obj.info
    will automatically select a suitable locale."""

    def __init__(self, hw):
        self.hw = hw

        # determine the best info to be selected
        locale = get_best_locale_name(hw.get_name_locales())
        self.info = [i for i in hw.info if i.lang == locale][0]

    def __getattr__(self, key):
        return getattr(self.hw, key)

    # the following methods are extensions to common.hw.Homework.
    def is_locked(self):
        """Whether this homework is locked?"""
        return self.hw.uuid in app.config['LOCKED_HOMEWORKS'] or \
            '*' in app.config['LOCKED_HOMEWORKS']

    def is_hidden(self):
        """Whether this homework is hidden?"""
        return self.hw.uuid in app.config['HIDDEN_HOMEWORKS'] or \
            '*' in app.config['HIDDEN_HOMEWORKS']

    def attach_url(self, lang):
        """get the attachment url for given `lang`"""
        return url_for('hwpack', slug=self.slug, lang=lang)

    def attach_size(self, lang):
        """get the size of attachment for given `lang`"""
        fpath = os.path.join(
            app.config['HOMEWORK_PACK_DIR'],
            '%s/%s.zip' % (self.slug, lang)
        )
        if os.path.isfile(fpath):
            return os.path.getsize(fpath)
        return None


class HwSetProxy(object):
    """per-request proxy to `HwSet`, whose iterable items are all `HwProxy`."""

    def __init__(self, hwset):
        # cache all HwProxy instances
        self.items = [HwProxy(hw) for hw in hwset]

        # build slug-to-hw and uuid-to-hw lookup dictionary
        self.__slug_to_hw = {hw.slug: hw for hw in self.items}
        self.__uuid_to_hw = {hw.uuid: hw for hw in self.items}

    def __iter__(self):
        """get iterable object through all HwProxy instances."""
        if current_user.is_admin:
            return iter(self.items)
        return (i for i in self.items if not i.is_hidden())

    def get_by_uuid(self, uuid):
        """get HwProxy by uuid."""
        return self.__uuid_to_hw.get(uuid, None)

    def get_by_slug(self, slug):
        """get HwProxy by slug."""
        return self.__slug_to_hw.get(slug, None)


# global homework set instance
homeworks = HwSet(app.config['HOMEWORK_DIR'])


# inject homework proxies into `g` object
@app.before_request
def __inject_flask_g(*args, **kwargs):
    g.homeworks = HwSetProxy(homeworks)
    # g.utcnow will be used in templates/homework.html to determine some
    # visual styles
    g.utcnow = utc_now()
