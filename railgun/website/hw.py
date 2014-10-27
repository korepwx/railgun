#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/website/hw.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

"""This module contains the proxies to :class:`~railgun.common.hw.Homework`
and :class:`~railgun.common.hw.HwSet` instances.

What is a proxy?  A proxy is a container to another object.  All the access,
including getting or setting the attributes, calling methods, and any other
operations, will be redirected from the container to the actual object.

Why proxy?  Because we can change the behaviour of a given object without
change its code.  For example, :class:`~railgun.common.hw.Homework` contains
the titles and descriptions for all languages.  However, the visitor only
wants one version.
Rather than accessing the correct resources carefully with an explicit
language identity, we wrap the original objects with a simple proxy
object, and we may just use `hw.title` to replace `hw.info[lang].title`.
"""

import os

from flask import g, url_for
from flask.ext.login import current_user

from railgun.common.hw import HwSet, utc_now
from .context import app
from .i18n import get_best_locale_name


class HwProxy(object):
    """Per-request proxy to :class:`~railgun.common.hw.Homework`.
    The best locale for current user will be detected during :meth:`__init__`
    method.

    :param hw: The original :class:`~railgun.common.hw.Homework` object.
    :type hw: :class:`~railgun.common.hw.Homework`
    """

    def __init__(self, hw):
        self.hw = hw

        # determine the best info to be selected
        locale = get_best_locale_name(hw.get_name_locales())
        self.info = [i for i in hw.info if i.lang == locale][0]

    def __getattr__(self, key):
        return getattr(self.hw, key)

    # the following methods are extensions to common.hw.Homework.
    def is_locked(self):
        """Whether this homework is locked?

        You may put the uuid of locked homework in ``config.LOCKED_HOMEWORKS``.
        If you wish to lock all homework assignments, put a "``*``" in it.
        """
        return self.hw.uuid in app.config['LOCKED_HOMEWORKS'] or \
            '*' in app.config['LOCKED_HOMEWORKS']

    def is_hidden(self):
        """Whether this homework is hidden?

        You may put the uuid of hidden homework in ``config.HIDDEN_HOMEWORKS``.
        If you wish to lock all homework assignments, put a "``*``" in it.
        """
        return self.hw.uuid in app.config['HIDDEN_HOMEWORKS'] or \
            '*' in app.config['HIDDEN_HOMEWORKS']

    def attach_url(self, lang):
        """Get the attachment url for given programming language.
        The url should refer to :func:`~railgun.website.views.hwpack`.

        :param lang: The identity of programming language.
        :type lang: :class:`str`
        :return: The attachment url address.
        """
        return url_for('hwpack', slug=self.slug, lang=lang)

    def attach_size(self, lang):
        """Get the attachment file size for given programming language.
        If the file does not exist, return :data:`None`.

        :param lang: The identity of programming language.
        :type lang: :class:`str`
        :return: The attachment file size or :data:`None`.
        """
        fpath = os.path.join(
            app.config['HOMEWORK_PACK_DIR'],
            '%s/%s.zip' % (self.slug, lang)
        )
        if os.path.isfile(fpath):
            return os.path.getsize(fpath)
        return None


class HwSetProxy(object):
    """Per-request proxy to :class:`~railgun.common.hw.HwSet`.
    You may hide some homework assignments to the visitor, so a proxy to
    :class:`~railgun.common.hw.HwSet` is necessary.

    :param hwset: The original :class:`~railgun.common.hw.HwSet` object.
    :type hwset: :class:`~railgun.common.hw.HwSet`
    """

    def __init__(self, hwset):
        # cache all HwProxy instances
        self.items = [HwProxy(hw) for hw in hwset]

        # build slug-to-hw and uuid-to-hw lookup dictionary
        self.__slug_to_hw = {hw.slug: hw for hw in self.items}
        self.__uuid_to_hw = {hw.uuid: hw for hw in self.items}

    def __iter__(self):
        """Iterate through all :class:`HwProxy` instances.
        :return: Iterable object of :class:`HwProxy` instances.
        """
        if not current_user.is_anonymous() and current_user.is_admin:
            return iter(self.items)
        return (i for i in self.items if not i.is_hidden())

    def get_by_uuid(self, uuid):
        """Get the homework with given uuid.

        :param uuid: The homework uuid.
        :type uuid: :class:`str`
        :return: The requested :class:`HwProxy` or :data:`None` if not found.
        """
        return self.__uuid_to_hw.get(uuid, None)

    def get_by_slug(self, slug):
        """Get the homework with given slug.

        :param slug: The homework slug.
        :type slug: :class:`str`
        :return: The requested :class:`HwProxy` or :data:`None` if not found.
        """
        return self.__slug_to_hw.get(slug, None)


#: The global :class:`~railgun.common.hw.HwSet` instance which is initialized
#: at website startup.
homeworks = HwSet(app.config['HOMEWORK_DIR'])


@app.before_request
def __inject_flask_g(*args, **kwargs):
    g.homeworks = HwSetProxy(homeworks)
    # g.utcnow will be used in templates/homework.html to determine some
    # visual styles
    g.utcnow = utc_now()
