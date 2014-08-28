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
            'CoverageScorer': CoveragePartialScoreRender,
        }.get(typeName, DefaultPartialScoreRender)()


class DefaultPartialScoreRender(PartialScoreRender):
    """Default HwPartialScore renderer that wraps each detail text in a
    pair of `pre` tags."""

    def render(self, partial):
        return render_template(
            'renders/PartialScore.default.html', partial=partial
        )


class CoveragePartialScoreRender(PartialScoreRender):
    """HwPartialScorer renderer that renders coverage results."""

    def line_class(self, line):
        return {
            '*': 'warning',
            '-': 'danger',
            '+': 'success',
        }.get(line[:1], None)

    def format_file(self, detail):
        ret = {}
        text = unicode(detail).split(u'\n')
        # first line is the summary of file
        ret['file'] = text[0]
        # second line is the delimeter
        ret['lines'] = [
            (self.line_class(line), line[2:])
            for line in text[2:]
        ]
        return ret

    def render(self, partial):
        # Format each file result
        if (partial.detail):
            detail = [self.format_file(d) for d in partial.detail]
        else:
            detail = None
        return render_template('renders/PartialScore.coverage.html',
                               detail=detail)


def renderPartialScore(partial):
    """Render the detail of given partial."""
    return PartialScoreRender.getRender(partial.typeName).render(partial)


# inject renderPartialScore into template context
@app.context_processor
def __inject_renderPartialScore():
    return dict(renderPartialScore=renderPartialScore)
