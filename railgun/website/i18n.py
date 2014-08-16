#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/website/i18n.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Contributors:
#   public@korepwx.com   <public@korepwx.com>
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import os

from flask import request
from flask.ext.babel import Babel, get_locale
from flask.ext.login import current_user

from .context import app

# We must import credential here, so that all hooks should be initialized by
# flask.login before we start i18n hooks
# from . import credential

# Initialize the Babel translation system
babel = Babel(app)


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
            if (len(arr) < 2):
                continue
            k, v = arr[0].strip(), arr[1].strip()
            if (k and v):
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
    """Select the prefered language according to Accept-Language."""
    if (current_user.is_authenticated()):
        return current_user.locale
    best_match = request.accept_languages.best_match(best_matches)
    return locale_aliases.get(best_match, best_match)


@babel.timezoneselector
def __select_request_timezone():
    # TODO: set the correct time zone according to user configuration.
    #       if possible, also guess by client ip.
    if (current_user.is_authenticated()):
        return current_user.timezone
    return None


@app.context_processor
def __inject_template_context():
    """Add `pagelng` variable to template context.  `pagelng` should be
    compatible with HTML lang attribute."""

    pagelng = get_locale()
    if (pagelng.territory):
        pagelng = '%s-%s' % (pagelng.language, pagelng.territory)
    else:
        pagelng = pagelng.language
    return dict(pagelng=pagelng)
