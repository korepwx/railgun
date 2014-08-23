#!/usr/bin/env bash
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: tools/debian-installer.sh
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

if [ "`id -u`" != "0" ]; then
    echo "Run this script with root privilege!"
    exit 0
fi

# Upgrade the whole system before we start installing
apt-get -y update || exit -1
apt-get -y dist-upgrade || exit -1

# Install system requirements for python
apt-get -y install python-pip           \
    python-virtualenv                   \
    redis-server                        \
    json-c                              \
    boost-python                        \
    cryptopp                            \
|| exit -1
