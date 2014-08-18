#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/website/renders.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

from flask import render_template

from .context import app


class PartialScoreRender(object):
    """Class to render HwPartialScore of a given handin."""

    def render(self, partial):
        """Return rendered HTML code for `partial`."""
        pass

    @staticmethod
    def getRender(typeName):
        return {
            'default': DefaultPartialScoreRender,
        }.get(typeName, DefaultPartialScoreRender)()


class DefaultPartialScoreRender(PartialScoreRender):
    """Default HwPartialScore renderer that wraps each detail text in a
    pair of `pre` tags."""

    def render(self, partial):
        return render_template(
            'renders/PartialScore.default.html', partial=partial
        )


def renderPartialScore(partial):
    """Render the detail of given partial."""
    return PartialScoreRender.getRender(partial.typeName).render(partial)


# inject renderPartialScore into template context
@app.context_processor
def __inject_renderPartialScore():
    return dict(renderPartialScore=renderPartialScore)
