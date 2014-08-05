#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/website/hw.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Contributors:
#   public@korepwx.com   <public@korepwx.com>
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import os

from flask import request, g

from railgun.common.hw import Homework
from .context import app


class HwSet(object):
    """Collection of all homeworks."""

    def __init__(self, hwdir):

        # `hwdir` is the root path of homework
        self.hwdir = hwdir
        # `items` store all discovered homeworks in order of `slug`.
        self.items = None

        self.reload()

    def reload(self):
        """reload the homeworks from directory."""

        # load all homeworks
        self.items = []
        for fn in os.listdir(self.hwdir):
            fp = os.path.join(self.hwdir, fn)
            if (os.path.isdir(fp) and
                    os.path.isfile(os.path.join(fp, 'hw.xml'))):
                self.items.append(Homework.load(fp))
        self.items = sorted(self.items, cmp=lambda a, b: cmp(a.slug, b.slug))

    def __iter__(self):
        """get iterable object through all homeworks."""
        return iter(self.items)


class HwProxy(object):
    """per-request proxy to a given `Homework` instance. access to obj.info
    will automatically select a suitable locale."""

    def __init__(self, hw):
        self.hw = hw

        # determine the best info to be selected
        locale = request.accept_languages.best_match(hw.get_name_locales())
        if (not locale):
            locale = app.config['BABEL_DEFAULT_LOCALE']
        self.info = [i for i in hw.info if i.lang == locale]
        if (not self.info):
            self.info = hw.info[-1]
        else:
            self.info = self.info[0]

    def __getattr__(self, key):
        return getattr(self.hw, key)


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
        return iter(self.items)

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
