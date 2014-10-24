#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/common/csvdata.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

"""
Utilities to load objects from csv file.

Suppose you are given csv data like this:

.. code-block: csv
    name,student-number,year,registered
    Jenny,00001,21,True
    Bob,000002,22,False

You may derive an object schema from :class:`CsvSchema`, giving the names and
types of the columns::

    class MyObjectSchema(CsvSchema):

        name = CsvString()
        stdno = CsvString(name='student-number')
        year = CsvInteger()
        registered = CsvBoolean()

Then you may get the objects by::

    with open('data.csv', 'rb') as f:
        for obj in CsvSchema.LoadCSV(MyObjectSchema, f):
            print obj

.. note::
    The first row in csv file must be the column names!  However, they may
    not be at the same order as defined in schema.  :class:`CsvSchema`
    uses this row to detect the order.
"""

import csv

from railgun.common.lazy_i18n import lazy_gettext


class CsvField(object):
    """Define a column in csv file.

    This is the base class for all types of columns.  You may inherit this
    class to provide your own field type, for example::

        import json

        class CsvJsonField(object):

            def fromString(self, value):
                return json.loads(value)

            def toString(self, value):
                return json.dumps(value)

    :param name: Give the name of column. If not given, use the attribute
        name in :class:`CsvSchema`.
    :type name: :class:`str`
    :param default: Give the default value of this column. If given, this
        value will be used if such column does not exist. If not given,
        :class:`KeyError` will be raised if not exist.
    """

    def __init__(self, **kwargs):
        # If name is given, this field will use a different name from its
        # attribute name in Schema
        self.name = kwargs.get('name', None)

        # If default is given, this field will give the default value if
        # field does not exist in CSV file. It not, raise KeyError.
        self.has_default = 'default' in kwargs
        self.default = kwargs.get('default', None)

    def fromString(self, value):
        """Convert `value` from :class:`str` to field type.

        Derived classes should overwrite this.  You may raise any exceptions
        as you need.

        :return: Converted object.
        """
        pass

    def parseString(self, value):
        try:
            return self.fromString(value)
        except Exception:
            raise ValueError(lazy_gettext(
                'Cannot convert "%(value)s" to %(type)s.',
                value=value, type=self.__class__.__name__
            ))

    def toString(self, value):
        """Convert `value` from field type to :class:`str`.

        You must return such string representations that `fromString`
        can convert it back.

        :return: Converted str.
        """
        return str(value)

    def __repr__(self):
        return '<Field(%s)>' % self.__class__.__name__


class CsvInteger(CsvField):
    """Define an integral field in csv file."""

    def fromString(self, value):
        return int(value)


class CsvString(CsvField):
    """Define a string field in csv file."""

    def fromString(self, value):
        return value


class CsvFloat(CsvField):
    """Define a float field in csv file."""

    def fromString(self, value):
        return float(value)


class CsvBoolean(CsvField):
    """Define a boolean field in csv file.

    String literals will be converted according to the following table:

    .. tabularcolumns:: |p{4cm}|p{11cm}|

    ======================= ================================================
    Value                   Literals (Case Insensitive)
    ======================= ================================================
    :data:`True`            'true', 'on', '1', 'yes'
    :data:`False`           'false', 'off', '0', 'no'
    :class:`ValueError`     Any other literal
    ======================= ================================================
    """

    def fromString(self, value):
        val = value.lower()
        if val in ('true', 'on', '1', 'yes'):
            return True
        if val in ('false', 'off', '0', 'no'):
            return False
        raise ValueError('%s is not a boolean value.' % value)


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
            if isinstance(v, CsvField):
                field_name = v.name if v.name else k
                if field_name in headers:
                    # set the getter to fetch Nth column of a row
                    # where N = headers[k]
                    field_getter[k] = (
                        lambda row, key=field_name, col=v: (
                            col.parseString(row[headers[key]])
                        )
                    )
                elif v.has_default:
                    # not exist in CSV, if has default, use default value
                    field_getter[k] = lambda row, val=v: val.default
                else:
                    # not exist, no default, raise KeyError
                    raise KeyError(lazy_gettext(
                        'Field "%(field)s" not found in CSV data.',
                        field=field_name
                    ))

        # Yield object from CSV one by one
        for row in rdr:
            if not row:
                continue
            obj = cls()
            for f, g in field_getter.iteritems():
                setattr(obj, f, g(row))
            yield obj

    @staticmethod
    def SaveCSV(cls, fileobj, items):
        writer = csv.writer(fileobj)

        # Given attrname, field, get the field name
        def FieldName(attrname, field):
            return field.name if field.name else attrname

        # Collect meta data
        attrs = [(k, v) for k, v in cls.__dict__.iteritems()
                 if isinstance(v, CsvField)]

        # Write the header
        writer.writerow([FieldName(k, v) for k, v in attrs])

        # Write value rows
        for itm in items:
            writer.writerow([v.toString(getattr(itm, k))
                             for k, v in attrs])
