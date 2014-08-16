#!/bin/bash

# Scan the messages in source
pybabel extract -F babel.cfg -k lazy_gettext -o railgun/website/translations/messages.pot .

# Scan the update of messages
pybabel update -i railgun/website/translations/messages.pot -d railgun/website/translations
