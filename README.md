# json_np

Json for numpy, or if you prefer, json no problems! 

**Authors:** Luca de Alfaro (luca@dealfaro.com) and Massimo Di Pierro 
(mdipierro@gmail.com)

This is a version of Json that can handle also: 
* Dates
* Sets
* numpy array
* bytes

There are two ways to use it. 

## Basic Usage

```
import json_np
import numpy as np

a = np.array([3, 4, 5])
s = json_np.dumps(a)
aa = json_np.loads(s)

```

Here, we have applied `json_np.dumps` to a numpy array, but we could equally 
well have used a datetime, a dictionary, a list, etc (nesting of such types is 
allowed).

## Class-Based Usage

You can also dump any object.
All object attributes, except those whose name begins with underscore (`_`), 
will be serialized. 
Optionally, if `serializable_only` is True, only objects that are 
instances of `Serializable`, or that are dates, numpy arrays,  will be 
serialized. 

The deserialization happens in the same class, if:
* the class can be loaded
* the class initializer has no required arguments.

If any of these two conditions is not met, the deserialization happens
using the `Serializable` class. 

```
from json_np import Serializable

class C(object):

    def __init__(self, a=8):
        super().__init__()
        self.a = a # Serialized
        self._b = 32 # Not serialized

c = C("hello")
s = json_np.dumps(c)
cc = json_np.loads(s)
```

Obviously, you should ensure that C contains compatible fields when it is 
deserialized, in case the code changed in the meantime. 

## History

This package was originally developed by Luca and Massimo at Camio, for 
Python2.  The work was open sourced.  The package was later ported to Python 3. 
The authors thank Camio for allowing the open-sourcing of the code. 
