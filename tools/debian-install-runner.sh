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

# Install system requirements
apt-get -y install cmake                \
    build-essential                     \
    python-pip                          \
    python-virtualenv                   \
    redis-server                        \
    libjson0-dev                        \
    libboost-python-dev                 \
    libcrypto++-dev                     \
    libldap2-dev                        \
    libsasl2-dev                        \
    libxml2-dev                         \
    libxslt1-dev                        \
    libmysqlclient-dev                  \
    libcurl4-openssl-dev                \
    unrar-free                          \
|| exit -1

# Compile the CSafeRunner
(cd runlib/python/pyhost/CSafeRunner    &&
    rm -rf build                        &&
    mkdir -p build                      &&
    cd build                            &&
    cmake ..                            &&
    make                                &&
    cp SafeRunner ../../../../../SafeRunner
) || exit -1

# Make virtual environment, and install python requirements
(rm -rf env                             &&
    virtualenv env                      &&
    . env/bin/activate                  &&
    pip install -r requirements.txt
) || exit -1

# The temporary and logs directory
mkdir -p tmp
mkdir -p logs
