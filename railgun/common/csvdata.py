#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/common/csvdata.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Contributors:
#   public@korepwx.com   <public@korepwx.com>
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import csv

from railgun.common.lazy_i18n import gettext_lazy


class CsvField(object):
    """Represent a field in a CSV data schema."""

    def __init__(self, **kwargs):
        # If name is given, this field will use a different name from its
        # attribute name in Schema
        self.name = kwargs.get('name', None)

        # If default is given, this field will give the default value if
        # field does not exist in CSV file. It not, raise KeyError.
        self.has_default = 'default' in kwargs
        self.default = kwargs.get('default', None)

    def _parseString(self, value):
        pass

    def parseString(self, value):
        """Parse Python object from CSV string value."""
        try:
            return self._parseString(value)
        except Exception:
            raise ValueError(gettext_lazy(
                'Cannot convert "%(value)s" to %(type)s.',
                value=value, type=self.__class__.__name__
            ))

    def toString(self, value):
        """Convert Python object into CSV string value."""
        return str(value)

    def __repr__(self):
        return '<Field(%s)>' % self.__class__.__name__


class CsvInteger(CsvField):
    def _parseString(self, value):
        return int(value)


class CsvString(CsvField):
    def _parseString(self, value):
        return value


class CsvFloat(CsvField):
    def _parseString(self, value):
        return float(value)


class CsvSchema(object):
    """Represent a data schema on CSV file."""

    @staticmethod
    def LoadCSV(cls, iterable):
        """Get iterable objects from given line `iterable` object."""
        rdr = csv.reader(iterable)

        # parse the header line
        headers = {k: i for i, k in enumerate(next(rdr))}
        field_getter = {}

        for k, v in cls.__dict__.iteritems():
            if (isinstance(v, CsvField)):
                field_name = v.name if v.name else k
                if (field_name in headers):
                    # set the getter to fetch Nth column of a row
                    # where N = headers[k]
                    field_getter[k] = (
                        lambda row, key=field_name, col=v: (
                            col.parseString(row[headers[key]])
                        )
                    )
                elif (v.has_default):
                    # not exist in CSV, if has default, use default value
                    field_getter[k] = lambda row, val=v: val.default
                else:
                    # not exist, no default, raise KeyError
                    raise KeyError(gettext_lazy(
                        'Field "%(field)s" not found in CSV data.',
                        field=field_name
                    ))

        # Yield object from CSV one by one
        for row in rdr:
            if (not row):
                continue
            obj = cls()
            for f, g in field_getter.iteritems():
                setattr(obj, f, g(row))
            yield obj
