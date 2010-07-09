#!/usr/bin/env python
from postmarkup import textilize

from django.db import models
from django.db.models import CharField, TextField, IntegerField

from base64 import encodestring, decodestring
import binascii

MARKUP_TYPES = [ ("html", "Raw HTML"),
                ("postmarkup", "Postmarkup (BBCode like)"),
                ("emarkup", "Extended markup"),
                ("text", "Plain text"),
                ("comment_bbcode", "BBcode used in comments"), ]


try:
    import cPickle as pickle
except ImportError:
    import pickle

class PickledObject(str):
    """A subclass of string so it can be told whether a string is
       a pickled object or not (if the object is an instance of this class
       then it must [well, should] be a pickled one)."""
    pass

class PickledObjectField(models.Field):
    __metaclass__ = models.SubfieldBase

    def to_python(self, value):
        if isinstance(value, PickledObject):
            # If the value is a definite pickle; and an error is raised in de-pickling
            # it should be allowed to propogate.
            return pickle.loads(str(decodestring(value)))
        else:
            try:
                try:
                    return pickle.loads(str(decodestring(value)))
                except binascii.Error:
                    return pickle.loads(str(value))
            except:
                return value


    def get_db_prep_save(self, value):
        if value is not None and not isinstance(value, PickledObject):
            value = PickledObject(encodestring(pickle.dumps(value)))
        return value

    def get_internal_type(self):
        return 'TextField'

    def get_db_prep_lookup(self, lookup_type, value):
        if lookup_type == 'exact':
            value = self.get_db_prep_save(value)
            return super(PickledObjectField, self).get_db_prep_lookup(lookup_type, value)
        elif lookup_type == 'in':
            value = [self.get_db_prep_save(v) for v in value]
            return super(PickledObjectField, self).get_db_prep_lookup(lookup_type, value)
        else:
            raise TypeError('Lookup type %s is not supported.' % lookup_type)

class MarkupField(TextField):


    def __init__(self, renderer=None, *args, **kwargs):
        self._renderer_callback = renderer or self._defaultrenderer

        super(MarkupField, self).__init__(*args, **kwargs)

    @classmethod
    def _defaultrenderer(cls, markup, markup_type):

        return markup, '', textilize(markup), {}


    def contribute_to_class(self, cls, name):

        self._html_field = name + "_html"
        self._type_field = name + "_markup_type"
        self._version_field = name + "_version"
        self._summary_field = name + "_summary_html"
        self._text_field = name + "_text"
        self._data_field = name + "_data"

        CharField("Markup type", blank=False, max_length=20, choices=MARKUP_TYPES, default="postmarkup").contribute_to_class(cls, self._type_field)
        IntegerField(default=0).contribute_to_class(cls, self._version_field)
        TextField(editable=True, blank=True, default="").contribute_to_class(cls, self._html_field)
        TextField(editable=True, blank=True, default="").contribute_to_class(cls, self._summary_field)
        TextField(editable=False, blank=True, default="").contribute_to_class(cls, self._text_field)
        PickledObjectField(editable=False, default={}, blank=True).contribute_to_class(cls, self._data_field)

        super(MarkupField, self).contribute_to_class(cls, name)


    def pre_save(self, model_instance, add):

        markup = getattr(model_instance, self.attname)
        markup_type = getattr(model_instance, self._type_field)

        html, summary_html, text, data = self._renderer_callback(markup, markup_type)

        setattr(model_instance, self._html_field, html)
        setattr(model_instance, self._summary_field, summary_html)
        setattr(model_instance, self._text_field, text)
        setattr(model_instance, self._data_field, data)
        return markup