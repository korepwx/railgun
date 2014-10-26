#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: docs/sphinx_patch.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.


from sphinx.ext.autodoc import (ModuleLevelDocumenter, ModuleDocumenter,
                                annotation_option, safe_repr,
                                SUPPRESS)


class PatchedDataDocumenter(ModuleLevelDocumenter):
    """
    Specialized Documenter subclass for data items.
    """
    objtype = 'data'
    member_order = 40
    priority = -9
    option_spec = dict(ModuleLevelDocumenter.option_spec)
    option_spec["annotation"] = annotation_option

    skip_annotation = {
        'railgun.website.codelang.languages',
    }

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        return isinstance(parent, ModuleDocumenter) and isattr

    def add_directive_header(self, sig):
        ModuleLevelDocumenter.add_directive_header(self, sig)
        if not self.options.annotation:
            try:
                objrepr = safe_repr(self.object)
            except ValueError:
                pass
            else:
                if self.fullname in PatchedDataDocumenter.skip_annotation:
                    pass
                elif not (objrepr.startswith('<') and objrepr.endswith('>')):
                    self.add_line(u'   :annotation: = ' + objrepr, '<autodoc>')
        elif self.options.annotation is SUPPRESS:
            pass
        else:
            self.add_line(u'   :annotation: %s' % self.options.annotation,
                          '<autodoc>')

    def document_members(self, all_members=False):
        pass


def setup(app):
    app.add_autodocumenter(PatchedDataDocumenter)
