#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/common/osutil.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import os
import time
import math
import signal
import subprocess


class ProcessTimeout(Exception):
    """Indicate that the timeout was reached when executing a process."""
    pass


def is_running(pid):
    """Check whether the process with given `pid` is still running.

    :param pid: The process id.
    :type pid: :class:`int`

    :return: :data:`True` if the process is still alive, :data:`False`
        otherwise.
    """
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def execute(cmd, timeout=None, **kwargs):
    """Execute a command, read the output and return it back.

    :param cmd: Command to execute.
    :type cmd: :class:`str`
    :param timeout: Process timeout in seconds.
    :type timeout: :class:`int`
    :param kwargs: Named arguments for `subprocess.Popen`.
    :return: (stdout, stderr, exit code)
    :rtype: :class:`tuple`

    :raises: :class:`OSError` on missing command or any other OS errors.
    :raises: :class:`ProcessTimeout` if a timeout was reached.
    """

    ph_out = None   # process output
    ph_err = None   # stderr
    ph_ret = None   # return code

    p = subprocess.Popen(cmd, shell=True,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         **kwargs)
    # if timeout is not set wait for process to complete
    if not timeout:
        ph_ret = p.wait()
    else:
        fin_time = math.ceil(time.time() + timeout)
        while p.poll() is None and fin_time > time.time():
            time.sleep(1)

        # if timeout reached, raise an exception
        if fin_time < time.time():

            # starting 2.6 subprocess has a kill() method which is preferable
            # p.kill()
            if is_running(p.pid):
                os.kill(p.pid, signal.SIGKILL)
                raise ProcessTimeout("Process timeout has been reached.")

        ph_ret = p.returncode

    ph_out, ph_err = p.communicate()
    return (ph_ret, ph_out, ph_err)
