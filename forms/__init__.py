import os, sys
from decimal import *
import re
import time
import logging

class FieldRequiredError(Exception):
    pass

class FieldFormatError(Exception):
    def __init__(self, message = None, *args):
        self.message = message
        self.args = args

class Field(object):
    name_re = re.compile('^[a-zA-Z_][0-9a-zA-Z_]*$')

    def __init__(self, name, value = None, required = True, strip = True, validators = [], common_error = False, **kwargs):
        assert self.name_re.match(name)
        self.name = name
        self.strip = strip
        self.required = required
        self.common_error = common_error

        self.options = kwargs

        if value is not None: self.set_val(value)
        else: self.value = None

        self.validators = validators

    def set_val(self, v):
        self.value = v.strip() if v is not None and self.strip and isinstance(v, basestring) else v

    def validate(self):
        if (self.value is None or self.value == '') and self.required:
            raise FieldRequiredError()

        if (self.value is None or self.value == '') and not self.required:
            return

        for v in self.validators:
            v(self.value)

class DecimalField(Field):
    def validate(self):
        Field.validate(self)

        if self.value is None and not self.required:
            return

        try:
            Decimal(self.value)
        except:
            raise FieldFormatError('Field must be decimal')

    def set_val(self, v):
        Field.set_val(self, v)

        if self.value == '':
            self.value = None

class BoolField(Field):
    def set_val(self, v):
        Field.set_val(self, v)

        if isinstance(self.value, basestring):
            self.value = 1 if ['true', 'on', 'On'].index(self.value) > 0 else 0
        elif isinstance(self.value, int):
            self.value = 1 if self.value > 0 else 0
        else:
            self.value = 0

class DateField(Field):
    def set_val(self, v):
        Field.set_val(self, v)

        format = self.options['format'] if 'format' in self.options else '%d.%m.%Y'
        try:
            ts = time.strptime(self.value, format)
            self.value = int(time.mktime(ts))
        except ValueError:
            self.value = None
            return

class Form(object):
    def __init__(self, fields, data = {}):
        self.fields = fields
        self.errors = {}
        self.valid = False

        for field in fields:
            if field.name in data:
                field.set_val(data[field.name])

    def add(self, field):
        self.fields.append(field)
        self.errors = {}
        self.valid = False

    def values(self):
        result = {}
        for field in self.fields:
            result[field.name] = field.value

        return result

    def error(self, field_name, message = 'Unknown error'):
        for field in self.fields:
            if field.name == field_name:
                key = field.name if not field.common_error else 'common'
                self.errors[key] = {'message' : message}
                break

        self.valid = False

    def validate(self):
        self.errors = {}
        for field in self.fields:
            key = field.name if not field.common_error else 'common'
            try:
                field.validate()
            except FieldRequiredError:
                self.errors[key] = {'message' : 'Field is required'}
            except FieldFormatError, e:
                self.errors[key] = {'message' : e.message}
            except Exception, e:
                self.errors[key] = {'message' : 'Unknown error'}

        self.valid = True if len(self.errors) == 0 else False

        return self.valid

    def get_errors(self):
        return self.errors