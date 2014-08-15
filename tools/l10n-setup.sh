#!/bin/bash

mkdir -p railgun/website/translations

# Scan the messages in source
pybabel extract -F babel.cfg -k lazy_gettext -o railgun/website/translations/messages.pot .

# Initialize the languages
pybabel init -i railgun/website/translations/messages.pot -d railgun/website/translations -l zh_Hans_CN
