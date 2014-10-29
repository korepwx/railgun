#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: docs/sphinx_patch.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import re
import inspect
from sphinx.ext.autodoc import (ModuleLevelDocumenter, AttributeDocumenter,
                                ModuleDocumenter, ClassLevelDocumenter,
                                annotation_option,
                                safe_repr,
                                isdescriptor,
                                FunctionType, BuiltinFunctionType,
                                MethodType, class_types,
                                SUPPRESS)


SKIP_ANNOTATION = '|'.join(
    '(^(%s)$)' % s for s in (
        r'railgun\.website\.codelang\.languages',
        r'railgun\.website\.context\..*',
        r'railgun\.website\.credential\.login_manager',
        r'railgun\.website\.forms\..*',
        r'railgun\.website\.hw\.homeworks',
        r'railgun\.website\.manual\.manual_pages',
        r'railgun\.website\.scriptlibs\.scripts',
        r'railgun\.website\.userauth\.auth_providers',
        r'railgun\.runner\.context\..*',
        r'railgun\.runner\.hw\.homeworks',
    )
)
SKIP_ANNOTATION_RE = re.compile(SKIP_ANNOTATION)


class PatchedDataDocumenter(ModuleLevelDocumenter):

    """
    Specialized Documenter subclass for data items.
    """
    objtype = 'data'
    member_order = 40
    priority = -9
    option_spec = dict(ModuleLevelDocumenter.option_spec)
    option_spec["annotation"] = annotation_option

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
                if not SKIP_ANNOTATION_RE.match(self.fullname):
                    self.add_line(u'   :annotation: = ' + objrepr, '<autodoc>')
        elif self.options.annotation is SUPPRESS:
            pass
        else:
            self.add_line(u'   :annotation: %s' % self.options.annotation,
                          '<autodoc>')

    def document_members(self, all_members=False):
        pass


class PatchedAttributeDocumenter(AttributeDocumenter):

    """
    Specialized Documenter subclass for attributes.
    """
    objtype = 'attribute'
    member_order = 60
    option_spec = dict(ModuleLevelDocumenter.option_spec)
    option_spec["annotation"] = annotation_option

    # must be higher than the MethodDocumenter, else it will recognize
    # some non-data descriptors as methods
    priority = 11

    method_types = (FunctionType, BuiltinFunctionType, MethodType)

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        isdatadesc = isdescriptor(member) and not \
            isinstance(member, cls.method_types) and not \
            type(member).__name__ in ("type", "method_descriptor",
                                      "instancemethod")
        return isdatadesc or (not isinstance(parent, ModuleDocumenter)
                              and not inspect.isroutine(member)
                              and not isinstance(member, class_types))

    def add_directive_header(self, sig):
        ClassLevelDocumenter.add_directive_header(self, sig)
        if not self.options.annotation:
            if not self._datadescriptor:
                try:
                    objrepr = safe_repr(self.object)
                except ValueError:
                    pass
                else:
                    if not SKIP_ANNOTATION_RE.match(self.fullname):
                        self.add_line(u'   :annotation: = ' + objrepr,
                                      '<autodoc>')
        elif self.options.annotation is SUPPRESS:
            pass
        else:
            self.add_line(u'   :annotation: %s' % self.options.annotation,
                          '<autodoc>')


def setup(app):
    app.add_autodocumenter(PatchedDataDocumenter)
    app.add_autodocumenter(PatchedAttributeDocumenter)
