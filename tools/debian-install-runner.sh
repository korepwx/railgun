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
apt-get -y install cmake                \
    build-essential                     \
    python-pip                          \
    python-virtualenv                   \
    redis-server                        \
    libjson0-dev                        \
    libboost-python-dev                 \
    libcrypto++-dev                     \
    libcurl4-openssl-dev                \
    unrar-free                          \
|| exit -1

# Compile the CSafeRunner
(cd runlib/python/pyhost/CSafeRunner    &&
    mkdir -p build                      &&
    cd build                            &&
    cmake ..                            &&
    make                                &&
    cp SafeRunner.so ../../SafeRunner.so
) || exit -1

# Print current directory
echo "`pwd`"
