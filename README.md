# json_np

Json for numpy, or if you prefer, json no problems! 

**Authors:** Luca de Alfaro (luca@dealfaro.com) and Massimo Di Pierro 
(mdipierro@gmail.com)

This is a version of Json that can handle also: 
* Dates
* Sets
* numpy nd.array
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

In class-based usage, you can declare a class to be a subclass of `json_np.
Serializable`.  Then, calling the `to_json` method of an object causes the 
complete object to be serialized, including recursively all object 
attributes, except for the attributes that start with underscore (`_`). 

```
from json_np import Serializable

class C(Serializable):

    def __init__(self, a):
        super().__init__()
        self.a = a # Serialized
        self._b = 32 # Not serialized

c = C("hello")
s = c.to_json()
cc = C.from_json(s)
```

Obviously, you should ensure that C contains compatible fields when it is 
deserialized, in case the code changed in the meantime. 

## History

This package was originally developed by Luca and Massimo at Camio, for 
Python2.  The work was open sourced.  The package was later ported to Python 3. 
The authors thank Camio for allowing the open-sourcing of the code. 
