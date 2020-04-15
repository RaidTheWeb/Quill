# Quill

## How to contribute:

Quill is a statically typed language written in python for speed.

You can Contribute in a couple ways by editing the main code and submitting a pull request, creating a new library for
the standard library, fixing errors and mistakes or by testing Quill yourself and submitting issues when problems
are found.

## How to write a library for Quill

A library can be written in Python or Quill.

### Python

In a python file write this:

```python
import sys
sys.path.append('../src')

import data
import errors
```

This will add src to your PythonPATH value.

On every function, add a return value ( if needed ) as a Quill data type


```python
def myFunction(*args):
  return data.String("I am a function")
```

The other data types are:

data.String()
data.Number()
data.List()
data.Bool()

and more.



At the bottom of the file add some attrs:

```python
attrs = {
    'myFunction': data.Method(myFunction),
}
```

Add as many as you need to the attrs dictionary.



## Quill

The same as you would if you were just define functions and classes, but in a different file.

< Quill Module Guide Here >



