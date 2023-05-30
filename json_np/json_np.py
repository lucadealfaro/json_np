#!/usr/bin/env python
"""
Copyright 2014 Camiolog Inc.
Authors: Luca de Alfaro and Massimo Di Pierro
"""

# pylint: disable=invalid-name,too-many-return-statements

import base64
import collections
import datetime
import importlib
import io
import json
import numbers

import numpy


class Storage(dict):
    """
    Like a dict but attributes can be accessed
    with obj.name instead obj[name]
    """

    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


class Serializable:
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
        """Get a value given a corresponding key."""
        return getattr(self, key)

    def __setitem__(self, key, value):
        """Set a value for the correspoding key."""
        setattr(self, key, value)

    def __delitem__(self, key):
        """Delete a value given a corresponding key."""
        del self.__dict__[key]

    def keys(self):
        """Returns an iterator over keys."""
        return self.__dict__.keys()

    def items(self):
        """Returns an iterator over items."""
        return self.__dict__.items()

    def values(self):
        """Returns an interator over values."""
        return self.__dict__.values()

    def update(self, data):
        """Update values from provided data dict."""
        self.__dict__.update(data)

    def __len__(self):
        """Returns the number of items stored."""
        return len(self.__dict__)

    def __contains__(self, item):
        """Returns True if the item is stored, else otherwise."""
        return item in self.__dict__

    def __repr__(self):
        """Returns a string representation for the object."""
        return repr(self.__dict__)

    def get(self, key, default=None):
        """Returns the value corresponding to the key or default value."""
        return getattr(self, key, default)

    def __eq__(self, other):
        return hasattr(other, "__dict__") and self.__dict__ == other.__dict__

    def to_json(self, pack_ndarray=True, tolerant=True, indent=2, encoding="utf-8"):
        """
        Dumps itself to a string.
        :param pack_ndarray: Whether to serialize numpy arrays.  Default is yes.
        :param tolerant: Ignore attributes that cannot be serialized.
        :param indent: Indentation of resulting json.
        :param encoding: encoding used for bytes
        :return: The serialized object.
        """
        return Serializable.dumps(
            self,
            pack_ndarray=pack_ndarray,
            tolerant=tolerant,
            indent=indent,
            encoding=encoding,
        )

    @staticmethod
    def dump(
        obj, stream, pack_ndarray=True, tolerant=True, indent=2, encoding="utf-8"
    ):  # pylint: disable=too-many-arguments
        """
        Dumps an object to a string.
        :param stream: file where to dump the result.
        :param obj: The object to serialize.
        :param pack_ndarray: Whether to serialize numpy arrays.  Default is yes.
        :param tolerant: Ignore attributes that cannot be serialized.
        :param indent: Indentation of resulting json.
        :param encoding: encoding used for bytes
        :return: The serialized object.
        """
        return stream.write(
            Serializable.dumps(
                obj,
                pack_ndarray=pack_ndarray,
                tolerant=tolerant,
                indent=indent,
                encoding=encoding,
            )
        )

    @staticmethod
    def dumps(obj, pack_ndarray=True, tolerant=True, indent=2, encoding="utf-8"):
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
                d["meta_class"] = "%s.%s" % (module, o.__class__.__name__)
                d.update(
                    item for item in o.__dict__.items() if not item[0].startswith("_")
                )
                return d

            if isinstance(o, bytes):
                # Bytes are encoded.
                d = {"meta_class": "bytes", "bytes": o.decode(encoding)}
                return d

            if isinstance(o, datetime.datetime):
                d = {"meta_class": "datetime.datetime", "date": o.isoformat()}
                return d

            if isinstance(o, set):
                d = {"meta_class": "set", "set": list(o)}
                return d

            if isinstance(o, io.FileIO):
                return "<file %r>" % o.name

            if pack_ndarray and isinstance(o, numpy.ndarray):
                d = {
                    "meta_class": "numpy.ndarray",
                    "dtype": str(o.dtype),
                    "shape": o.shape,
                    "data": base64.b64encode(o.tobytes()),
                }
                return d

            # Normal Python types are unchanged
            if isinstance(o, (int, str, float, bool, list, dict, tuple)):
                return o

            if isinstance(o, numbers.Integral):
                return int(o)

            if isinstance(o, numbers.Real):
                return float(o)

            if isinstance(o, bool):
                return bool(o)

            if tolerant:
                return None

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
            meta_module, meta_class = None, o.get("meta_class")
            if meta_class in ("Datetime", "datetime.datetime"):
                # 'Datetime' included for backward compatibility
                fmt = "%Y-%m-%dT%H:%M:%S"
                if len(o["date"]) > 19:
                    fmt += ".%f"
                return datetime.datetime.strptime(o["date"], fmt)

            if meta_class == "set":
                return set(o["set"])

            if meta_class == "bytes":
                return o["bytes"].encode(encoding)

            # Numpy arrays.
            if meta_class == "numpy.ndarray":
                data = base64.b64decode(o["data"])
                dtype = o["dtype"]
                shape = o["shape"]
                v = numpy.frombuffer(data, dtype=dtype)
                v = v.reshape(shape)
                obj = v.copy()
                obj.flags.writeable = True
                return obj

            if meta_class and "." in meta_class:
                # correct for classes that have migrated from one module to another
                meta_class = mapper.get(meta_class, meta_class)
                # separate the module name from the actual class name
                meta_module, meta_class = meta_class.rsplit(".", 1)

            if meta_class is not None:
                del o["meta_class"]
                if meta_module is not None:
                    meta_class = mapper.get(meta_class, meta_class)
                    try:
                        module = importlib.import_module(meta_module)
                        cls = getattr(module, meta_class)
                        obj = cls()
                        obj.__dict__.update(o)
                        o = obj
                    except Exception:  # pylint: disable=broad-except
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
            elif type(o).__name__ == "dict":
                # For convenience we deserialize dict into Storage.
                o = Storage(o)
            return o

        return json.loads(s, object_hook=hook)

    @staticmethod
    def loads(string):
        """Loads json from input string."""
        return Serializable.from_json(string)

    @staticmethod
    def load(stream):
        """Loads json from input stream."""
        return Serializable.loads(stream.read())


loads = Serializable.loads
dumps = Serializable.dumps
