#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/website/renders.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

from flask import render_template

from railgun.common.lazy_i18n import GetTextString
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
            'ObjSchemaScorer': ObjSchemaPartialScoreRender,
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

    def extract_total(self, first):
        if (not first):
            return None
        txt = unicode(first)
        lines = txt.split('\n')
        headers = [s.strip() for s in lines[2].split(u',')]
        files = [[s.strip() for s in v.split(u',')] for v in lines[4:-2]]
        total = [s.strip() for s in lines[-1].split(u',')]
        return headers, files, total

    def render(self, partial):
        # Format each file result
        if (partial.detail):
            # Whether there exists the total coverage report?
            # this special check is for compatibility with older versions.
            first = partial.detail[0]
            first_title = str(first.text) if isinstance(first, GetTextString) \
                else str(first)
            if (first_title.startswith('Coverage Results:')):
                raw_detail = partial.detail[1:]
            else:
                raw_detail = partial.detail
                first = None
            # Make the detail reports
            first_extract = self.extract_total(first)
            if (first_extract):
                total_report = {
                    'headers': first_extract[0],
                    'files': first_extract[1],
                    'total': first_extract[2],
                }
            else:
                total_report = None
            detail = [self.format_file(d) for d in raw_detail]
        else:
            detail = None
            total_report = None
        return render_template('renders/PartialScore.coverage.html',
                               detail=detail, total=total_report)


class ObjSchemaPartialScoreRender(PartialScoreRender):
    """HwPartialScorer renderer that renders objschema results."""

    def render(self, partial):
        return render_template(
            'renders/PartialScore.objschema.html', partial=partial
        )


def renderPartialScore(partial):
    """Render the detail of given partial."""
    return PartialScoreRender.getRender(partial.typeName).render(partial)


# inject renderPartialScore into template context
@app.context_processor
def __inject_renderPartialScore():
    return dict(renderPartialScore=renderPartialScore)
