#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/common/fileutil.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Contributors:
#   public@korepwx.com   <public@korepwx.com>
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import os
import zipfile
import rarfile
import tarfile

# set the global parameters of external modules
rarfile.PATH_SEP = '/'


def dirtree(path):
    """Get all file entries under directory `path`."""

    def F(parent, p):
        for f in os.listdir(parent):
            fpath = os.path.join(parent, f)
            p2 = p + f
            # if directory, scan recursively
            if (os.path.isdir(fpath)):
                for p3 in F(fpath, p2 + '/'):
                    yield p3
            yield p2

    return F(os.path.realpath(path), '')


def packzip(base_path, files, target):
    """Pack all items in `files` under `base_path` into `target` zipfile."""
    for f in files:
        fp = os.path.join(base_path, f)
        target.write(fp, f)
    return target


def makezip(filename):
    """Make a new compressed zip file `filename`."""
    return zipfile.ZipFile(filename, 'w', zipfile.ZIP_DEFLATED)


class Extractor(object):
    """Basic interface for archive file extractor."""

    def __init__(self, fobj):
        self.fobj = fobj

    # support with statement
    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        if (self.fobj):
            self.fobj.close()
            self.fobj = None

    # support iteration over the extractor
    def __iter__(self):
        return self.extract()

    # the basic method to get next file from archive
    def extract(self):
        """Get iterable (fname, fobj) from the archive."""
        raise NotImplementedError()

    @staticmethod
    def open(fpath):
        """Open an extractor for given `fpath`."""

        fext = os.path.splitext(fpath)[1].lower()
        if (fext in ('.rar')):
            return RarExtractor(fpath)
        if (fext in ('.zip')):
            return ZipExtractor(fpath)
        if (fext in ('.tar', '.tgz', '.gz', '.bz2', '.tbz')):
            return TarExtractor(fpath)
        raise ValueError('Archive file "%s" not recognized.')


class ZipExtractor(Extractor):

    def __init__(self, fpath):
        super(ZipExtractor, self).__init__(zipfile.ZipFile(fpath, 'r'))

    def extract(self):
        for mi in self.fobj.infolist():
            # ignore directory entries
            if (mi.compress_type == 0):
                continue
            f = self.fobj.open(mi)
            yield mi.filename, f


class RarExtractor(Extractor):

    def __init__(self, fpath):
        super(RarExtractor, self).__init__(rarfile.RarFile(fpath, 'r'))

    def extract(self):
        for mi in self.fobj.infolist():
            if (mi.isdir()):
                continue
            f = self.fobj.open(mi)
            yield mi.filename, f


class TarExtractor(Extractor):

    def __init__(self, fpath):
        super(TarExtractor, self).__init__(tarfile.open(fpath, 'r'))

    def extract(self):
        for mi in self.fobj:
            if (not mi.isdir()):
                yield mi.name, self.fobj.extractfile(mi)
