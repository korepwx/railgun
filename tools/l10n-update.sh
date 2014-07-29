#!/bin/bash

pushd 
cd railgun/website

# Scan the update of messages
pybabel update -i translations/messages.pot -d translations


