#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: tools/autolint.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import os


class LinePatcher(object):

    def patch_superfluous_parens(self, fpath, lineno, line):
        strip_line = line.strip()
        if (strip_line.startswith('if (') or strip_line.startswith('elif (')) \
                and strip_line.endswith('):'):
            pos = line.find('if (')
            end = line.rfind('):')
            line = line[:pos] + 'if ' + line[pos+4:end] + ':'
        return line

    def patch(self, fpath, lineno, line):
        for method in dir(self):
            if callable(method) and method.startswith('patch_'):
                getattr(self, method)(fpath, lineno, line)


line_patcher = LinePatcher()
for pkg in ('railgun', 'runlib'):
    for dpath, dnames, fnames in os.walk(pkg):
        for fname in fnames:
            # We only care about '.py' files
            if not fname.endswith('.py'):
                continue
            fpath = os.path.join(dpath, fname)
            with open(fpath, 'rb') as f:
                lines = [l.rstrip() for l in f]
            # Patch each line
            updated = 0
            for i, line in enumerate(lines):
                line2 = line_patcher.patch(fpath, i, line)
                if line2 != line:
                    updated += 1
                    lines[i] = line2
            # Save if updated
            if updated > 0:
                with open(fpath, 'wb') as f:
                    f.write('\n'.join(lines))
                print('Patched %d line(s) in %s' % (updated, fpath))
