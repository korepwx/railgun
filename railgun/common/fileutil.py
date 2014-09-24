#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/common/fileutil.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import os
import zipfile
import rarfile
import tarfile

# set the global parameters of external modules
rarfile.PATH_SEP = '/'


def file_get_contents(path):
    """Get the content of `path`, or None if exception raised."""
    try:
        with open(path, 'rb') as f:
            return unicode(f.read(), 'utf-8')
    except Exception:
        pass


def remove_firstdir(path):
    """Remove the first level directory from `path`"""
    slash_pos = path.find('/')
    if slash_pos >= 0:
        path = path[slash_pos+1:]
    return path


def dirtree(path):
    """Get all file entries under directory `path`."""

    def F(parent, p):
        for f in os.listdir(parent):
            fpath = os.path.join(parent, f)
            p2 = p + f
            # if directory, scan recursively
            if os.path.isdir(fpath):
                for p3 in F(fpath, p2 + '/'):
                    yield p3
            yield p2

    return F(os.path.realpath(path), '')


def packzip(base_path, files, target, path_prefix=''):
    """Pack all items in `files` under `base_path` into `target` zipfile."""
    for f in files:
        fp = os.path.join(base_path, f)
        target.write(fp, path_prefix + f)
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
        if self.fobj:
            self.fobj.close()
            self.fobj = None

    # support iteration over the extractor
    def __iter__(self):
        return self.extract()

    # canonical path: replace '\\' to '/'
    def _canonical_path(self, p):
        return p.replace('\\', '/')

    # basic method to get next file from archive
    def extract(self):
        """Get iterable (fname, fobj) from the archive."""
        raise NotImplementedError()

    # basic method to get names of all files
    def filelist(self):
        """Get iterable fname from the archive."""
        raise NotImplementedError()

    def countfiles(self, maxcount=1048576):
        """Count all files in the archive.

        Args:
            maxcount (int): Maximum files to count.  If exceeds this limit,
                return ``maxcount + 1``.  Default is 1048576.

        Returns:
            The count of entities in this archive.
        """

        counter = 0
        for fname in self.filelist():
            counter += 1
            if counter > maxcount:
                break
        return counter

    def onedir(self):
        """Check whether this archive contains only one directory"""
        last_dname = None
        for fname in self.filelist():
            # get the first directory name
            slash_pos = fname.find('/')
            if slash_pos >= 0:
                dname = fname[: slash_pos]
            else:
                dname = fname
            # ignore some meta data directories
            if dname == '__MACOSX':
                # OS X will add a hidden directory named "__MACOSX" to archive
                # even the user just wants to compress a single directory.
                # So ignore this directory.
                continue
            # check whether one dir.
            if last_dname is None:
                last_dname = dname
            if last_dname != dname:
                return False
        return True

    @staticmethod
    def open(fpath):
        """Open an extractor for given `fpath`."""

        fext = os.path.splitext(fpath)[1].lower()
        if fext in ('.rar'):
            return RarExtractor(fpath)
        if fext in ('.zip'):
            return ZipExtractor(fpath)
        if fext in ('.tar', '.tgz', '.gz', '.bz2', '.tbz'):
            return TarExtractor(fpath)
        raise ValueError('Archive file "%s" not recognized.')


class ZipExtractor(Extractor):

    def __init__(self, fpath):
        super(ZipExtractor, self).__init__(zipfile.ZipFile(fpath, 'r'))

    def extract(self):
        for mi in self.fobj.infolist():
            # ignore directory entries
            if mi.filename[-1] == '/':
                continue
            f = self.fobj.open(mi)
            yield self._canonical_path(mi.filename), f

    def filelist(self):
        for mi in self.fobj.infolist():
            if mi.filename[-1] == '/':
                continue
            yield self._canonical_path(mi.filename)


class RarExtractor(Extractor):

    def __init__(self, fpath):
        super(RarExtractor, self).__init__(rarfile.RarFile(fpath, 'r'))

    def extract(self):
        for mi in self.fobj.infolist():
            if mi.isdir():
                continue
            f = self.fobj.open(mi)
            yield self._canonical_path(mi.filename), f

    def filelist(self):
        for mi in self.fobj.infolist():
            if mi.isdir():
                continue
            yield self._canonical_path(mi.filename)


class TarExtractor(Extractor):

    def __init__(self, fpath):
        super(TarExtractor, self).__init__(tarfile.open(fpath, 'r'))

    def extract(self):
        for mi in self.fobj:
            if not mi.isdir():
                yield self._canonical_path(mi.name), self.fobj.extractfile(mi)

    def filelist(self):
        for mi in self.fobj:
            if not mi.isdir():
                yield self._canonical_path(mi.name)
