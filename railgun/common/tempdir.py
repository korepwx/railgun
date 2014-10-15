#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/common/tempdir.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import os
import uuid
import config
import shutil

from .fileutil import remove_firstdir


class TempDir(object):
    """It's a common requirement to create a temporary directory for some
    work, and delete it after the work has done.  :class:`TempDir` provides
    such utility to manage a temporary directory.

    All the temporary directories are created under ``config.TEMPORARY_DIR``.
    You may create a temp directory like this::

        with TempDir() as d:
            fpath = d.fullpath('subfile.txt')
            with open(fpath, 'wb') as f:
                f.write('hello, world!')

    :param name: The name of this temporary directory.  If not given,
        it will generate a randomized name by ``uuid.uuid4().get_hex()``.
    :type name: :class:`str`
    """

    def __init__(self, name=None):
        #: Hold the name of this temporary directory.
        self.name = name if name else uuid.uuid4().get_hex()

        #: Hold the path of this temporary directory.
        self.path = os.path.join(config.TEMPORARY_DIR, self.name)

    def open(self, mode=0700):
        """Create the temporary directory.

        If the directory already exists, this method will do nothing.
        You may call `chown` to ensure the mode of this directory.

        :param mode: Unix file system mode for this temporary directory.
        :type mode: :class:`int`
        """
        if not os.path.isdir(self.path):
            os.makedirs(self.path, mode)

    def close(self):
        """Delete the temporary directory recursively.

        If the directory does not exist, this method will do nothing.
        """
        if os.path.isdir(self.path):
            shutil.rmtree(self.path)

    def fullpath(self, subpath):
        """Get the fullpath for child entity.

        :param subpath: Relative path for the child entity.
        :type subpath: :class:`str`
        """
        return os.path.join(self.path, subpath)

    def copyfiles(self, srcdir, filelist, mode=0700):
        """Copy all files from source directory into this.

        :param srcdir: The path of source directory.
        :type srcdir: :class:`str`
        :param filelist: Iterable relative paths of file entities.
        :type filelist: iterable object
        :param mode: Unix file system mode for all files and directories.
            This parameter will not affect existing directories.  Call
            `chown` to ensure it.
        :type mode: :class:`int`
        """

        for f in filelist:
            srcpath = os.path.join(srcdir, f)
            dstpath = os.path.join(self.path, f)

            # We do not care about the directory entities in `filelist`.
            #
            # This is because all the files in `filelist` is relative to
            # `srcdir`.  We may create the directory for each file if
            # necessary.
            if not os.path.isdir(srcpath):
                parent_path = os.path.dirname(dstpath)

                # Create the container directory for this file if necessary
                if not os.path.isdir(parent_path):
                    os.makedirs(parent_path, mode)

                # Copy the file and set the mode
                shutil.copyfile(srcpath, dstpath)
                os.chmod(dstpath, mode)

    def extract(self, extractor, should_skip=None, mode=0700):
        """Extract files into this directory.

        :param extractor: An extractor object.
        :type extractor: :class:`railgun.common.fsutil.Extractor`
        :param should_skip: A callback to determine whether a given file
            should be skipped.
        :type should_skip: method(fpath) -> bool
        :param mode: Unix file system mode for all new directories and files.
            This parameter will not affect existing directories.  Call
            `chown` to ensure it.
        :type mode: :class:`int`
        """
        # check the arguments
        should_skip = should_skip or (lambda p: False)
        canonical_path = remove_firstdir \
            if extractor.onedir() else (lambda p: p)

        for fname, fobj in extractor.extract():
            fpath = canonical_path(fname)
            dstpath = os.path.join(self.path, fpath)

            # check whether the file should skip
            if should_skip(fpath):
                continue

            # create the parent directory if not exist
            parent_path = os.path.dirname(dstpath)
            if not os.path.isdir(parent_path):
                os.makedirs(parent_path, mode)

            with open(dstpath, 'wb') as f:
                f.write(fobj.read())
            os.chmod(dstpath, mode)

    def chown(self, uid, gid=None, recursive=False):
        """Change the owner uid and gid of this directory.

        :param uid: Name or id of owner user.
        :type uid: :class:`str` or :class:`int`
        :param gid: Name or id of owner group.  If not given, gid will not be
            changed.
        :type uid: :class:`str` or :class:`int`
        :param recursive: Whether or not to chown all children?
        :type recursive: :class:`bool`
        """
        if gid is None:
            gid = os.stat(self.path).st_gid
        if recursive:
            for dpath, _, fnames in os.walk(self.path):
                os.chown(dpath, uid, gid)
                for fn in fnames:
                    os.chown(os.path.join(dpath, fn), uid, gid)
        else:
            os.chown(self.path, uid, gid)

    def chmod(self, mode, recursive=False):
        """Change the Unix file system mode of this directory.

        :param mode: File system mode number.
        :type mode: :class:`int`
        :param recursive: Whether or not to chmod all children?
        :type recursive: :class:`bool`
        """
        if recursive:
            for dpath, _, fnames in os.walk(self.path):
                os.chmod(dpath, mode)
                for fn in fnames:
                    os.chmod(os.path.join(dpath, fn), mode)
        else:
            os.chmod(self.path, mode)

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, ignore1, ignore2, ignore3):
        self.close()
