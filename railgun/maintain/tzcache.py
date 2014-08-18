#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/maintain/tzcache.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import os
import json

from pytz import common_timezones, timezone
from babel.dates import get_timezone_name

import config
from .base import Task, tasks
from railgun.website.i18n import list_locales


class TzCacheTask(Task):
    """Task to generate timezone cache."""

    def mktz(self, tzlist, loc):
        return [(tz, get_timezone_name(timezone(tz), locale=loc))
                for tz in tzlist]

    def make_cache(self):
        self.logger.info('start building tzcache ...')

        # Cache common timezone list
        tzlist = list(common_timezones)

        # Make each files
        for l in list_locales():
            tz = self.mktz(tzlist, l)
            tzfile = os.path.join(
                config.RAILGUN_ROOT,
                'railgun/website/static/tz/%s.json' % str(l)
            )
            with open(tzfile, 'wb') as f:
                f.write(json.dumps(tz))
            self.logger.info('tzcache "%s": ok.' % tzfile)

    def execute(self):
        try:
            self.make_cache()
        except Exception:
            self.logger.exception('Build timezone cache failed.')

tasks.add('tzcache', TzCacheTask)
