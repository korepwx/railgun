#!/bin/bash

pushd
cd railgun/website
mkdir -p translations

# Scan the messages in source
pybabel extract -F babel.cfg -k lazy_gettext -o translations/messages.pot .

# Initialize the languages
pybabel init -i translations/messages.pot -d translations -l zh_Hans_CN

