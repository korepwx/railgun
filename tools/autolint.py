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
            m = getattr(self, method)
            if callable(m) and method.startswith('patch_'):
                return m(fpath, lineno, line)
        return line


def patch_lines(fpath):
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


def patch_file(fpath):
    with open(fpath, 'rb') as f:
        cnt = f.read()
    updated = False
    # Replace '\r\n' to '\n'
    cnt2 = cnt.replace('\r\n', '\n').replace('\r', '')
    if cnt2 != cnt:
        updated = True
        cnt = cnt2
    # Require an empty line at tail
    if cnt[-1] != '\n':
        cnt = cnt + '\n'
        updated = True
    # Save if changed
    if updated:
        print('Patched %s' % fpath)
        with open(fpath, 'wb') as f:
            f.write(cnt)


line_patcher = LinePatcher()
for pkg in ('railgun', 'runlib'):
    for dpath, dnames, fnames in os.walk(pkg):
        for fname in fnames:
            # We only care about '.py' files
            if not fname.endswith('.py'):
                continue
            fpath = os.path.join(dpath, fname)
            patch_lines(fpath)
            patch_file(fpath)
