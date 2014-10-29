#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: runlib/python/pyhost/errors.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.


class ScorerFailure(Exception):
    """Stop the execution of a :class:`~pyhost.scorer.Scorer` and set the
    :attr:`score`, the :attr:`brief` explanation and the :attr:`detail`
    explanation.

    :param brief: The brief explanation.
    :type brief: :class:`~railgun.common.lazy_i18n.GetTextString`
    :param score: The final score given by this error.
    :type score: :class:`float`
    :param detail: Detailed explanation of the score, a list of translated
        strings.
    :type detail: :class:`list` of
        :class:`~railgun.common.lazy_i18n.GetTextString`
    """

    def __init__(self, brief, score=0.0, detail=None):
        super(ScorerFailure, self).__init__(brief, score, detail)

        #: The final score given by this error.
        self.score = score
        #: The brief explanation of the score, a translated string.
        #: (:class:`~railgun.common.lazy_i18n.GetTextString`)
        self.brief = brief
        #: Detailed explanation of the score, a list of translated string.
        #: (:class:`list` of :class:`~railgun.common.lazy_i18n.GetTextString`)
        self.detail = detail
