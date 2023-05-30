#!/usr/bin/env python

# Copyright 2014 Camiolog Inc.
# Authors: Luca de Alfaro and Massimo Di Pierro

import base64
import collections
import datetime
import importlib
import io
import json
import numbers
import traceback

import numpy


class Storage(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


class Serializable(object):
    """
    If a class subclasses Serializable, then json_plus
    will serialize its objects.
    In a composite object Obj, json_plus will traverse and serialize:
    - primitive types that are json-serializable
    - all lists, dictionaries, sets, numpy arrays, dates.
    - all attributes that are of a Serializable class.
    """

    # We mimick a dict.
    def __getitem__(self, key):
        return getattr(self, key)
    def __setitem__(self, key, value):
        setattr(self, key, value)
    def __delitem__(self, key):
        del self.__dict__[key]
    def keys(self):
        return self.__dict__.keys()
    def items(self):
        return self.__dict__.items()
    def values(self):
        return self.__dict__.values()
    def update(self, d):
        self.__dict__.update(d)
    def __len__(self):
        return len(self.__dict__)
    def __contains__(self, item):
        return item in self.__dict__
    def __repr__(self):
        return repr(self.__dict__)

    def get(self, k, d=None):
        return getattr(self, k, d)

    def __eq__(self, other):
        return hasattr(other, '__dict__') and self.__dict__ == other.__dict__

    def to_json(self, pack_ndarray=True, tolerant=True, indent=2, encoding='utf-8'):
        """
        Dumps itself to a string.
        :param pack_ndarray: Whether to serialize numpy arrays.  Default is yes.
        :param tolerant: Ignore attributes that cannot be serialized.
        :param indent: Indentation of resulting json.
        :param encoding: encoding used for bytes
        :return: The serialized object.
        """
        return Serializable.dumps(self, pack_ndarray=pack_ndarray, tolerant=tolerant, indent=indent, encoding=encoding)

    @staticmethod
    def dump(obj, fp, pack_ndarray=True, tolerant=True, indent=2, encoding='utf-8'):
        """
        Dumps an object to a string.
        :param fp: file where to dump the result.
        :param obj: The object to serialize.
        :param pack_ndarray: Whether to serialize numpy arrays.  Default is yes.
        :param tolerant: Ignore attributes that cannot be serialized.
        :param indent: Indentation of resulting json.
        :param encoding: encoding used for bytes
        :return: The serialized object.
        """
        return fp.write(Serializable.dumps(obj, pack_ndarray=pack_ndarray, tolerant=tolerant, indent=indent, encoding=encoding))

    @staticmethod
    def dumps(obj, pack_ndarray=True, tolerant=True, indent=2, encoding='utf-8'):
        """
        Dumps an object to a string.
        :param obj: The object to serialize.
        :param pack_ndarray: Whether to serialize numpy arrays.  Default is yes.
        :param tolerant: Ignore attributes that cannot be serialized.
        :param indent: Indentation of resulting json.
        :param encoding: encoding used for bytes
        :return: The serialized object.
        """
        def custom(o):
            if isinstance(o, Serializable):
                module = o.__class__.__module__.split(".")[-1]
                # make sure keys are sorted
                d = collections.OrderedDict()
                d['meta_class'] = '%s.%s' % (module, o.__class__.__name__)
                d.update(item for item in o.__dict__.items()
                                 if not item[0].startswith('_'))
                return d
            elif isinstance(o, bytes):
                # Bytes are encoded.
                d = {'meta_class': 'bytes',
                    'bytes': o.decode(encoding)}
                return d
            elif isinstance(o, datetime.datetime):
                d = {'meta_class': 'datetime.datetime',
                     'date': o.isoformat()}
                return d
            elif isinstance(o, set):
                d = {'meta_class': 'set',
                     'set': list(o)}
                return d
            elif isinstance(o, io.FileIO):
                return '<file %r>' % o.name

            elif pack_ndarray and isinstance(o, numpy.ndarray):
                d = {'meta_class': 'numpy.ndarray',
                     'dtype': str(o.dtype),
                     'shape': o.shape,
                     'data': base64.b64encode(o.tobytes())}
                return d

            # Normal Python types are unchanged
            elif isinstance(o, (int, str, float, bool, list, dict, tuple)):
                return o
            elif isinstance(o, numbers.Integral):
                return int(o)
            elif isinstance(o, numbers.Real):
                return float(o)
            elif isinstance(o, bool):
                return bool(o)
            elif tolerant:
                return None
            else:
                raise ValueError("Cannot encode in json object %r" % o)
        return json.dumps(obj, default=custom, indent=indent)

    @staticmethod
    def from_json(s, mapper=None, encoding="utf-8"):
        """Decodes json_plus.
         :param s : the string to decode
         :param mapper : A dictionary. key classes are replaced by the value classes in the
                decoding. Classes not found are replaced by Serializable.
        :param encoding: encoding used for bytes
        :return: the decoded object.
        """
        mapper = mapper or {}
        def hook(o):
            meta_module, meta_class = None, o.get('meta_class')
            if meta_class in ('Datetime', 'datetime.datetime'):
                # 'Datetime' included for backward compatibility
                try:
                    tmp = datetime.datetime.strptime(
                        o['date'], '%Y-%m-%dT%H:%M:%S.%f')
                except Exception:
                    tmp = datetime.datetime.strptime(
                        o['date'], '%Y-%m-%dT%H:%M:%S')
                return tmp
            elif meta_class == 'set':
                return set(o['set'])
            elif meta_class == 'bytes':
                return o['bytes'].encode(encoding)
            # Numpy arrays.
            elif meta_class == 'numpy.ndarray':
                data = base64.b64decode(o['data'])
                dtype = o['dtype']
                shape = o['shape']
                v = numpy.frombuffer(data, dtype=dtype)
                v = v.reshape(shape)
                obj = v.copy()
                obj.flags.writeable = True
                return obj

            elif meta_class and '.' in meta_class:
                # correct for classes that have migrated from one module to another
                meta_class = mapper.get(meta_class, meta_class)
                # separate the module name from the actual class name
                meta_module, meta_class = meta_class.rsplit('.', 1)

            if meta_class is not None:
                del o['meta_class']
                if meta_module is not None:
                    meta_class = mapper.get(meta_class, meta_class)
                    try:
                        module = importlib.import_module(meta_module)
                        cls = getattr(module, meta_class)
                        obj = cls()
                        obj.__dict__.update(o)
                        o = obj
                    except Exception:
                        # If an object is unknown, restores it as a member
                        # of this same class.
                        obj = Serializable()
                        obj.__dict__.update(o)
                        o = obj
                else:
                    # Map all to Serializable.
                    obj = Serializable()
                    obj.__dict__.update(o)
                    o = obj
            elif type(o).__name__ == 'dict':
                # For convenience we deserialize dict into Storage.
                o = Storage(o)
            return o

        return json.loads(s, object_hook=hook)

    @staticmethod
    def loads(s):
        return Serializable.from_json(s)

    @staticmethod
    def load(fp):
        return Serializable.loads(fp.read())


loads = Serializable.loads
dumps = Serializable.dumps
