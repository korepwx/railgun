![Image of Python Logo](hw://img/python-logo.png)

(Download this image: [hw://img/python-logo.png](hw://img/python-logo.png))

Finish <code>reform_path</code> in path.py, so that it will produce output for input <code>path</code> that satisfies given requirements.

The homework has 6 test points. Furthermore, you must make sure that your programs follow the code styles. Please upload your submission before deadline.

```python
def reform_path(path):
    """Re-format the input `path`. Strip all "." and ".." parts. Return the
    new path that matches the following rules:

    *   All "\\" in old path should be treated as and translated to "/".
    *   Continous "/" should be compressed to one.
    *   "." in old path should be stripped directly.
    *   ".." in old path should consume one parent dir. However if no parent
        exists, a `ValueError` should be raised.
    *   If old path is empty, or all parents in old path is consumed, new path
        should be "" or "/", depending on the following rule.
    *   New path should starts with "/" if and only if the old does.
    *   Whether or not the old path ends with "/", new path shouldn't, unless
        it is "/".
    """

    raise NotImplementedError()
```
