#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: tools/mktz.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Contributors:
#   public@korepwx.com   <public@korepwx.com>
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import os
import sys
import json
sys.path.insert(0, os.path.split(os.path.dirname(__file__))[0])

from pytz import common_timezones, timezone
from babel.dates import get_timezone_name
from railgun.website.i18n import list_locales


# Generate timezone list for given locale
def mktz(tzlist, loc):
    return [(tz, get_timezone_name(timezone(tz), locale=loc)) for tz in tzlist]

# Cache common timezone list
tzlist = list(common_timezones)

# Make each files
for l in list_locales():
    tz = mktz(tzlist, l)
    with open('railgun/website/static/tz/%s.json' % str(l), 'wb') as f:
        f.write(json.dumps(tz))
