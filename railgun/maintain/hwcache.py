#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/maintain/hwcache.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import os
import shutil

import config
from railgun.common.hw import Homework
from .base import Task, tasks


class HwCacheTask(Task):
    """Task to generate hwpack and hwstatic cache."""

    def make_cache(self):
        self.logger.info('start building hwcache ...')

        # delete all files and directories under config.HOMEWORK_PACK_DIR and
        # config.HOMEWORK_STATIC_DIR
        if os.path.isdir(config.HOMEWORK_PACK_DIR):
            for f in os.listdir(config.HOMEWORK_PACK_DIR):
                shutil.rmtree(os.path.join(config.HOMEWORK_PACK_DIR, f))

        if os.path.isdir(config.HOMEWORK_STATIC_DIR):
            for f in os.listdir(config.HOMEWORK_STATIC_DIR):
                shutil.rmtree(os.path.join(config.HOMEWORK_STATIC_DIR, f))

        # create the pack dir and static dir if not exist
        if not os.path.isdir(config.HOMEWORK_PACK_DIR):
            os.makedirs(config.HOMEWORK_PACK_DIR)
        if not os.path.isdir(config.HOMEWORK_STATIC_DIR):
            os.makedirs(config.HOMEWORK_STATIC_DIR)

        # list all homeworks under config.HOMEWORK_DIR
        # only the directories which contain "hw.xml" should be marked as
        # homework
        for hw_name in os.listdir(config.HOMEWORK_DIR):
            hw_path = os.path.join(config.HOMEWORK_DIR, hw_name)
            meta_path = os.path.join(hw_path, 'hw.xml')
            if os.path.isdir(hw_path) and os.path.isfile(meta_path):
                hw = Homework.load(hw_path)

                # create the pack & static directory for this homework
                hw_pack_path = os.path.join(config.HOMEWORK_PACK_DIR, hw_name)
                os.makedirs(hw_pack_path)

                # make packed archive for each programming language
                for lang in hw.get_code_languages():
                    # Some code package may not provide downloadable attachment
                    if not hw.get_code(lang).has_attach:
                        continue
                    archive_path = os.path.join(hw_pack_path, '%s.zip' % lang)
                    hw.pack_assignment(lang, archive_path)
                    self.logger.info('hwpack "%s": ok.' % archive_path)

                # copy static resources into target directory
                hw_desc = os.path.join(hw.path, 'desc')
                hw_static_path = os.path.join(
                    config.HOMEWORK_STATIC_DIR, hw_name)
                shutil.copytree(hw_desc, hw_static_path)
                self.logger.info('hwstatic "%s": ok.' % hw_static_path)

    def execute(self):
        try:
            self.make_cache()
        except Exception:
            self.logger.exception('Build homework cache failed.')


tasks.add('hwcache', HwCacheTask)
