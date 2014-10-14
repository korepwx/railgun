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
    """Read the file contents of `path`.

    :returns: File content as string, or None if any error occurred.
    """
    try:
        with open(path, 'rb') as f:
            return unicode(f.read(), 'utf-8')
    except Exception:
        pass


def remove_firstdir(path):
    """Remove the first directory of given `path` and return modified str.

    If '/' is not found in `path`, assume that it does not contain a directory.
    For examples::

        >>> remove_firstdir('/entity')
        'entity'
        >>> remove_firstdir('top/entity')
        'entity'
        >>> remove_firstdir('entity')
        'entity'

    :param path: The input path string.
    :type path: :class:`str`
    :return: Path of which the first directory is removed.
    """

    slash_pos = path.find('/')
    if slash_pos >= 0:
        path = path[slash_pos+1:]
    return path


def dirtree(parent):
    """Get an iterable object over all relative paths of entities under
    directory `parent`.

    :returns: iterable object over all relative paths.
    :raises: :class:`Exception` from the system libraries.
    """

    def F(pa, p):
        for f in os.listdir(pa):
            fpath = os.path.join(pa, f)
            p2 = p + f
            # if directory, scan recursively
            if os.path.isdir(fpath):
                for p3 in F(fpath, p2 + '/'):
                    yield p3
            yield p2

    return F(os.path.realpath(parent), '')


def packzip(base_path, files, target, path_prefix=''):
    """Pack all entities in `files` under `base_path` into `target` zipfile.

    :param base_path: the base path of all entities.
    :type base_path: :class:`str`
    :param files: iterable object over relative paths of file entities.
    :type files: :class:`object`
    :param target: Target zipfile object.
    :type target: :class:`zipfile.ZipFile`
    :param path_prefix: prefix of paths to be added into archive file.
    :type path_prefix: :class:`str`

    :return: `target`
    """
    for f in files:
        fp = os.path.join(base_path, f)
        target.write(fp, path_prefix + f)
    return target


def makezip(filename):
    """Create a new :class:`zipfile.ZipFile` object.

    :param filename: the file system path of created zip file.
    :type filename: :class:`str`

    :return: :class:`zipfile.ZipFile` object.
    """

    return zipfile.ZipFile(filename, 'w', zipfile.ZIP_DEFLATED)


class Extractor(object):
    """The unique interface for archive file extractors.

    `Railgun` system can extract various types of archive files.  This class
    provides a unique interface to create an extractor on given archive file.
    The format of archive will be recognized according to file extension,
    For examples::

        >>> Extractor.open('a.zip')
        <ZipExtractor instance>
        >>> Extractor.open('a.rar')
        <RarExtractor instance>

    Also, the :class:`Extractor` objects implements context manager, for
    example:

    .. code-block:: python

        with Extractor.open('a.zip') as f:
            for fname, fobj in f:
                print 'the content of %s is:' % fname
                print fobj.read()
    """

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
        """Get iterable (fname, fobj) from the archive.

        You may simply iterate over a :class:`Extractor` object, which is
        same as calling to this method.

        :return: list of tuple (fname, fobj), where `fname` is a :class:`str`,
            and `fobj` is a file-like object.
        """
        raise NotImplementedError()

    # basic method to get names of all files
    def filelist(self):
        """Get iterable name lists in this archive file."""
        raise NotImplementedError()

    def countfiles(self, maxcount=1048576):
        """Count all files in the archive.

        :param maxcount: maximum files to count.  If exceeds this limit,
            the method will be interrupted, and ``maxcount + 1`` will be
            returned.
        :type maxcount: :class:`int`

        :return: the number of files in this archive.
        """

        counter = 0
        for fname in self.filelist():
            counter += 1
            if counter > maxcount:
                break
        return counter

    def onedir(self):
        """Check whether this archive contains only one top-level directory?

        Some students may compress a whole directory.  We want to detect such
        situations.

        .. note::
            OS X may add a hidden directory named `__MACOSX` to zip archives.
            This method will ignore such directory.

        :return: True if the archive file indeed contains only one top-level
            directory, while False otherwise.
        """
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
        """Open an extractor for given archive file.

        :param fpath: the path of archive file.
        :type fpath: :class:`str`

        :return: instance derived from :class:`Extractor`.
        :raises: :class:`ValueError` if the extension of given file is not
            supported.
        """

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
