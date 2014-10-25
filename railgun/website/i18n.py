#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/website/i18n.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import os

from flask import request
from flask.ext.babel import Babel, get_locale, Locale
from flask.ext.login import current_user

from .context import app

#: A :class:`flask.ext.babel.Babel` object.  It extends the
#: :data:`~railgun.website.context.app` to support translations for
#: each request.
babel = Babel(app)


def list_locales():
    """Get a list of available :class:`babel.core.Locale` objects.

    Whatever translations the system provides, "en" should always
    appear in the list.  The returned list should be sorted in the order
    of display names, which may be vary in different languages.

    :return: :class:`list` of :class:`babel.core.Locale` objects.
    """
    ret = [Locale('en')] + babel.list_translations()
    return sorted(ret, cmp=lambda a, b: cmp(a.display_name, b.display_name))


def get_best_locale_name(locale_names):
    """Select the best matching locale from `locale_names` according to
    current request.

    The locales are evaluated according to the language, script and territory.
    If no best choice is found, fallback to ``config.DEFAULT_LOCALE``.
    Moreover, if even ``config.DEFAULT_LOCALE`` does not appear in
    `locale_names`, choose the last item in `locale_names`.

    Usage:

    .. code-block:: python

        # If current user prefers zh-CN, or zh-TW.
        >>> get_best_locale_name(['zh-cn', 'en'])
        'zh-cn'

        # If current user prefers en-US.
        >>> get_best_locale_name(['zh-cn', 'en'])
        'en'

        # If current user prefers ja-JP, and default locale is zh-CN.
        >>> get_best_locale_name(['zh-cn', 'en'])
        'zh-cn'

        # If current user prefers ja-JP, and default locale is zh-CN.
        >>> get_best_locale_name(['fr', 'en'])
        'en'

    :param locale_names: List of alternative locale names.
    :type locale_names: :class:`list`

    :return: The best matching or fallback locale name.
    :rtype: :class:`str`
    """

    top_score = 0
    top_name = None
    req_locale = get_locale()

    for name in locale_names:
        l = Locale.parse(name.replace('-', '_'))
        # If locale object is the same, return True at once
        if l == req_locale:
            return name
        # If language not match, give up this locale
        if l.language != req_locale.language:
            continue
        # Exam the matched score
        score = 0
        # script match, give 5
        if l.script == req_locale.script:
            score += 5
        # territory match, give 3
        if l.territory == req_locale.territory:
            score += 3
        # variant match, give 3
        # TODO: check these score weights
        if l.variant == req_locale.variant:
            score += 3
        # Update top_name if > top_score
        if score > top_score:
            top_name = name
            top_score = score

    # Fallback to default locale or last locale
    if top_name is None:
        if app.config['DEFAULT_LOCALE'] in locale_names:
            top_name = app.config['DEFAULT_LOCALE']
        else:
            top_name = locale_names[-1]
    return top_name


# Flask-Babel only accepts zh_Hans_CN to construct locale object for zh_CN,
# However the browser reports zh_CN.  So load the alias names to locales
# here.
def __load_aliases():
    ret = {}
    aliases_path = os.path.join(app.config['TRANSLATION_DIR'], 'aliases.txt')
    try:
        f = open(aliases_path, 'rb')
        for l in f:
            arr = l.split('=')
            if len(arr) < 2:
                continue
            k, v = arr[0].strip(), arr[1].strip()
            if k and v:
                ret[k] = v
        f.close()
    except Exception:
        pass
    return ret

locale_aliases = __load_aliases()


# Construct the best match list for locale selector according to the
# locale files which babel has loaded, and the alias name table.
def __make_best_match():
    trans = babel.list_translations()
    ret = set(['en'])
    for t in trans:
        tname = str(t)
        ret.add(tname)
    for t in locale_aliases.iterkeys():
        ret.add(t)
    return list(ret)

best_matches = __make_best_match()


@babel.localeselector
def __select_request_locale():
    """Detect the request locale according to the user setting and browser
    request headers.
    """
    if current_user.is_authenticated():
        return current_user.locale
    best_match = request.accept_languages.best_match(best_matches)
    return locale_aliases.get(best_match, best_match)


@babel.timezoneselector
def __select_request_timezone():
    """Detect the request timezone according to the user settings.

    Flask-Babel should be initialized to format datetime in the user's
    timezone after this method is called, so the timezone name should be
    compatible with :mod:`flask.ext.babel`.
    """
    # TODO: set the correct time zone according to user configuration.
    #       if possible, also guess by client ip.
    if current_user.is_authenticated():
        return current_user.timezone
    return None


@app.context_processor
def __inject_template_context():
    """Add `pagelng` to Jinja2 template context.

    `pagelng` is the locale name which can be used to describe the language of
    html elements.  For example::

        <html lang={{ pagelang }}>
            ...
        </html>
    """

    pagelng = get_locale()
    if pagelng.territory:
        pagelng = '%s-%s' % (pagelng.language, pagelng.territory)
    else:
        pagelng = pagelng.language
    return dict(pagelng=pagelng)
